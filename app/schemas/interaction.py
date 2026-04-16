from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import InteractionType, OverrideAction, SeverityLevel
from app.models.interaction import Interaction, InteractionSourceAssertion


class InteractionSummary(BaseModel):
    severity: SeverityLevel
    severity_label: str
    severity_color: str
    drug_a_name: str
    drug_b_name: str
    interaction_type: InteractionType
    mechanism_brief: str
    effect_brief: str
    action_brief: str
    sources_conflict: bool
    max_severity: SeverityLevel
    hub_score_a: Optional[int]
    hub_score_b: Optional[int]
    has_llm_explanation: bool


class LlmExplanationResult(BaseModel):
    explanation_id: str
    summary: Optional[str]
    mechanism: Optional[str]
    clinical_effect: Optional[str]
    management: Optional[str]
    severity_rationale: Optional[str]
    sources_used: list[str]
    confidence: Optional[str]
    schema_validation_passed: bool
    validation_errors: Optional[list[str]]


class OverrideRequest(BaseModel):
    action: OverrideAction
    note: Optional[str] = None
    user_id: Optional[str] = None


class OverrideResponse(BaseModel):
    id: int
    finding_id: int
    user_id: str
    action: OverrideAction
    severity_overridden: SeverityLevel
    note: Optional[str]
    occurred_at: datetime


class AcknowledgeRequest(BaseModel):
    note: Optional[str] = None
    expires_days: Optional[int] = None
    user_id: Optional[str] = None


class AcknowledgmentResponse(BaseModel):
    id: int
    patient_id: str
    interaction_id: str
    acknowledged_by: str
    acknowledged_at: datetime
    severity_at_ack: SeverityLevel
    expires_at: Optional[datetime]
    note: Optional[str]
    is_active: bool


SEVERITY_ORDER = {
    SeverityLevel.unknown: 0,
    SeverityLevel.minor: 1,
    SeverityLevel.moderate: 2,
    SeverityLevel.major: 3,
    SeverityLevel.contraindicated: 4,
}

SEVERITY_COLORS = {
    SeverityLevel.contraindicated: "red",
    SeverityLevel.major: "orange",
    SeverityLevel.moderate: "yellow",
    SeverityLevel.minor: "gray",
    SeverityLevel.unknown: "gray",
}


def _truncate(text: Optional[str], limit: int = 80) -> str:
    if not text:
        return ""
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _first_assertion(assertions: list[InteractionSourceAssertion]) -> Optional[InteractionSourceAssertion]:
    return assertions[0] if assertions else None


def _derive_effect_brief(assertion: Optional[InteractionSourceAssertion]) -> str:
    if assertion is None:
        return ""

    raw_payload = assertion.raw_payload if isinstance(assertion.raw_payload, dict) else {}
    for key in ("effect", "clinical_effect", "outcome", "mechanism"):
        value = raw_payload.get(key)
        if isinstance(value, str) and value.strip():
            return _truncate(value)

    if assertion.mechanism:
        return _truncate(assertion.mechanism)
    if assertion.management:
        return _truncate(assertion.management)
    return ""


def build_summary(
    interaction: Interaction,
    assertions: list[InteractionSourceAssertion],
    hub_scores: dict[str, int],
) -> InteractionSummary:
    effective_assertions = assertions or list(getattr(interaction, "assertions", []) or [])
    first_assertion = _first_assertion(effective_assertions)

    severities = [assertion.severity for assertion in effective_assertions] or [SeverityLevel.unknown]
    max_severity = max(severities, key=lambda severity: SEVERITY_ORDER[severity])
    sources_conflict = len({severity.value for severity in severities}) > 1

    drug_a_name = getattr(getattr(interaction, "drug_a", None), "preferred_name", interaction.drug_a_rxcui)
    if interaction.drug_b is not None:
        drug_b_name = interaction.drug_b.preferred_name
    elif interaction.food is not None:
        drug_b_name = interaction.food.name
    elif interaction.condition is not None:
        drug_b_name = interaction.condition.name
    else:
        drug_b_name = interaction.drug_b_rxcui or ""

    return InteractionSummary(
        severity=max_severity,
        severity_label=max_severity.value.upper(),
        severity_color=SEVERITY_COLORS[max_severity],
        drug_a_name=drug_a_name,
        drug_b_name=drug_b_name,
        interaction_type=interaction.interaction_type,
        mechanism_brief=_truncate(first_assertion.mechanism if first_assertion else ""),
        effect_brief=_derive_effect_brief(first_assertion),
        action_brief=_truncate(first_assertion.management if first_assertion else ""),
        sources_conflict=sources_conflict,
        max_severity=max_severity,
        hub_score_a=hub_scores.get(interaction.drug_a_rxcui),
        hub_score_b=hub_scores.get(interaction.drug_b_rxcui) if interaction.drug_b_rxcui else None,
        has_llm_explanation=bool(getattr(interaction, "llm_explanations", [])),
    )
