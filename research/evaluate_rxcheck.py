from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.audit import AuditEvent, InteractionAcknowledgment, InteractionOverride
from app.models.check import InteractionCheckFinding
from app.models.drug import Drug
from app.models.enums import InteractionSource, InteractionType, NormalizationStatus, OverrideAction, SeverityLevel
from app.models.interaction import Condition, Interaction, InteractionSourceAssertion
from app.models.patient import Patient, PatientCondition, PatientMedication, User
from app.services.orchestrator import InteractionCheckResult, run_interaction_check

RESULTS_JSON = Path(__file__).with_name("evaluation_results.json")
RESULTS_MD = Path(__file__).with_name("evaluation_results.md")


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    expected: str
    observed: str
    evidence: dict[str, Any]


def unique_label() -> str:
    return f"eval-{uuid.uuid4().hex[:10]}"


def severity_value(value) -> str:
    return getattr(value, "value", str(value))


def summary_types(result: InteractionCheckResult) -> list[str]:
    return [item.summary.interaction_type.value for item in result.summaries]


def find_item(result: InteractionCheckResult, interaction_id: str):
    for item in result.summaries:
        if item.interaction_id == interaction_id:
            return item
    return None


def record(
    results: list[ScenarioResult],
    name: str,
    passed: bool,
    expected: str,
    observed: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    results.append(
        ScenarioResult(
            name=name,
            passed=passed,
            expected=expected,
            observed=observed,
            evidence=evidence or {},
        )
    )


def upsert_drug(db: Session, rxcui: str, preferred_name: str, is_placeholder: bool = False) -> Drug:
    drug = db.get(Drug, rxcui)
    if drug is None:
        drug = Drug(
            rxcui=rxcui,
            preferred_name=preferred_name,
            tty="IN" if not is_placeholder else "PLACEHOLDER",
            is_active=True,
            is_placeholder=is_placeholder,
            rxnorm_synced_at=datetime.utcnow() if not is_placeholder else None,
        )
        db.add(drug)
    else:
        drug.preferred_name = preferred_name
        drug.is_placeholder = is_placeholder
        drug.is_active = True
    db.flush()
    return drug


def create_assertion(
    db: Session,
    interaction: Interaction,
    severity: SeverityLevel,
    source_record_id: str,
    mechanism: str,
    management: str,
) -> InteractionSourceAssertion:
    assertion = InteractionSourceAssertion(
        interaction_id=interaction.id,
        source=InteractionSource.DDInter,
        source_severity_raw=severity.value.title(),
        severity=severity,
        mechanism=mechanism,
        management=management,
        source_record_id=source_record_id,
        raw_payload={
            "evaluation_fixture": True,
            "mechanism": mechanism,
            "management": management,
        },
    )
    db.add(assertion)
    db.flush()
    return assertion


def create_fixtures(db: Session) -> dict[str, Any]:
    label = unique_label()
    user = User(
        email=f"{label}@rxcheck-evaluation.local",
        full_name="Research Evaluation User",
        role="pharmacist",
        is_active=True,
    )
    patient = Patient(is_synthetic=True, created_by=None)
    db.add_all([user, patient])
    db.flush()

    drug_a_rxcui = f"{label}-a"
    drug_b_rxcui = f"{label}-b"
    placeholder_rxcui = f"{label}-placeholder"

    drug_a = upsert_drug(db, drug_a_rxcui, "Evaluation Warfarin", is_placeholder=False)
    drug_b = upsert_drug(db, drug_b_rxcui, "Evaluation Amiodarone", is_placeholder=False)
    placeholder = upsert_drug(db, placeholder_rxcui, "Evaluation Unknown Herb", is_placeholder=True)

    for drug in (drug_b, drug_a, placeholder):
        db.add(
            PatientMedication(
                patient_id=patient.id,
                rxcui=drug.rxcui,
                raw_input=drug.preferred_name,
                normalization_status=NormalizationStatus.unmatched
                if drug.is_placeholder
                else NormalizationStatus.matched_exact,
                is_active=True,
                added_by=user.id,
            )
        )

    ddi_a, ddi_b = sorted([drug_a.rxcui, drug_b.rxcui])
    ddi = Interaction(
        interaction_type=InteractionType.DDI,
        drug_a_rxcui=ddi_a,
        drug_b_rxcui=ddi_b,
    )
    db.add(ddi)
    db.flush()
    create_assertion(
        db,
        ddi,
        SeverityLevel.major,
        f"{label}-ddi",
        "Evaluation DDI mechanism.",
        "Evaluation DDI management.",
    )

    condition = Condition(name=f"{label} renal impairment", icd10_code="N18")
    db.add(condition)
    db.flush()

    ddsi = Interaction(
        interaction_type=InteractionType.DDSI,
        drug_a_rxcui=drug_a.rxcui,
        condition_id=condition.id,
    )
    db.add(ddsi)
    db.flush()
    create_assertion(
        db,
        ddsi,
        SeverityLevel.moderate,
        f"{label}-ddsi",
        "Evaluation DDSI mechanism.",
        "Evaluation DDSI management.",
    )

    db.commit()
    return {
        "label": label,
        "user_id": user.id,
        "patient_id": patient.id,
        "drug_a_rxcui": drug_a.rxcui,
        "drug_b_rxcui": drug_b.rxcui,
        "placeholder_rxcui": placeholder.rxcui,
        "ddi_interaction_id": ddi.id,
        "ddsi_interaction_id": ddsi.id,
        "condition_id": condition.id,
    }


async def run_evaluation(db: Session) -> dict[str, Any]:
    fixtures = create_fixtures(db)
    results: list[ScenarioResult] = []

    first_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    first_types = summary_types(first_result)
    ddi_item = find_item(first_result, fixtures["ddi_interaction_id"])
    ddsi_item = find_item(first_result, fixtures["ddsi_interaction_id"])

    record(
        results,
        "deterministic_ddi_check",
        ddi_item is not None,
        "Known DDI fixture appears in check result.",
        f"Interaction types returned: {first_types}",
        {
            "run_id": first_result.run_id,
            "ddi_interaction_id": fixtures["ddi_interaction_id"],
        },
    )
    record(
        results,
        "canonical_pair_and_placeholder_exclusion",
        first_result.total_medications == 2 and first_result.total_pairs_checked == 1,
        "Two non-placeholder medications and one DDI pair are checked despite three active medication rows.",
        f"total_medications={first_result.total_medications}, total_pairs_checked={first_result.total_pairs_checked}",
        {
            "placeholder_rxcui": fixtures["placeholder_rxcui"],
        },
    )
    record(
        results,
        "ddsi_absent_without_condition",
        ddsi_item is None,
        "DDSI fixture is absent before matching patient condition is recorded.",
        f"DDSI present before condition: {ddsi_item is not None}",
        {
            "ddsi_interaction_id": fixtures["ddsi_interaction_id"],
            "condition_id": fixtures["condition_id"],
        },
    )

    db.add(
        PatientCondition(
            patient_id=fixtures["patient_id"],
            condition_id=fixtures["condition_id"],
            notes="Research evaluation condition fixture.",
        )
    )
    db.commit()

    condition_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    ddsi_after_condition = find_item(condition_result, fixtures["ddsi_interaction_id"])
    record(
        results,
        "ddsi_present_with_active_condition",
        ddsi_after_condition is not None,
        "DDSI fixture appears after matching active patient condition is recorded.",
        f"DDSI present after condition: {ddsi_after_condition is not None}",
        {
            "run_id": condition_result.run_id,
            "condition_id": fixtures["condition_id"],
        },
    )

    db.add(
        InteractionAcknowledgment(
            patient_id=fixtures["patient_id"],
            interaction_id=fixtures["ddi_interaction_id"],
            acknowledged_by=fixtures["user_id"],
            severity_at_ack=SeverityLevel.major,
            note="Research evaluation acknowledgment fixture.",
            is_active=True,
        )
    )
    db.commit()

    ack_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    ddi_after_ack = find_item(ack_result, fixtures["ddi_interaction_id"])
    record(
        results,
        "acknowledgment_suppression",
        ddi_after_ack is not None and ddi_after_ack.suppressed is True,
        "Acknowledged DDI remains in result but is marked suppressed.",
        f"DDI suppressed={getattr(ddi_after_ack, 'suppressed', None)}",
        {
            "run_id": ack_result.run_id,
            "suppressed_count": ack_result.suppressed_count,
        },
    )

    first_finding = db.scalar(
        select(InteractionCheckFinding)
        .where(InteractionCheckFinding.run_id == ack_result.run_id)
        .where(InteractionCheckFinding.interaction_id == fixtures["ddi_interaction_id"])
    )
    if first_finding is None:
        override_persisted = False
        override_evidence: dict[str, Any] = {"reason": "No DDI finding available for override test."}
    else:
        override = InteractionOverride(
            finding_id=first_finding.id,
            user_id=fixtures["user_id"],
            action=OverrideAction.overridden,
            severity_overridden=first_finding.max_severity_at_run,
            note="Research evaluation override fixture.",
        )
        db.add(override)
        db.flush()
        db.add(
            AuditEvent(
                user_id=fixtures["user_id"],
                event_type="interaction_override",
                target_type="finding",
                target_id=str(first_finding.id),
                payload={"action": OverrideAction.overridden.value, "note": override.note},
            )
        )
        db.commit()
        override_persisted = override.id is not None
        override_evidence = {
            "finding_id": first_finding.id,
            "override_id": override.id,
        }

    record(
        results,
        "override_persistence",
        override_persisted,
        "Override row is persisted for a finding.",
        f"override_persisted={override_persisted}",
        override_evidence,
    )

    findings_without_llm = db.scalars(
        select(InteractionCheckFinding).where(InteractionCheckFinding.run_id == ack_result.run_id)
    ).all()
    llm_boundary_passed = bool(findings_without_llm) and all(
        finding.llm_explanation_id is None for finding in findings_without_llm
    )
    record(
        results,
        "llm_separate_from_interaction_existence",
        llm_boundary_passed,
        "Findings exist before any LLM explanation is requested.",
        f"finding_count={len(findings_without_llm)}, all_llm_explanation_id_none={llm_boundary_passed}",
        {
            "run_id": ack_result.run_id,
            "finding_ids": [finding.id for finding in findings_without_llm],
        },
    )

    return {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "evaluation_scope": "architecture behavior, not clinical effectiveness",
            "external_paid_apis_called": False,
            "external_free_apis_called": False,
            "database": "configured SQLAlchemy DATABASE_URL",
            "fixtures": fixtures,
        },
        "summary": {
            "total_scenarios": len(results),
            "passed": sum(1 for result in results if result.passed),
            "failed": sum(1 for result in results if not result.passed),
        },
        "scenarios": [asdict(result) for result in results],
        "limitations": [
            "Uses synthetic fixtures rather than clinical cases.",
            "Does not evaluate clinical correctness or source coverage completeness.",
            "Does not call RxNorm, OpenFDA, or Anthropic.",
            "Writes synthetic evaluation rows to the configured database.",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# RxCheck Evaluation Results",
        "",
        f"Generated at: `{payload['metadata']['generated_at']}`",
        "",
        "Scope: architecture behavior, not clinical effectiveness.",
        "",
        "## Summary",
        "",
        f"- Total scenarios: {payload['summary']['total_scenarios']}",
        f"- Passed: {payload['summary']['passed']}",
        f"- Failed: {payload['summary']['failed']}",
        f"- Paid APIs called: {payload['metadata']['external_paid_apis_called']}",
        f"- Free external APIs called: {payload['metadata']['external_free_apis_called']}",
        "",
        "## Scenarios",
        "",
        "| Scenario | Result | Expected | Observed |",
        "|---|---|---|---|",
    ]
    for scenario in payload["scenarios"]:
        status = "PASS" if scenario["passed"] else "FAIL"
        lines.append(
            f"| `{scenario['name']}` | {status} | {scenario['expected']} | {scenario['observed']} |"
        )

    lines.extend(
        [
            "",
            "## Fixture IDs",
            "",
            "```json",
            json.dumps(payload["metadata"]["fixtures"], indent=2, sort_keys=True),
            "```",
            "",
            "## Limitations",
            "",
        ]
    )
    for limitation in payload["limitations"]:
        lines.append(f"- {limitation}")

    RESULTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run RxCheck architecture evaluation fixtures.")
    parser.add_argument(
        "--allow-live-db",
        action="store_true",
        help="Acknowledge that this script writes synthetic rows to the configured database.",
    )
    args = parser.parse_args()

    if not args.allow_live_db:
        print(
            "Refusing to run without --allow-live-db because this script writes synthetic evaluation rows "
            "to the configured database.",
            file=sys.stderr,
        )
        return 2

    db = SessionLocal()
    try:
        payload = await run_evaluation(db)
    except Exception as exc:
        payload = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "evaluation_scope": "architecture behavior, not clinical effectiveness",
                "external_paid_apis_called": False,
                "external_free_apis_called": False,
            },
            "summary": {
                "total_scenarios": 1,
                "passed": 0,
                "failed": 1,
            },
            "scenarios": [
                asdict(
                    ScenarioResult(
                        name="evaluation_script_runtime",
                        passed=False,
                        expected="Script completes against configured database.",
                        observed=f"{type(exc).__name__}: {exc}",
                        evidence={},
                    )
                )
            ],
            "limitations": [
                "Runtime failure prevented scenario execution.",
                "Check database connectivity and configured DATABASE_URL.",
            ],
        }
        RESULTS_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        write_markdown(payload)
        print(f"Evaluation failed. Results written to {RESULTS_JSON} and {RESULTS_MD}.", file=sys.stderr)
        return 1
    finally:
        db.close()

    RESULTS_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(payload)
    print(f"Evaluation complete. Results written to {RESULTS_JSON} and {RESULTS_MD}.")
    return 0 if payload["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
