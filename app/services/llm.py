from __future__ import annotations

import json
import re
import time
from typing import Optional

from anthropic import AsyncAnthropic
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.check import InteractionCheckFinding, LlmExplanation
from app.models.drug import Drug
from app.models.interaction import Interaction
from app.schemas import LlmExplanationResult
from app.services.openfda import fetch_citations_for_interaction

PROMPT_SYSTEM = """You are a clinical pharmacist assistant. Your job is to explain drug interactions clearly to pharmacists.

STRICT RULES:
- Only use information provided in the CONTEXT below. Do not add information from your training.
- Do not invent interactions, severities, or recommendations not present in the context.
- If the context lacks detail on a point, say "insufficient data" rather than guessing.
- Always cite which source the information comes from (DDInter, FDA label, etc).
- Keep explanations concise — pharmacists are busy.
- Never recommend a specific dose or make a prescribing decision.
- End every explanation with: "Always verify with institutional references before clinical decisions."
"""

PROMPT_TEMPLATE_VERSION = "v1"
STORED_MODEL_NAME = "claude-sonnet-4-6"
API_MODEL_NAME = settings.ANTHROPIC_MODEL or "claude-sonnet-4-20250514"


def _truncate(text: Optional[str], limit: int = 500) -> str:
    if not text:
        return "insufficient data"
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip()


def _content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def _parse_explanation_payload(raw_text: str) -> tuple[Optional[dict], list[str]]:
    errors: list[str] = []
    candidate_text = raw_text.strip()
    if candidate_text.startswith("```"):
        lines = candidate_text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate_text = "\n".join(lines).strip()
    try:
        payload, _ = json.JSONDecoder().raw_decode(candidate_text)
    except json.JSONDecodeError as exc:
        return None, [f"JSON parse error: {exc}"]

    required_keys = {
        "summary",
        "mechanism",
        "clinical_effect",
        "management",
        "severity_rationale",
        "sources_used",
        "confidence",
    }
    missing = sorted(required_keys - payload.keys())
    if missing:
        errors.append(f"Missing keys: {', '.join(missing)}")

    if "sources_used" in payload and not isinstance(payload["sources_used"], list):
        errors.append("sources_used must be a list")

    return payload, errors


def _validate_drug_mentions(raw_text: str, interaction: Interaction, db: Session) -> list[str]:
    allowed_names = {
        interaction.drug_a.preferred_name.lower() if interaction.drug_a else "",
        interaction.drug_b.preferred_name.lower() if interaction.drug_b else "",
    }
    allowed_names.discard("")
    lowered_text = raw_text.lower()

    errors: list[str] = []
    all_drug_names = db.scalars(select(Drug.preferred_name).where(Drug.is_placeholder.is_(False))).all()
    for drug_name in all_drug_names:
        normalized_name = drug_name.lower()
        if normalized_name in allowed_names:
            continue
        pattern = r"\b" + re.escape(normalized_name) + r"\b"
        if re.search(pattern, lowered_text):
            errors.append(f"Unexpected drug referenced in explanation: {drug_name}")
    return errors


def _build_result_from_payload(explanation: LlmExplanation, payload: Optional[dict]) -> LlmExplanationResult:
    return LlmExplanationResult(
        explanation_id=explanation.id,
        summary=payload.get("summary") if payload else None,
        mechanism=payload.get("mechanism") if payload else None,
        clinical_effect=payload.get("clinical_effect") if payload else None,
        management=payload.get("management") if payload else None,
        severity_rationale=payload.get("severity_rationale") if payload else None,
        sources_used=payload.get("sources_used", []) if payload else [],
        confidence=payload.get("confidence") if payload else None,
        schema_validation_passed=explanation.schema_validation_passed,
        validation_errors=explanation.validation_errors,
    )


def explanation_row_to_result(explanation: LlmExplanation) -> LlmExplanationResult:
    payload, parse_errors = _parse_explanation_payload(explanation.explanation_text)
    if parse_errors:
        payload = None
    return _build_result_from_payload(explanation, payload)


