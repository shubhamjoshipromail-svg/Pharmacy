from __future__ import annotations

import itertools
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import or_, select, tuple_
from sqlalchemy.orm import Session, selectinload

from app.models.audit import InteractionAcknowledgment
from app.models.check import InteractionCheckFinding, InteractionCheckRun
from app.models.drug import Drug
from app.models.enums import InteractionSource, InteractionType, SeverityLevel
from app.models.interaction import Interaction, InteractionSourceAssertion
from app.models.patient import PatientMedication
from app.schemas import InteractionSummary, build_summary
from app.services.checks import get_hub_scores


class InteractionSummaryWithSuppression(BaseModel):
    summary: InteractionSummary
    suppressed: bool
    finding_id: int
    interaction_id: str


class InteractionCheckResult(BaseModel):
    run_id: str
    patient_id: str
    total_medications: int
    total_pairs_checked: int
    total_interactions_found: int
    critical_count: int
    major_count: int
    moderate_count: int
    minor_count: int
    suppressed_count: int
    warning: Optional[str]
    summaries: list[InteractionSummaryWithSuppression]
    checked_at: datetime
    duration_ms: int


SEVERITY_ORDER = {
    SeverityLevel.unknown: 0,
    SeverityLevel.minor: 1,
    SeverityLevel.moderate: 2,
    SeverityLevel.major: 3,
    SeverityLevel.contraindicated: 4,
}


def _severity_rank(severity: SeverityLevel) -> int:
    return SEVERITY_ORDER[severity]


