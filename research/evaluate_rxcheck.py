from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.interactions import get_finding_or_404
from app.db.session import SessionLocal
from app.models.audit import AuditEvent, InteractionAcknowledgment, InteractionOverride
from app.models.check import InteractionCheckFinding, InteractionCheckRun
from app.models.drug import Drug
from app.models.enums import InteractionSource, InteractionType, NormalizationStatus, OverrideAction, SeverityLevel
from app.models.interaction import Condition, Food, Interaction, InteractionSourceAssertion
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
    code_evidence: str
    manuscript_safe_interpretation: str
    evidence: dict[str, Any]


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def unique_label() -> str:
    return f"eval-{uuid.uuid4().hex[:10]}"


def find_item(result: InteractionCheckResult, interaction_id: str):
    return next((item for item in result.summaries if item.interaction_id == interaction_id), None)


def interaction_occurrences(result: InteractionCheckResult, interaction_id: str) -> int:
    return sum(1 for item in result.summaries if item.interaction_id == interaction_id)


def record(
    results: list[ScenarioResult],
    name: str,
    passed: bool,
    expected: str,
    observed: str,
    code_evidence: str,
    manuscript_safe_interpretation: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    results.append(
        ScenarioResult(
            name=name,
            passed=passed,
            expected=expected,
            observed=observed,
            code_evidence=code_evidence,
            manuscript_safe_interpretation=manuscript_safe_interpretation,
            evidence=evidence or {},
        )
    )


def add_drug(db: Session, rxcui: str, preferred_name: str, is_placeholder: bool = False) -> Drug:
    drug = Drug(
        rxcui=rxcui,
        preferred_name=preferred_name,
        tty="PLACEHOLDER" if is_placeholder else "IN",
        is_active=True,
        is_placeholder=is_placeholder,
        rxnorm_synced_at=None if is_placeholder else utc_now_naive(),
    )
    db.add(drug)
    db.flush()
    return drug


def add_medication(
    db: Session,
    patient_id: str,
    user_id: str,
    drug: Drug,
    *,
    is_active: bool,
) -> PatientMedication:
    medication = PatientMedication(
        patient_id=patient_id,
        rxcui=drug.rxcui,
        raw_input=drug.preferred_name,
        normalization_status=(
            NormalizationStatus.unmatched if drug.is_placeholder else NormalizationStatus.matched_exact
        ),
        is_active=is_active,
        added_by=user_id,
        notes="Research architecture evaluation fixture.",
    )
    db.add(medication)
    db.flush()
    return medication


def add_assertion(
    db: Session,
    interaction: Interaction,
    source: InteractionSource,
    severity: SeverityLevel,
    source_record_id: str,
) -> InteractionSourceAssertion:
    assertion = InteractionSourceAssertion(
        interaction_id=interaction.id,
        source=source,
        source_severity_raw=severity.value.title(),
        severity=severity,
        mechanism=f"{source.value} evaluation mechanism at {severity.value} severity.",
        management=f"{source.value} evaluation management text.",
        evidence_url=f"https://example.invalid/{source_record_id}",
        source_record_id=source_record_id,
        raw_payload={
            "evaluation_fixture": True,
            "source_record_id": source_record_id,
            "severity": severity.value,
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
    patient = Patient(is_synthetic=True)
    db.add_all([user, patient])
    db.flush()

    drug_a = add_drug(db, f"{label}-100", "Evaluation Drug A")
    drug_b = add_drug(db, f"{label}-200", "Evaluation Drug B")
    drug_c = add_drug(db, f"{label}-300", "Evaluation Drug With No Stored Interaction")
    placeholder = add_drug(db, f"{label}-placeholder", "Evaluation Unresolved Drug", is_placeholder=True)

    medication_b = add_medication(db, patient.id, user.id, drug_b, is_active=True)
    medication_a = add_medication(db, patient.id, user.id, drug_a, is_active=True)
    medication_c = add_medication(db, patient.id, user.id, drug_c, is_active=False)
    placeholder_medication = add_medication(db, patient.id, user.id, placeholder, is_active=True)

    ddi_a, ddi_b = sorted([drug_a.rxcui, drug_b.rxcui])
    ddi = Interaction(
        interaction_type=InteractionType.DDI,
        drug_a_rxcui=ddi_a,
        drug_b_rxcui=ddi_b,
    )
    db.add(ddi)
    db.flush()
    ddi_assertion_major = add_assertion(
        db,
        ddi,
        InteractionSource.DDInter,
        SeverityLevel.major,
        f"{label}-ddi-ddinter",
    )
    ddi_assertion_minor = add_assertion(
        db,
        ddi,
        InteractionSource.manual,
        SeverityLevel.minor,
        f"{label}-ddi-manual",
    )

    food = Food(name=f"{label} grapefruit")
    db.add(food)
    db.flush()
    dfi = Interaction(
        interaction_type=InteractionType.DFI,
        drug_a_rxcui=drug_a.rxcui,
        food_id=food.id,
    )
    db.add(dfi)
    db.flush()
    dfi_assertion = add_assertion(
        db,
        dfi,
        InteractionSource.DDInter,
        SeverityLevel.minor,
        f"{label}-dfi",
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
    ddsi_assertion = add_assertion(
        db,
        ddsi,
        InteractionSource.DDInter,
        SeverityLevel.moderate,
        f"{label}-ddsi",
    )

    db.commit()
    return {
        "label": label,
        "user_id": user.id,
        "patient_id": patient.id,
        "drug_a_rxcui": drug_a.rxcui,
        "drug_b_rxcui": drug_b.rxcui,
        "drug_c_rxcui": drug_c.rxcui,
        "drug_c_name": drug_c.preferred_name,
        "placeholder_rxcui": placeholder.rxcui,
        "medication_a_id": medication_a.id,
        "medication_b_id": medication_b.id,
        "medication_c_id": medication_c.id,
        "placeholder_medication_id": placeholder_medication.id,
        "ddi_interaction_id": ddi.id,
        "dfi_interaction_id": dfi.id,
        "ddsi_interaction_id": ddsi.id,
        "condition_id": condition.id,
        "food_id": food.id,
        "assertion_ids": [
            ddi_assertion_major.id,
            ddi_assertion_minor.id,
            dfi_assertion.id,
            ddsi_assertion.id,
        ],
    }


async def run_evaluation(db: Session) -> dict[str, Any]:
    fixtures = create_fixtures(db)
    results: list[ScenarioResult] = []

    baseline = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    ddi_baseline = find_item(baseline, fixtures["ddi_interaction_id"])
    dfi_baseline = find_item(baseline, fixtures["dfi_interaction_id"])
    ddsi_baseline = find_item(baseline, fixtures["ddsi_interaction_id"])

    record(
        results,
        "deterministic_ddi_from_stored_row",
        ddi_baseline is not None,
        "A stored DDI row produces a finding.",
        f"DDI present={ddi_baseline is not None}; run_id={baseline.run_id}",
        "app/services/orchestrator.py::run_interaction_check",
        "The prototype deterministically returns a DDI fixture stored in its database.",
        {"interaction_id": fixtures["ddi_interaction_id"], "run_id": baseline.run_id},
    )
    record(
        results,
        "canonical_drug_pair_ordering",
        ddi_baseline is not None and interaction_occurrences(baseline, fixtures["ddi_interaction_id"]) == 1,
        "Medications entered in reverse order still match one canonical DDI row.",
        (
            f"stored_pair={sorted([fixtures['drug_a_rxcui'], fixtures['drug_b_rxcui']])}; "
            f"occurrences={interaction_occurrences(baseline, fixtures['ddi_interaction_id'])}"
        ),
        "app/services/orchestrator.py canonical_pairs; app/models/interaction.py interactions_ddi_ordered",
        "Canonical RxCUI ordering prevents A/B and B/A from producing separate DDI findings.",
    )
    record(
        results,
        "inactive_medication_exclusion",
        baseline.total_medications == 2
        and fixtures["drug_c_name"]
        not in {
            name
            for item in baseline.summaries
            for name in (item.summary.drug_a_name, item.summary.drug_b_name)
        },
        "The inactive medication is not counted or checked.",
        f"active_non_placeholder_count={baseline.total_medications}; inactive_medication_id={fixtures['medication_c_id']}",
        "app/services/orchestrator.py active medication query",
        "The orchestrator excludes medication rows where is_active is false.",
    )
    record(
        results,
        "placeholder_drug_exclusion",
        baseline.total_medications == 2 and baseline.total_pairs_checked == 1,
        "The active placeholder medication is excluded from check counts and DDI pairs.",
        f"total_medications={baseline.total_medications}; total_pairs_checked={baseline.total_pairs_checked}",
        "app/services/orchestrator.py filter Drug.is_placeholder.is_(False)",
        "Unresolved placeholders do not participate in deterministic interaction checking.",
    )
    visible_placeholder = db.scalar(
        select(PatientMedication)
        .join(Drug, PatientMedication.rxcui == Drug.rxcui)
        .where(
            PatientMedication.id == fixtures["placeholder_medication_id"],
            Drug.is_placeholder.is_(True),
        )
    )
    record(
        results,
        "placeholder_visible_but_excluded",
        visible_placeholder is not None and baseline.total_medications == 2,
        "The placeholder remains stored in the patient medication list while excluded from checks.",
        f"placeholder_medication_stored={visible_placeholder is not None}; checked_medications={baseline.total_medications}",
        "app/models/patient.py::PatientMedication; app/services/orchestrator.py placeholder filter",
        "The architecture preserves unresolved input for review without treating it as a verified interaction-check concept.",
    )
    record(
        results,
        "ddsi_absent_without_active_condition",
        ddsi_baseline is None,
        "DDSI is absent before the matching patient condition is recorded.",
        f"DDSI present={ddsi_baseline is not None}",
        "app/services/orchestrator.py DDSI PatientCondition subquery",
        "The DDSI query avoids surfacing the fixture when the matching condition is absent.",
    )
    record(
        results,
        "dfi_independent_of_condition_profile",
        dfi_baseline is not None,
        "DFI appears for an active drug even when the patient has no condition rows.",
        f"DFI present={dfi_baseline is not None}",
        "app/services/orchestrator.py DFI query",
        "The prototype treats DFI lookup as drug-based rather than condition-gated.",
    )
    ordered_severities = [item.summary.severity.value for item in baseline.summaries]
    record(
        results,
        "severity_ranking",
        ordered_severities == sorted(
            ordered_severities,
            key=["unknown", "minor", "moderate", "major", "contraindicated"].index,
            reverse=True,
        ),
        "Findings are ordered from higher to lower severity.",
        f"ordered_severities={ordered_severities}",
        "app/services/orchestrator.py ranked_items.sort",
        "The returned fixture findings are ordered by the implemented severity priority.",
    )
    record(
        results,
        "source_severity_conflict_flag",
        ddi_baseline is not None and ddi_baseline.summary.sources_conflict is True,
        "Different assertion severities set sources_conflict=true.",
        f"sources_conflict={getattr(getattr(ddi_baseline, 'summary', None), 'sources_conflict', None)}",
        "app/schemas/interaction.py::build_summary",
        "The summary flags disagreement between stored source severities; it does not adjudicate which source is clinically correct.",
    )

    stored_assertions = list(
        db.scalars(
            select(InteractionSourceAssertion)
            .where(InteractionSourceAssertion.interaction_id == fixtures["ddi_interaction_id"])
            .order_by(InteractionSourceAssertion.id)
        ).all()
    )
    assertion_preserved = (
        len(stored_assertions) == 2
        and {assertion.source for assertion in stored_assertions}
        == {InteractionSource.DDInter, InteractionSource.manual}
        and all(assertion.raw_payload.get("evaluation_fixture") is True for assertion in stored_assertions)
    )
    record(
        results,
        "source_assertion_preservation",
        assertion_preserved,
        "Both source assertions retain source, raw severity, source ID, and raw payload.",
        (
            f"assertion_count={len(stored_assertions)}; "
            f"sources={[assertion.source.value for assertion in stored_assertions]}"
        ),
        "app/models/interaction.py::InteractionSourceAssertion",
        "The schema preserves multiple source assertions and their provenance for the fixture interaction.",
        {"assertion_ids": [assertion.id for assertion in stored_assertions]},
    )

    stored_run = db.get(InteractionCheckRun, baseline.run_id)
    record(
        results,
        "check_run_persistence",
        stored_run is not None and len(stored_run.medications_snapshot) == 2,
        "The completed check run is stored with the checked medication snapshot.",
        (
            f"run_persisted={stored_run is not None}; "
            f"snapshot_size={len(stored_run.medications_snapshot) if stored_run else None}"
        ),
        "app/models/check.py::InteractionCheckRun; app/services/orchestrator.py medication_snapshot",
        "The prototype persists a run-level record of the non-placeholder active medications evaluated.",
    )

    baseline_findings = list(
        db.scalars(
            select(InteractionCheckFinding).where(InteractionCheckFinding.run_id == baseline.run_id)
        ).all()
    )
    ddi_finding = next(
        (finding for finding in baseline_findings if finding.interaction_id == fixtures["ddi_interaction_id"]),
        None,
    )
    finding_snapshot_ok = (
        ddi_finding is not None
        and ddi_finding.max_severity_at_run == SeverityLevel.major
        and set(ddi_finding.sources_at_run) == {"DDInter", "manual"}
        and ddi_finding.sources_conflicted is True
    )
    record(
        results,
        "finding_snapshot_persistence",
        finding_snapshot_ok,
        "The finding stores run-time severity, source list, and conflict state.",
        (
            f"severity={getattr(getattr(ddi_finding, 'max_severity_at_run', None), 'value', None)}; "
            f"sources={getattr(ddi_finding, 'sources_at_run', None)}; "
            f"conflicted={getattr(ddi_finding, 'sources_conflicted', None)}"
        ),
        "app/models/check.py::InteractionCheckFinding; app/services/orchestrator.py finding creation",
        "The fixture finding retains selected run-time fields for later review.",
    )
    llm_ids_before_request = [finding.llm_explanation_id for finding in baseline_findings]
    record(
        results,
        "findings_exist_before_llm_request",
        bool(baseline_findings) and all(value is None for value in llm_ids_before_request),
        "Findings exist with no LLM explanation requested.",
        f"finding_count={len(baseline_findings)}; llm_explanation_ids={llm_ids_before_request}",
        "app/services/orchestrator.py; app/models/check.py::InteractionCheckFinding",
        "Interaction findings are created independently of the optional explanation layer.",
    )

    duplicate = PatientMedication(
        patient_id=fixtures["patient_id"],
        rxcui=fixtures["drug_a_rxcui"],
        raw_input="Duplicate Evaluation Drug A",
        normalization_status=NormalizationStatus.matched_exact,
        is_active=True,
        added_by=fixtures["user_id"],
    )
    db.add(duplicate)
    db.commit()
    duplicate_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    duplicate_occurrences = interaction_occurrences(duplicate_result, fixtures["ddi_interaction_id"])
    record(
        results,
        "duplicate_medication_does_not_duplicate_finding",
        duplicate_occurrences == 1,
        "A duplicate active medication row does not duplicate the canonical DDI finding.",
        (
            f"DDI_occurrences={duplicate_occurrences}; total_medications={duplicate_result.total_medications}; "
            f"total_pairs_checked={duplicate_result.total_pairs_checked}"
        ),
        "app/services/orchestrator.py canonical pair set and database interaction query",
        (
            "Duplicate medication rows did not duplicate the fixture finding. The current pair-count metric may still "
            "include a same-RxCUI self-pair, so this is not evidence of complete duplicate-medication normalization."
        ),
    )
    duplicate.is_active = False
    db.commit()

    inactive_medication = db.get(PatientMedication, fixtures["medication_c_id"])
    inactive_medication.is_active = True
    db.commit()
    missing_interaction_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    drug_c_name = db.get(Drug, fixtures["drug_c_rxcui"]).preferred_name
    mentions_drug_c = any(
        drug_c_name in {item.summary.drug_a_name, item.summary.drug_b_name}
        for item in missing_interaction_result.summaries
    )
    record(
        results,
        "missing_database_interaction_creates_no_finding",
        not mentions_drug_c,
        "An active normalized drug with no stored interaction does not create a finding.",
        (
            f"drug_c_mentioned={mentions_drug_c}; total_medications={missing_interaction_result.total_medications}; "
            f"total_interactions={missing_interaction_result.total_interactions_found}"
        ),
        "app/services/orchestrator.py database-only interaction queries",
        "The checker does not infer missing interactions from an LLM or external label service.",
    )
    inactive_medication.is_active = False
    db.commit()

    patient_condition = PatientCondition(
        patient_id=fixtures["patient_id"],
        condition_id=fixtures["condition_id"],
        notes="Research evaluation active condition.",
    )
    db.add(patient_condition)
    db.commit()
    condition_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    record(
        results,
        "ddsi_present_with_matching_active_condition",
        find_item(condition_result, fixtures["ddsi_interaction_id"]) is not None,
        "DDSI appears after adding the matching active condition.",
        f"DDSI present={find_item(condition_result, fixtures['ddsi_interaction_id']) is not None}",
        "app/services/orchestrator.py DDSI PatientCondition subquery",
        "The DDSI fixture is returned when its matching condition is active for the patient.",
    )
    condition_severities = [item.summary.severity.value for item in condition_result.summaries]
    record(
        results,
        "severity_ranking_with_three_interaction_types",
        condition_severities == ["major", "moderate", "minor"],
        "DDI major, DDSI moderate, and DFI minor are returned in severity order.",
        f"ordered_severities={condition_severities}",
        "app/services/orchestrator.py ranked_items.sort",
        "The three fixture interaction types follow the implemented severity ordering.",
    )
    patient_condition.resolved_date = date.today()
    db.commit()
    resolved_condition_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    record(
        results,
        "ddsi_absent_after_condition_resolution",
        find_item(resolved_condition_result, fixtures["ddsi_interaction_id"]) is None,
        "DDSI is absent after the patient condition receives a resolved date.",
        f"DDSI present={find_item(resolved_condition_result, fixtures['ddsi_interaction_id']) is not None}",
        "app/services/orchestrator.py filter PatientCondition.resolved_date.is_(None)",
        "Resolved conditions are excluded from the DDSI fixture query.",
    )

    dfi_finding = next(
        (finding for finding in baseline_findings if finding.interaction_id == fixtures["dfi_interaction_id"]),
        None,
    )
    override = None
    if dfi_finding is not None:
        override = InteractionOverride(
            finding_id=dfi_finding.id,
            user_id=fixtures["user_id"],
            action=OverrideAction.overridden,
            severity_overridden=dfi_finding.max_severity_at_run,
            note="Research evaluation override.",
        )
        db.add(override)
        db.flush()
        db.add(
            AuditEvent(
                user_id=fixtures["user_id"],
                event_type="interaction_override",
                target_type="finding",
                target_id=str(dfi_finding.id),
                payload={"action": "overridden", "note": override.note},
            )
        )
        db.commit()
    record(
        results,
        "override_persistence",
        override is not None and override.id is not None,
        "An override row is persisted for an existing finding.",
        f"override_id={getattr(override, 'id', None)}; finding_id={getattr(dfi_finding, 'id', None)}",
        "app/models/audit.py::InteractionOverride; app/api/interactions.py::override_finding",
        "The prototype persists override metadata for later review.",
    )
    post_override_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    dfi_after_override = find_item(post_override_result, fixtures["dfi_interaction_id"])
    record(
        results,
        "override_does_not_suppress_future_finding",
        dfi_after_override is not None and dfi_after_override.suppressed is False,
        "The overridden interaction remains an unsuppressed finding in a later check.",
        (
            f"DFI present={dfi_after_override is not None}; "
            f"suppressed={getattr(dfi_after_override, 'suppressed', None)}"
        ),
        "app/services/orchestrator.py does not query InteractionOverride",
        "Current overrides are audit records and do not automatically alter future check behavior.",
    )

    low_ack = InteractionAcknowledgment(
        patient_id=fixtures["patient_id"],
        interaction_id=fixtures["ddi_interaction_id"],
        acknowledged_by=fixtures["user_id"],
        severity_at_ack=SeverityLevel.moderate,
        note="Evaluation acknowledgment below current severity.",
        is_active=True,
    )
    db.add(low_ack)
    db.commit()
    low_ack_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    ddi_low_ack = find_item(low_ack_result, fixtures["ddi_interaction_id"])
    record(
        results,
        "acknowledgment_severity_escalation_behavior",
        ddi_low_ack is not None and ddi_low_ack.suppressed is False,
        "An acknowledgment below the current major severity does not suppress the DDI.",
        f"ack_severity=moderate; current_severity=major; suppressed={getattr(ddi_low_ack, 'suppressed', None)}",
        "app/services/orchestrator.py acknowledgment severity comparison",
        "The implemented comparison resurfaces a finding when current severity exceeds the stored acknowledgment severity.",
    )

    major_ack = InteractionAcknowledgment(
        patient_id=fixtures["patient_id"],
        interaction_id=fixtures["ddi_interaction_id"],
        acknowledged_by=fixtures["user_id"],
        severity_at_ack=SeverityLevel.major,
        note="Evaluation acknowledgment at current severity.",
        is_active=True,
    )
    db.add(major_ack)
    db.commit()
    ack_result = await run_interaction_check(fixtures["patient_id"], fixtures["user_id"], db)
    ddi_after_ack = find_item(ack_result, fixtures["ddi_interaction_id"])
    record(
        results,
        "acknowledgment_suppression",
        ddi_after_ack is not None and ddi_after_ack.suppressed is True,
        "An acknowledgment at current severity marks the DDI suppressed without deleting it.",
        (
            f"DDI present={ddi_after_ack is not None}; suppressed={getattr(ddi_after_ack, 'suppressed', None)}; "
            f"suppressed_count={ack_result.suppressed_count}"
        ),
        "app/services/orchestrator.py acknowledgment suppression",
        "Acknowledgment changes presentation state while preserving the finding in the result and database.",
    )

    nonexistent_finding_id = 2_147_483_647
    try:
        get_finding_or_404(nonexistent_finding_id, db)
        missing_finding_rejected = False
        missing_finding_observed = "No exception raised."
    except HTTPException as exc:
        missing_finding_rejected = exc.status_code == 404
        missing_finding_observed = f"HTTP {exc.status_code}: {exc.detail}"
    record(
        results,
        "llm_explanation_requires_existing_finding",
        missing_finding_rejected,
        "A nonexistent finding is rejected before explanation generation.",
        missing_finding_observed,
        "app/api/interactions.py::get_finding_or_404 and explain_finding",
        "The explanation endpoint is structurally tied to persisted findings and cannot start from an arbitrary drug pair.",
    )

    boundary_runs: dict[str, InteractionCheckResult] = {}
    with patch(
        "app.services.llm.generate_explanation",
        side_effect=AssertionError("Anthropic/LLM path must not be called by core checking."),
    ):
        boundary_runs["anthropic"] = await run_interaction_check(
            fixtures["patient_id"], fixtures["user_id"], db
        )
    record(
        results,
        "anthropic_not_required_for_core_checking",
        boundary_runs["anthropic"].total_interactions_found >= 1,
        "Core checking completes when the LLM explanation function is replaced with a failing sentinel.",
        f"total_interactions_found={boundary_runs['anthropic'].total_interactions_found}",
        "app/services/orchestrator.py has no Anthropic dependency",
        "The deterministic check path does not require Anthropic; this does not evaluate explanation quality.",
    )

    with patch(
        "app.services.openfda.fetch_citations_for_interaction",
        side_effect=AssertionError("OpenFDA path must not be called by core checking."),
    ):
        boundary_runs["openfda"] = await run_interaction_check(
            fixtures["patient_id"], fixtures["user_id"], db
        )
    record(
        results,
        "openfda_not_required_for_core_checking",
        boundary_runs["openfda"].total_interactions_found >= 1,
        "Core checking completes when OpenFDA citation fetching is replaced with a failing sentinel.",
        f"total_interactions_found={boundary_runs['openfda'].total_interactions_found}",
        "app/services/orchestrator.py has no OpenFDA dependency",
        "OpenFDA is optional explanation context, not a source of interaction existence.",
    )

    with patch(
        "app.services.normalization.normalize_drug_name",
        side_effect=AssertionError("RxNorm normalization must not be called during checking."),
    ):
        boundary_runs["rxnorm"] = await run_interaction_check(
            fixtures["patient_id"], fixtures["user_id"], db
        )
    record(
        results,
        "rxnorm_not_required_at_check_time",
        boundary_runs["rxnorm"].total_interactions_found >= 1,
        "Core checking completes when normalization is replaced with a failing sentinel.",
        f"total_interactions_found={boundary_runs['rxnorm'].total_interactions_found}",
        "app/services/orchestrator.py consumes stored RxCUIs and does not call normalize_drug_name",
        "Once medications are normalized and stored, the check path does not require a live RxNorm call.",
    )

    return {
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
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
            "Evaluates architecture behavior, not clinical correctness or patient outcomes.",
            "Does not evaluate interaction-source completeness.",
            "Does not call RxNorm, OpenFDA, or Anthropic.",
            "Writes clearly labeled synthetic evaluation rows to the configured database.",
            "Duplicate medication handling is evaluated only for duplicate finding prevention; the pair-count metric can include a same-RxCUI self-pair.",
        ],
    }


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# RxCheck Expanded Architecture Evaluation Results",
        "",
        f"Generated at: `{payload['metadata']['generated_at']}`",
        "",
        "Scope: formative architecture behavior, not clinical effectiveness.",
        "",
        "## Summary",
        "",
        f"- Total scenarios: {payload['summary']['total_scenarios']}",
        f"- Passed: {payload['summary']['passed']}",
        f"- Failed: {payload['summary']['failed']}",
        f"- Paid APIs called: {payload['metadata']['external_paid_apis_called']}",
        f"- Free external APIs called: {payload['metadata']['external_free_apis_called']}",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Result | Expected | Observed | Code evidence | Manuscript-safe interpretation |",
        "|---|---|---|---|---|---|",
    ]
    for scenario in payload["scenarios"]:
        status = "PASS" if scenario["passed"] else "FAIL"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{scenario['name']}`",
                    status,
                    markdown_escape(scenario["expected"]),
                    markdown_escape(scenario["observed"]),
                    markdown_escape(scenario["code_evidence"]),
                    markdown_escape(scenario["manuscript_safe_interpretation"]),
                ]
            )
            + " |"
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
    lines.extend(f"- {limitation}" for limitation in payload["limitations"])
    RESULTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def failure_payload(exc: Exception) -> dict[str, Any]:
    return {
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "evaluation_scope": "architecture behavior, not clinical effectiveness",
            "external_paid_apis_called": False,
            "external_free_apis_called": False,
        },
        "summary": {"total_scenarios": 1, "passed": 0, "failed": 1},
        "scenarios": [
            asdict(
                ScenarioResult(
                    name="evaluation_script_runtime",
                    passed=False,
                    expected="Script completes against the configured database.",
                    observed=f"{type(exc).__name__}: {exc}",
                    code_evidence="research/evaluate_rxcheck.py",
                    manuscript_safe_interpretation=(
                        "The evaluation could not execute; no architecture conclusion should be drawn from this run."
                    ),
                    evidence={},
                )
            )
        ],
        "limitations": [
            "Runtime failure prevented scenario execution.",
            "Check database connectivity, schema state, and DATABASE_URL.",
        ],
    }


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run expanded RxCheck architecture evaluation fixtures.")
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
        db.rollback()
        payload = failure_payload(exc)
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
