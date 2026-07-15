#!/usr/bin/env python3
"""Audit unchanged RxCheck persistence and traceability semantics."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import make_url


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[5]


@dataclass
class CriterionResult:
    criterion_id: str
    domain: str
    passed: bool
    expected: str
    observed: str
    interpretation: str
    evidence: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def validate_database_url() -> tuple[str, str, int]:
    from os import environ

    raw_url = environ.get("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("DATABASE_URL must be set explicitly.")
    url = make_url(raw_url)
    if not url.drivername.startswith("postgresql"):
        raise RuntimeError("Only PostgreSQL is allowed.")
    if url.host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Refusing non-loopback database host.")
    if url.database != "rxcheck_traceability":
        raise RuntimeError("Refusing a database outside the traceability naming convention.")
    if not url.port:
        raise RuntimeError("An explicit local database port is required.")
    return url.host, url.database or "", url.port


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=PROJECT_ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def record(
    results: list[CriterionResult],
    criterion_id: str,
    domain: str,
    passed: bool,
    expected: str,
    observed: str,
    interpretation: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    results.append(
        CriterionResult(
            criterion_id=criterion_id,
            domain=domain,
            passed=bool(passed),
            expected=expected,
            observed=observed,
            interpretation=interpretation,
            evidence=evidence or {},
        )
    )


async def execute() -> int:
    args = parse_args()
    host, database_name, port = validate_database_url()
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from app.api.interactions import (
        acknowledge_interaction,
        deactivate_acknowledgment,
        override_finding,
    )
    from app.db.session import Base, SessionLocal, engine
    import app.models.audit  # noqa: F401
    import app.models.check  # noqa: F401
    import app.models.drug  # noqa: F401
    import app.models.interaction  # noqa: F401
    import app.models.patient  # noqa: F401
    from app.models.audit import AuditEvent, InteractionAcknowledgment, InteractionOverride
    from app.models.check import InteractionCheckFinding, InteractionCheckRun
    from app.models.drug import Drug
    from app.models.enums import (
        InteractionSource,
        InteractionType,
        NormalizationStatus,
        OverrideAction,
        SeverityLevel,
    )
    from app.models.interaction import Interaction, InteractionSourceAssertion
    from app.models.patient import Patient, PatientMedication, User
    from app.schemas.interaction import AcknowledgeRequest, OverrideRequest
    from app.services.orchestrator import run_interaction_check

    if inspect(engine).get_table_names():
        raise RuntimeError("Traceability database must be empty.")
    with engine.connect() as connection:
        server_address = connection.scalar(text("SELECT host(inet_server_addr())"))
        server_version = connection.scalar(text("SHOW server_version"))
    if server_address not in {"127.0.0.1", "::1"}:
        raise RuntimeError(f"Server is not loopback-only: {server_address!r}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    results: list[CriterionResult] = []
    fixture_ids: dict[str, Any] = {}

    def make_user(label: str) -> User:
        user = User(
            id=str(uuid.uuid4()),
            email=f"{label}@traceability.rxcheck.local",
            full_name=f"Traceability {label}",
            role="pharmacist",
            is_active=True,
        )
        db.add(user)
        db.flush()
        return user

    def make_patient(user: User) -> Patient:
        patient = Patient(id=str(uuid.uuid4()), created_by=user.id, is_synthetic=True)
        db.add(patient)
        db.flush()
        return patient

    def make_drug(prefix: str, suffix: str, name: str, *, placeholder: bool = False) -> Drug:
        drug = Drug(
            rxcui=f"{prefix}-{suffix}",
            preferred_name=name,
            tty="PLACEHOLDER" if placeholder else "IN",
            is_active=True,
            is_placeholder=placeholder,
        )
        db.add(drug)
        db.flush()
        return drug

    def make_medication(
        patient: Patient,
        user: User,
        drug: Drug,
        *,
        raw_input: str | None = None,
        dose: str | None = None,
    ) -> PatientMedication:
        medication = PatientMedication(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            rxcui=drug.rxcui,
            raw_input=raw_input or drug.preferred_name,
            normalization_status=(
                NormalizationStatus.unmatched
                if drug.is_placeholder
                else NormalizationStatus.matched_exact
            ),
            dose=dose,
            is_active=True,
            added_by=user.id,
        )
        db.add(medication)
        db.flush()
        return medication

    def make_ddi(drug_a: Drug, drug_b: Drug) -> Interaction:
        first, second = sorted((drug_a.rxcui, drug_b.rxcui))
        interaction = Interaction(
            id=str(uuid.uuid4()),
            interaction_type=InteractionType.DDI,
            drug_a_rxcui=first,
            drug_b_rxcui=second,
        )
        db.add(interaction)
        db.flush()
        return interaction

    def make_assertion(
        interaction: Interaction,
        source: InteractionSource,
        severity: SeverityLevel,
        record_id: str,
        *,
        mechanism: str,
        management: str,
    ) -> InteractionSourceAssertion:
        assertion = InteractionSourceAssertion(
            interaction_id=interaction.id,
            source=source,
            source_severity_raw=severity.value.title(),
            severity=severity,
            mechanism=mechanism,
            management=management,
            evidence_url=f"https://example.invalid/{record_id}",
            source_record_id=record_id,
            raw_payload={"traceability_fixture": True, "record_id": record_id},
        )
        db.add(assertion)
        db.flush()
        return assertion

    try:
        sentinel_error = AssertionError("External service called during traceability audit.")
        with (
            patch("app.services.llm.generate_explanation", side_effect=sentinel_error),
            patch(
                "app.services.openfda.fetch_citations_for_interaction",
                side_effect=sentinel_error,
            ),
            patch("app.services.normalization.normalize_drug_name", side_effect=sentinel_error),
        ):
            # T01-T02: below-threshold invocation.
            user_insufficient = make_user("insufficient")
            patient_insufficient = make_patient(user_insufficient)
            verified = make_drug("trace-insufficient", "100", "Insufficient Verified Drug")
            placeholder = make_drug(
                "trace-insufficient",
                "900",
                "Insufficient Placeholder Drug",
                placeholder=True,
            )
            make_medication(patient_insufficient, user_insufficient, verified)
            make_medication(patient_insufficient, user_insufficient, placeholder)
            db.commit()
            insufficient = await run_interaction_check(
                patient_insufficient.id,
                user_insufficient.id,
                db,
            )
            insufficient_run_count = int(
                db.scalar(
                    select(func.count(InteractionCheckRun.id)).where(
                        InteractionCheckRun.patient_id == patient_insufficient.id
                    )
                )
            )
            record(
                results,
                "T01",
                "insufficient_input",
                insufficient.warning is not None
                and insufficient.total_medications == 1
                and insufficient.total_pairs_checked == 0,
                "A below-threshold invocation returns a controlled warning and zero pairs.",
                f"warning={insufficient.warning!r}; medications={insufficient.total_medications}; pairs={insufficient.total_pairs_checked}",
                "The core returns a controlled insufficient-input result after excluding the placeholder.",
            )
            record(
                results,
                "T02",
                "attempt_history",
                bool(insufficient.run_id) and insufficient_run_count == 1,
                "Every check invocation has a persisted run or attempt record.",
                f"run_id={insufficient.run_id!r}; persisted_patient_runs={insufficient_run_count}",
                "Below-threshold attempts are not persisted, so check history is incomplete for attempted invocations.",
            )

            # T03-T05: duplicate rows, pair count, and manual-only source reporting.
            user_duplicate = make_user("duplicate")
            patient_duplicate = make_patient(user_duplicate)
            duplicate_a = make_drug("trace-duplicate", "100", "Duplicate Drug A")
            duplicate_b = make_drug("trace-duplicate", "200", "Duplicate Drug B")
            make_medication(patient_duplicate, user_duplicate, duplicate_a)
            make_medication(
                patient_duplicate,
                user_duplicate,
                duplicate_a,
                raw_input="Duplicate Drug A repeated",
            )
            make_medication(patient_duplicate, user_duplicate, duplicate_b)
            duplicate_interaction = make_ddi(duplicate_a, duplicate_b)
            make_assertion(
                duplicate_interaction,
                InteractionSource.manual,
                SeverityLevel.major,
                "trace-duplicate-manual",
                mechanism="Manual-only duplicate fixture mechanism.",
                management="Manual-only duplicate fixture management.",
            )
            db.commit()
            duplicate_result = await run_interaction_check(
                patient_duplicate.id,
                user_duplicate.id,
                db,
            )
            duplicate_run = db.get(InteractionCheckRun, duplicate_result.run_id)
            duplicate_findings = list(
                db.scalars(
                    select(InteractionCheckFinding).where(
                        InteractionCheckFinding.run_id == duplicate_result.run_id
                    )
                ).all()
            )
            finding_source_union = sorted(
                {source for finding in duplicate_findings for source in finding.sources_at_run}
            )
            distinct_pair_count = 1
            record(
                results,
                "T03",
                "duplicate_finding",
                duplicate_result.total_interactions_found == 1
                and len(duplicate_result.summaries) == 1
                and len(duplicate_findings) == 1,
                "Duplicate active medication rows do not create duplicate findings.",
                (
                    f"returned_interactions={duplicate_result.total_interactions_found}; "
                    f"returned_summaries={len(duplicate_result.summaries)}; persisted_findings={len(duplicate_findings)}"
                ),
                "Canonical pair lookup prevents duplicate findings for the repeated RxCUI.",
            )
            record(
                results,
                "T04",
                "pair_accounting",
                duplicate_result.total_pairs_checked == distinct_pair_count,
                "Pair count equals unordered pairs of distinct evaluated RxCUIs.",
                (
                    f"active_rows={duplicate_result.total_medications}; distinct_rxcuis=2; "
                    f"expected_distinct_pairs={distinct_pair_count}; reported_pairs={duplicate_result.total_pairs_checked}"
                ),
                "A same-RxCUI pair is included, so the metric overstates distinct-drug pairs.",
            )
            record(
                results,
                "T05",
                "source_reporting",
                sorted(duplicate_run.sources_used) == finding_source_union,
                "Run-level sources equal the union of persisted finding sources.",
                f"run_sources={duplicate_run.sources_used}; finding_source_union={finding_source_union}",
                "The run reports DDInter even though its only finding source is manual.",
            )

            # T06-T08: immutable selected snapshots versus incomplete display reconstruction.
            user_snapshot = make_user("snapshot")
            patient_snapshot = make_patient(user_snapshot)
            snapshot_a = make_drug("trace-snapshot", "100", "Snapshot Drug A")
            snapshot_b = make_drug("trace-snapshot", "200", "Snapshot Drug B")
            snapshot_med_a = make_medication(
                patient_snapshot,
                user_snapshot,
                snapshot_a,
                dose="5 mg",
            )
            make_medication(patient_snapshot, user_snapshot, snapshot_b, dose="10 mg")
            snapshot_interaction = make_ddi(snapshot_a, snapshot_b)
            snapshot_ddinter = make_assertion(
                snapshot_interaction,
                InteractionSource.DDInter,
                SeverityLevel.moderate,
                "trace-snapshot-ddinter",
                mechanism="Original DDInter mechanism.",
                management="Original DDInter management.",
            )
            snapshot_manual = make_assertion(
                snapshot_interaction,
                InteractionSource.manual,
                SeverityLevel.major,
                "trace-snapshot-manual",
                mechanism="Original manual mechanism.",
                management="Original manual management.",
            )
            db.commit()
            snapshot_result = await run_interaction_check(
                patient_snapshot.id,
                user_snapshot.id,
                db,
            )
            snapshot_run = db.get(InteractionCheckRun, snapshot_result.run_id)
            snapshot_finding = db.scalar(
                select(InteractionCheckFinding).where(
                    InteractionCheckFinding.run_id == snapshot_result.run_id,
                    InteractionCheckFinding.interaction_id == snapshot_interaction.id,
                )
            )
            original_medication_snapshot = copy.deepcopy(snapshot_run.medications_snapshot)
            original_finding_snapshot = {
                "max_severity_at_run": snapshot_finding.max_severity_at_run.value,
                "sources_at_run": list(snapshot_finding.sources_at_run),
                "sources_conflicted": snapshot_finding.sources_conflicted,
                "suppressed_by_ack": snapshot_finding.suppressed_by_ack,
            }
            original_evidence_values = [
                snapshot_ddinter.mechanism,
                snapshot_ddinter.management,
                snapshot_ddinter.evidence_url,
                snapshot_ddinter.source_record_id,
                snapshot_manual.mechanism,
                snapshot_manual.management,
                snapshot_manual.evidence_url,
                snapshot_manual.source_record_id,
            ]

            snapshot_med_a.dose = "99 mg"
            snapshot_med_a.is_active = False
            snapshot_a.preferred_name = "Mutated Snapshot Drug A"
            snapshot_b.preferred_name = "Mutated Snapshot Drug B"
            for assertion in (snapshot_ddinter, snapshot_manual):
                assertion.source_severity_raw = "Minor"
                assertion.severity = SeverityLevel.minor
                assertion.mechanism = "Mutated mechanism."
                assertion.management = "Mutated management."
                assertion.evidence_url = "https://example.invalid/mutated"
                assertion.source_record_id = f"mutated-{assertion.id}"
                assertion.raw_payload = {"mutated": True}
            db.commit()
            db.expire_all()
            persisted_snapshot_run = db.get(InteractionCheckRun, snapshot_result.run_id)
            persisted_snapshot_finding = db.get(InteractionCheckFinding, snapshot_finding.id)
            observed_finding_snapshot = {
                "max_severity_at_run": persisted_snapshot_finding.max_severity_at_run.value,
                "sources_at_run": list(persisted_snapshot_finding.sources_at_run),
                "sources_conflicted": persisted_snapshot_finding.sources_conflicted,
                "suppressed_by_ack": persisted_snapshot_finding.suppressed_by_ack,
            }
            finding_columns = set(InteractionCheckFinding.__table__.columns.keys())
            evidence_snapshot_fields = {
                "mechanism",
                "management",
                "evidence_url",
                "source_record_id",
                "raw_payload",
            }
            missing_evidence_snapshot_fields = sorted(evidence_snapshot_fields - finding_columns)
            snapshot_blob = json.dumps(
                {
                    "run": persisted_snapshot_run.medications_snapshot,
                    "finding": observed_finding_snapshot,
                },
                sort_keys=True,
            )
            original_evidence_recoverable = all(
                value is not None and value in snapshot_blob for value in original_evidence_values
            )
            record(
                results,
                "T06",
                "medication_snapshot",
                persisted_snapshot_run.medications_snapshot == original_medication_snapshot,
                "Completed-run medication snapshot remains unchanged after live row edits.",
                (
                    f"snapshot_unchanged={persisted_snapshot_run.medications_snapshot == original_medication_snapshot}; "
                    f"snapshot_entries={len(persisted_snapshot_run.medications_snapshot)}"
                ),
                "The selected medication fields in the JSON snapshot are stable after later edits.",
            )
            record(
                results,
                "T07",
                "finding_snapshot",
                observed_finding_snapshot == original_finding_snapshot,
                "Selected finding fields remain unchanged after live assertion edits.",
                f"original={original_finding_snapshot}; observed={observed_finding_snapshot}",
                "Run-time maximum severity, sources, conflict, and suppression state are stable snapshots.",
            )
            record(
                results,
                "T08",
                "display_reconstruction",
                not missing_evidence_snapshot_fields and original_evidence_recoverable,
                "Run/finding snapshots preserve prior displayed evidence details.",
                (
                    f"missing_finding_snapshot_fields={missing_evidence_snapshot_fields}; "
                    f"original_evidence_recoverable_from_snapshots={original_evidence_recoverable}"
                ),
                "Mechanism, management/effect, evidence URL, source record, and raw payload are live assertion data, not historical finding snapshots.",
            )

            # T09-T15: acknowledgment, escalation, deactivation, and override workflows.
            user_workflow = make_user("workflow")
            patient_workflow = make_patient(user_workflow)
            workflow_a = make_drug("trace-workflow", "100", "Workflow Drug A")
            workflow_b = make_drug("trace-workflow", "200", "Workflow Drug B")
            make_medication(patient_workflow, user_workflow, workflow_a)
            make_medication(patient_workflow, user_workflow, workflow_b)
            workflow_interaction = make_ddi(workflow_a, workflow_b)
            workflow_assertion = make_assertion(
                workflow_interaction,
                InteractionSource.DDInter,
                SeverityLevel.major,
                "trace-workflow-ddinter",
                mechanism="Workflow mechanism.",
                management="Workflow management.",
            )
            db.commit()
            workflow_baseline = await run_interaction_check(
                patient_workflow.id,
                user_workflow.id,
                db,
            )
            baseline_finding = db.scalar(
                select(InteractionCheckFinding).where(
                    InteractionCheckFinding.run_id == workflow_baseline.run_id,
                    InteractionCheckFinding.interaction_id == workflow_interaction.id,
                )
            )
            acknowledgment_response = acknowledge_interaction(
                patient_workflow.id,
                workflow_interaction.id,
                AcknowledgeRequest(
                    note="Traceability acknowledgment.",
                    user_id=user_workflow.id,
                ),
                db,
            )
            acknowledgment_row = db.get(
                InteractionAcknowledgment,
                acknowledgment_response.id,
            )
            acknowledgment_event = db.scalar(
                select(AuditEvent)
                .where(
                    AuditEvent.event_type == "interaction_acknowledged",
                    AuditEvent.target_id == workflow_interaction.id,
                )
                .order_by(AuditEvent.id.desc())
            )
            acknowledgment_persisted = (
                acknowledgment_row is not None
                and acknowledgment_row.patient_id == patient_workflow.id
                and acknowledgment_row.acknowledged_by == user_workflow.id
                and acknowledgment_row.severity_at_ack == SeverityLevel.major
                and acknowledgment_row.note == "Traceability acknowledgment."
                and acknowledgment_event is not None
                and acknowledgment_event.user_id == user_workflow.id
                and acknowledgment_event.payload.get("note") == "Traceability acknowledgment."
            )
            record(
                results,
                "T09",
                "acknowledgment_record",
                acknowledgment_persisted,
                "Acknowledgment state and creation event persist with tested user and payload.",
                (
                    f"ack_id={getattr(acknowledgment_row, 'id', None)}; "
                    f"ack_user={getattr(acknowledgment_row, 'acknowledged_by', None)}; "
                    f"event_user={getattr(acknowledgment_event, 'user_id', None)}"
                ),
                "The acknowledgment row and selected creation event are persisted.",
            )

            suppressed_result = await run_interaction_check(
                patient_workflow.id,
                user_workflow.id,
                db,
            )
            suppressed_item = next(
                item
                for item in suppressed_result.summaries
                if item.interaction_id == workflow_interaction.id
            )
            suppressed_finding = db.get(InteractionCheckFinding, suppressed_item.finding_id)
            record(
                results,
                "T10",
                "suppression_snapshot",
                suppressed_item.suppressed
                and suppressed_result.suppressed_count == 1
                and suppressed_finding.suppressed_by_ack,
                "Same-severity acknowledgment suppresses presentation while preserving the finding and state.",
                (
                    f"returned_suppressed={suppressed_item.suppressed}; "
                    f"suppressed_count={suppressed_result.suppressed_count}; "
                    f"persisted_suppressed={suppressed_finding.suppressed_by_ack}"
                ),
                "Suppression state is returned and saved without deleting the interaction finding.",
            )

            workflow_assertion.source_severity_raw = "Contraindicated"
            workflow_assertion.severity = SeverityLevel.contraindicated
            db.commit()
            escalated_result = await run_interaction_check(
                patient_workflow.id,
                user_workflow.id,
                db,
            )
            escalated_item = next(
                item
                for item in escalated_result.summaries
                if item.interaction_id == workflow_interaction.id
            )
            escalated_finding = db.get(InteractionCheckFinding, escalated_item.finding_id)
            record(
                results,
                "T11",
                "severity_escalation",
                not escalated_item.suppressed
                and escalated_item.summary.max_severity == SeverityLevel.contraindicated
                and not escalated_finding.suppressed_by_ack,
                "Higher current severity resurfaces relative to stored acknowledgment severity.",
                (
                    f"ack_severity={acknowledgment_row.severity_at_ack.value}; "
                    f"current_severity={escalated_item.summary.max_severity.value}; "
                    f"suppressed={escalated_item.suppressed}"
                ),
                "The comparison resurfaces the finding when current severity exceeds the stored acknowledgment severity.",
            )

            deactivate_acknowledgment(
                patient_workflow.id,
                workflow_interaction.id,
                db,
            )
            db.expire_all()
            deactivated_row = db.get(InteractionAcknowledgment, acknowledgment_response.id)
            deactivation_event = db.scalar(
                select(AuditEvent)
                .where(
                    AuditEvent.event_type == "interaction_acknowledgment_removed",
                    AuditEvent.target_id == workflow_interaction.id,
                )
                .order_by(AuditEvent.id.desc())
            )
            record(
                results,
                "T12",
                "acknowledgment_deactivation",
                deactivated_row is not None
                and not deactivated_row.is_active
                and deactivation_event is not None
                and deactivation_event.payload.get("patient_id") == patient_workflow.id,
                "Deactivation persists and creates a removal audit event.",
                (
                    f"ack_active={getattr(deactivated_row, 'is_active', None)}; "
                    f"removal_event_id={getattr(deactivation_event, 'id', None)}"
                ),
                "The acknowledgment is retained as inactive and a selected removal event is written.",
            )
            record(
                results,
                "T13",
                "deactivation_identity",
                deactivation_event is not None
                and deactivation_event.user_id == user_workflow.id,
                "Removal event is bound to the tested workflow user.",
                (
                    f"tested_user={user_workflow.id}; "
                    f"removal_event_user={getattr(deactivation_event, 'user_id', None)}"
                ),
                "The endpoint attributes removal to the default user rather than an authenticated actor or the tested workflow user.",
            )

            override_response = override_finding(
                escalated_finding.id,
                OverrideRequest(
                    action=OverrideAction.overridden,
                    note="Traceability override.",
                    user_id=user_workflow.id,
                ),
                db,
            )
            override_row = db.get(InteractionOverride, override_response.id)
            override_event = db.scalar(
                select(AuditEvent)
                .where(
                    AuditEvent.event_type == "interaction_override",
                    AuditEvent.target_id == str(escalated_finding.id),
                )
                .order_by(AuditEvent.id.desc())
            )
            override_persisted = (
                override_row is not None
                and override_row.finding_id == escalated_finding.id
                and override_row.user_id == user_workflow.id
                and override_row.action == OverrideAction.overridden
                and override_row.severity_overridden == SeverityLevel.contraindicated
                and override_row.note == "Traceability override."
                and override_event is not None
                and override_event.user_id == user_workflow.id
                and override_event.payload.get("action") == "overridden"
                and override_event.payload.get("note") == "Traceability override."
            )
            record(
                results,
                "T14",
                "override_record",
                override_persisted,
                "Override and audit event persist with tested user, action, severity, and note.",
                (
                    f"override_id={getattr(override_row, 'id', None)}; "
                    f"override_user={getattr(override_row, 'user_id', None)}; "
                    f"severity={getattr(getattr(override_row, 'severity_overridden', None), 'value', None)}"
                ),
                "The finding-level override and selected audit event are persisted.",
            )

            post_override = await run_interaction_check(
                patient_workflow.id,
                user_workflow.id,
                db,
            )
            post_override_item = next(
                item
                for item in post_override.summaries
                if item.interaction_id == workflow_interaction.id
            )
            later_override_count = int(
                db.scalar(
                    select(func.count(InteractionOverride.id)).where(
                        InteractionOverride.finding_id == post_override_item.finding_id
                    )
                )
            )
            original_override_count = int(
                db.scalar(
                    select(func.count(InteractionOverride.id)).where(
                        InteractionOverride.finding_id == escalated_finding.id
                    )
                )
            )
            record(
                results,
                "T15",
                "override_semantics",
                not post_override_item.suppressed
                and original_override_count == 1
                and later_override_count == 0,
                "Override remains attached to original finding and does not silently change a later check.",
                (
                    f"later_suppressed={post_override_item.suppressed}; "
                    f"original_finding_overrides={original_override_count}; "
                    f"later_finding_overrides={later_override_count}"
                ),
                "Overrides are historical records for one finding; later checks are neither suppressed nor annotated by them.",
            )

            fixture_ids = {
                "patients": {
                    "insufficient": patient_insufficient.id,
                    "duplicate": patient_duplicate.id,
                    "snapshot": patient_snapshot.id,
                    "workflow": patient_workflow.id,
                },
                "runs": {
                    "duplicate": duplicate_result.run_id,
                    "snapshot": snapshot_result.run_id,
                    "workflow_baseline": workflow_baseline.run_id,
                    "workflow_suppressed": suppressed_result.run_id,
                    "workflow_escalated": escalated_result.run_id,
                    "workflow_post_override": post_override.run_id,
                },
                "interactions": {
                    "duplicate": duplicate_interaction.id,
                    "snapshot": snapshot_interaction.id,
                    "workflow": workflow_interaction.id,
                },
                "acknowledgment": acknowledgment_response.id,
                "override": override_response.id,
                "baseline_workflow_finding": baseline_finding.id,
            }

        passed_count = sum(result.passed for result in results)
        failed_count = len(results) - passed_count
        audit_contract_passed = len(results) == 15 and failed_count == 0
        table_counts = {}
        for model, label in (
            (InteractionCheckRun, "interaction_check_runs"),
            (InteractionCheckFinding, "interaction_check_findings"),
            (InteractionAcknowledgment, "interaction_acknowledgments"),
            (InteractionOverride, "interaction_overrides"),
            (AuditEvent, "audit_events"),
        ):
            table_counts[label] = int(db.scalar(select(func.count(model.id))))

        source_paths = [
            "app/services/orchestrator.py",
            "app/api/interactions.py",
            "app/models/check.py",
            "app/models/audit.py",
            "app/models/interaction.py",
            "app/models/patient.py",
        ]
        payload = {
            "metadata": {
                "generated_at": datetime.now(UTC).isoformat(),
                "repository_head_at_execution": git_output("rev-parse", "HEAD"),
                "evaluated_source_commit": git_output(
                    "log",
                    "-1",
                    "--format=%H",
                    "--",
                    *source_paths,
                ),
                "database": {
                    "host": host,
                    "port": port,
                    "name": database_name,
                    "server_address": server_address,
                    "server_version": server_version,
                    "credentials_recorded": False,
                },
                "environment": {
                    "platform": platform.platform(),
                    "machine": platform.machine(),
                    "python": sys.version,
                    "packages": {
                        "fastapi": package_version("fastapi"),
                        "pydantic": package_version("pydantic"),
                        "sqlalchemy": package_version("sqlalchemy"),
                        "psycopg2-binary": package_version("psycopg2-binary"),
                    },
                },
                "schema_setup": "SQLAlchemy Base.metadata.create_all (not Alembic)",
                "external_api_calls": 0,
                "runner_sha256": sha256_file(SCRIPT_PATH),
                "source_sha256": {
                    path: sha256_file(PROJECT_ROOT / path) for path in source_paths
                },
            },
            "summary": {
                "criteria_expected": 15,
                "criteria_completed": len(results),
                "passed": passed_count,
                "failed": failed_count,
                "audit_contract_passed": audit_contract_passed,
                "external_api_calls": 0,
            },
            "criteria": [asdict(result) for result in results],
            "fixture_ids": fixture_ids,
            "table_counts_after_audit": table_counts,
            "static_scope_observations": [
                "AuditEvent rows are ordinary mutable database rows; no append-only or tamper-evident control is defined.",
                "The application has no authentication or route-level authorization binding the supplied/default user IDs to a caller.",
                "No read-access audit path is implemented.",
            ],
            "limitations": [
                "Synthetic fixtures and direct production-function calls, not clinical or authenticated user evaluation.",
                "One local database environment and one execution.",
                "No concurrency, retention, tamper, authorization, read-access, or regulatory-compliance test.",
                "Clinical appropriateness of acknowledgments and overrides is outside scope.",
            ],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(
            f"criteria={len(results)}/15; passed={passed_count}; failed={failed_count}; "
            f"audit_contract_passed={audit_contract_passed}"
        )
        return 0 if audit_contract_passed else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(execute()))