async def generate_explanation(
    interaction_id: str,
    finding_id: int,
    db: Session,
) -> LlmExplanationResult:
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured. Add it to .env before requesting explanations.")

    interaction = db.scalar(
        select(Interaction)
        .options(
            selectinload(Interaction.assertions),
            selectinload(Interaction.drug_a),
            selectinload(Interaction.drug_b),
            selectinload(Interaction.food),
            selectinload(Interaction.condition),
        )
        .where(Interaction.id == interaction_id)
    )
    if interaction is None:
        raise LookupError("Interaction not found")

    finding = db.get(InteractionCheckFinding, finding_id)
    if finding is None:
        raise LookupError("Finding not found")

    assertions = list(interaction.assertions)
    sources = sorted({assertion.source.value for assertion in assertions})
    first_assertion = assertions[0] if assertions else None
    max_severity = max(
        [assertion.severity for assertion in assertions] or [finding.max_severity_at_run],
        key=lambda sev: ["unknown", "minor", "moderate", "major", "contraindicated"].index(sev.value),
    )

    citations = await fetch_citations_for_interaction(interaction_id, db)
    drug_b_name = (
        interaction.drug_b.preferred_name
        if interaction.drug_b is not None
        else interaction.food.name
        if interaction.food is not None
        else interaction.condition.name
        if interaction.condition is not None
        else "insufficient data"
    )
    rag_context = {
        "interaction": f"{interaction.drug_a.preferred_name} + {drug_b_name}",
        "type": interaction.interaction_type.value,
        "severity": f"{max_severity.value} (sources: {', '.join(sources) if sources else 'insufficient data'})",
        "mechanism": first_assertion.mechanism if first_assertion and first_assertion.mechanism else "insufficient data",
        "management": first_assertion.management if first_assertion and first_assertion.management else "insufficient data",
        "fda_label_excerpt_drug_a": _truncate((citations.get("drug_a_label") or {}).get("drug_interactions_text")),
        "fda_label_excerpt_drug_b": _truncate((citations.get("drug_b_label") or {}).get("drug_interactions_text")),
        "citations": citations,
    }

    rag_text = "\n".join(
        [
            f"INTERACTION: {rag_context['interaction']}",
            f"TYPE: {rag_context['type']}",
            f"SEVERITY: {rag_context['severity']}",
            f"MECHANISM: {rag_context['mechanism']}",
            f"MANAGEMENT: {rag_context['management']}",
            f"FDA LABEL EXCERPT (Drug A): {rag_context['fda_label_excerpt_drug_a']}",
            f"FDA LABEL EXCERPT (Drug B): {rag_context['fda_label_excerpt_drug_b']}",
        ]
    )

    user_message = (
        "CONTEXT:\n"
        f"{rag_text}\n\n"
        "Please explain this interaction for a pharmacist in this exact JSON format:\n"
        "{\n"
        '  "summary": "One sentence overview of the interaction",\n'
        '  "mechanism": "Plain English mechanism explanation (2-3 sentences max)",\n'
        '  "clinical_effect": "What actually happens to the patient",\n'
        '  "management": "What the pharmacist should do",\n'
        '  "severity_rationale": "Why this severity rating is appropriate",\n'
        '  "sources_used": ["list of sources referenced"],\n'
        '  "confidence": "high/medium/low based on evidence quality in context"\n'
        "}\n"
        "Return only valid JSON. No preamble, no markdown, no explanation outside the JSON."
    )

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    started = time.perf_counter()
    response = await client.messages.create(
        model=API_MODEL_NAME,
        max_tokens=800,
        system=PROMPT_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    raw_text = _content_to_text(response.content)

    payload, validation_errors = _parse_explanation_payload(raw_text)
    validation_errors.extend(_validate_drug_mentions(raw_text, interaction, db))
    schema_validation_passed = len(validation_errors) == 0 and payload is not None

    token_usage = {
        "input_tokens": getattr(response.usage, "input_tokens", None),
        "output_tokens": getattr(response.usage, "output_tokens", None),
    }
    explanation = LlmExplanation(
        interaction_id=interaction_id,
        model_name=STORED_MODEL_NAME,
        model_version=API_MODEL_NAME,
        prompt_template_version=PROMPT_TEMPLATE_VERSION,
        structured_input=rag_context,
        explanation_text=raw_text,
        schema_validation_passed=schema_validation_passed,
        validation_errors=validation_errors or None,
        latency_ms=latency_ms,
        token_usage=token_usage,
    )
    db.add(explanation)
    db.flush()

    finding.llm_explanation_id = explanation.id
    db.commit()
    db.refresh(explanation)

    return _build_result_from_payload(explanation, payload if schema_validation_passed else None)