async def run_interaction_check(
    patient_id: str,
    user_id: str,
    db: Session,
) -> InteractionCheckResult:
    started_at = time.perf_counter()
    now = datetime.utcnow()

    medications = list(
        db.scalars(
            select(PatientMedication)
            .join(Drug, PatientMedication.rxcui == Drug.rxcui)
            .options(selectinload(PatientMedication.drug))
            .where(PatientMedication.patient_id == patient_id)
            .where(PatientMedication.is_active.is_(True))
            .where(Drug.is_placeholder.is_(False))
        ).all()
    )

    if len(medications) < 2:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        return InteractionCheckResult(
            run_id="",
            patient_id=patient_id,
            total_medications=len(medications),
            total_pairs_checked=0,
            total_interactions_found=0,
            critical_count=0,
            major_count=0,
            moderate_count=0,
            minor_count=0,
            suppressed_count=0,
            warning="Insufficient medications for interaction check — at least 2 required",
            summaries=[],
            checked_at=now,
            duration_ms=duration_ms,
        )

    active_rxcuis = [medication.rxcui for medication in medications]
    canonical_pairs = sorted(
        {tuple(sorted(pair)) for pair in itertools.combinations(active_rxcuis, 2)}
    )

    interaction_options = (
        selectinload(Interaction.assertions),
        selectinload(Interaction.llm_explanations),
        selectinload(Interaction.drug_a),
        selectinload(Interaction.drug_b),
        selectinload(Interaction.food),
        selectinload(Interaction.condition),
    )

    ddi_interactions = []
    if canonical_pairs:
        ddi_interactions = list(
            db.scalars(
                select(Interaction)
                .options(*interaction_options)
                .where(Interaction.interaction_type == InteractionType.DDI)
                .where(tuple_(Interaction.drug_a_rxcui, Interaction.drug_b_rxcui).in_(canonical_pairs))
            ).all()
        )

    non_ddi_interactions = list(
        db.scalars(
            select(Interaction)
            .options(*interaction_options)
            .where(Interaction.drug_a_rxcui.in_(active_rxcuis))
            .where(Interaction.interaction_type.in_([InteractionType.DFI, InteractionType.DDSI]))
        ).all()
    )

    interactions = ddi_interactions + non_ddi_interactions
    interaction_ids = [interaction.id for interaction in interactions]

    assertions_by_interaction: dict[str, list[InteractionSourceAssertion]] = defaultdict(list)
    if interaction_ids:
        assertions = db.scalars(
            select(InteractionSourceAssertion).where(InteractionSourceAssertion.interaction_id.in_(interaction_ids))
        ).all()
        for assertion in assertions:
            assertions_by_interaction[assertion.interaction_id].append(assertion)

    hub_scores = get_hub_scores(active_rxcuis, db)

    ranked_items: list[dict] = []
    for interaction in interactions:
        assertions = assertions_by_interaction.get(interaction.id, [])
        summary = build_summary(interaction, assertions, hub_scores)
        ranked_items.append(
            {
                "interaction": interaction,
                "assertions": assertions,
                "summary": summary,
            }
        )

    ranked_items.sort(
        key=lambda item: (
            -_severity_rank(item["summary"].severity),
            not item["summary"].sources_conflict,
            -(item["summary"].hub_score_a or 0),
            item["summary"].drug_a_name,
            item["summary"].drug_b_name,
        )
    )

    active_acknowledgments = list(
        db.scalars(
            select(InteractionAcknowledgment).where(
                InteractionAcknowledgment.patient_id == patient_id,
                InteractionAcknowledgment.is_active.is_(True),
                or_(
                    InteractionAcknowledgment.expires_at.is_(None),
                    InteractionAcknowledgment.expires_at > now,
                ),
            )
        ).all()
    )
    ack_by_interaction: dict[str, list[InteractionAcknowledgment]] = defaultdict(list)
    for acknowledgment in active_acknowledgments:
        ack_by_interaction[acknowledgment.interaction_id].append(acknowledgment)

    for item in ranked_items:
        summary = item["summary"]
        matching_acks = ack_by_interaction.get(item["interaction"].id, [])
        item["suppressed"] = any(
            _severity_rank(ack.severity_at_ack) >= _severity_rank(summary.max_severity)
            for ack in matching_acks
        )

    medication_snapshot = [
        {
            "id": medication.id,
            "rxcui": medication.rxcui,
            "preferred_name": medication.drug.preferred_name,
            "dose": medication.dose,
            "is_active": medication.is_active,
        }
        for medication in medications
    ]
    run = InteractionCheckRun(
        patient_id=patient_id,
        run_by=user_id,
        medications_snapshot=medication_snapshot,
        sources_used=[InteractionSource.DDInter.value],
    )
    db.add(run)
    db.flush()

    result_summaries: list[InteractionSummaryWithSuppression] = []
    unsuppressed_counts = {
        SeverityLevel.contraindicated: 0,
        SeverityLevel.major: 0,
        SeverityLevel.moderate: 0,
        SeverityLevel.minor: 0,
    }
    suppressed_count = 0

    for item in ranked_items:
        summary = item["summary"]
        finding = InteractionCheckFinding(
            run_id=run.id,
            interaction_id=item["interaction"].id,
            max_severity_at_run=summary.max_severity,
            sources_at_run=sorted({assertion.source.value for assertion in item["assertions"]}) or [InteractionSource.DDInter.value],
            sources_conflicted=summary.sources_conflict,
            suppressed_by_ack=item["suppressed"],
        )
        db.add(finding)
        db.flush()

        result_summaries.append(
            InteractionSummaryWithSuppression(
                summary=summary,
                suppressed=item["suppressed"],
                finding_id=finding.id,
                interaction_id=item["interaction"].id,
            )
        )

        if item["suppressed"]:
            suppressed_count += 1
        elif summary.max_severity in unsuppressed_counts:
            unsuppressed_counts[summary.max_severity] += 1

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    run.duration_ms = duration_ms
    db.commit()

    return InteractionCheckResult(
        run_id=run.id,
        patient_id=patient_id,
        total_medications=len(medications),
        total_pairs_checked=len(canonical_pairs),
        total_interactions_found=len(ranked_items),
        critical_count=unsuppressed_counts[SeverityLevel.contraindicated],
        major_count=unsuppressed_counts[SeverityLevel.major],
        moderate_count=unsuppressed_counts[SeverityLevel.moderate],
        minor_count=unsuppressed_counts[SeverityLevel.minor],
        suppressed_count=suppressed_count,
        warning=None,
        summaries=result_summaries,
        checked_at=run.run_at,
        duration_ms=duration_ms,
    )
