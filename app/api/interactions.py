from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.api.patients import ensure_default_user, get_patient_or_404
from app.db.session import get_db
from app.models.audit import AuditEvent, InteractionAcknowledgment, InteractionOverride
from app.models.check import InteractionCheckFinding, LlmExplanation
from app.models.interaction import Interaction, InteractionSourceAssertion
from app.models.patient import User
from app.schemas import (
    AcknowledgmentResponse,
    AcknowledgeRequest,
    LlmExplanationResult,
    OverrideRequest,
    OverrideResponse,
)
from app.services.llm import explanation_row_to_result, generate_explanation

router = APIRouter()

SEVERITY_ORDER = {
    "unknown": 0,
    "minor": 1,
    "moderate": 2,
    "major": 3,
    "contraindicated": 4,
}


def get_finding_or_404(finding_id: int, db: Session) -> InteractionCheckFinding:
    finding = db.scalar(
        select(InteractionCheckFinding)
        .options(selectinload(InteractionCheckFinding.interaction))
        .where(InteractionCheckFinding.id == finding_id)
    )
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return finding


def get_interaction_or_404(interaction_id: str, db: Session) -> Interaction:
    interaction = db.scalar(
        select(Interaction)
        .options(selectinload(Interaction.assertions))
        .where(Interaction.id == interaction_id)
    )
    if interaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    return interaction


def _resolve_user(user_id: Optional[str], db: Session) -> User:
    default_user = ensure_default_user(db)
    if not user_id:
        return default_user

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _current_max_severity(interaction: Interaction):
    severities = [assertion.severity for assertion in interaction.assertions]
    if not severities:
        return None
    return max(severities, key=lambda sev: SEVERITY_ORDER[sev.value])


@router.post("/findings/{finding_id}/explain", response_model=LlmExplanationResult)
async def explain_finding(finding_id: int, db: Session = Depends(get_db)) -> LlmExplanationResult:
    finding = get_finding_or_404(finding_id, db)
    if finding.llm_explanation_id:
        explanation = db.get(LlmExplanation, finding.llm_explanation_id)
        if explanation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Explanation not found")
        return explanation_row_to_result(explanation)

    try:
        return await generate_explanation(finding.interaction_id, finding_id, db)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/findings/{finding_id}/override", response_model=OverrideResponse, status_code=status.HTTP_201_CREATED)
def override_finding(
    finding_id: int,
    payload: OverrideRequest,
    db: Session = Depends(get_db),
) -> OverrideResponse:
    finding = get_finding_or_404(finding_id, db)
    user = _resolve_user(payload.user_id, db)

    override = InteractionOverride(
        finding_id=finding.id,
        user_id=user.id,
        action=payload.action,
        severity_overridden=finding.max_severity_at_run,
        note=payload.note,
    )
    db.add(override)
    db.flush()

    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="interaction_override",
            target_type="finding",
            target_id=str(finding_id),
            payload={"action": payload.action.value, "note": payload.note},
        )
    )
    db.commit()
    db.refresh(override)

    return OverrideResponse(
        id=override.id,
        finding_id=override.finding_id,
        user_id=override.user_id,
        action=override.action,
        severity_overridden=override.severity_overridden,
        note=override.note,
        occurred_at=override.occurred_at,
    )


@router.post(
    "/patients/{patient_id}/interactions/{interaction_id}/acknowledge",
    response_model=AcknowledgmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def acknowledge_interaction(
    patient_id: str,
    interaction_id: str,
    payload: AcknowledgeRequest,
    db: Session = Depends(get_db),
) -> AcknowledgmentResponse:
    get_patient_or_404(patient_id, db)
    interaction = get_interaction_or_404(interaction_id, db)
    user = _resolve_user(payload.user_id, db)

    max_severity = _current_max_severity(interaction)
    if max_severity is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interaction has no source assertions")

    acknowledgment = InteractionAcknowledgment(
        patient_id=patient_id,
        interaction_id=interaction_id,
        acknowledged_by=user.id,
        severity_at_ack=max_severity,
        expires_at=datetime.utcnow() + timedelta(days=payload.expires_days) if payload.expires_days else None,
        note=payload.note,
        is_active=True,
    )
    db.add(acknowledgment)
    db.flush()

    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="interaction_acknowledged",
            target_type="interaction",
            target_id=interaction_id,
            payload={"note": payload.note, "expires_days": payload.expires_days},
        )
    )
    db.commit()
    db.refresh(acknowledgment)

    return AcknowledgmentResponse(
        id=acknowledgment.id,
        patient_id=acknowledgment.patient_id,
        interaction_id=acknowledgment.interaction_id,
        acknowledged_by=acknowledgment.acknowledged_by,
        acknowledged_at=acknowledgment.acknowledged_at,
        severity_at_ack=acknowledgment.severity_at_ack,
        expires_at=acknowledgment.expires_at,
        note=acknowledgment.note,
        is_active=acknowledgment.is_active,
    )


@router.delete("/patients/{patient_id}/interactions/{interaction_id}/acknowledge", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_acknowledgment(
    patient_id: str,
    interaction_id: str,
    db: Session = Depends(get_db),
) -> Response:
    get_patient_or_404(patient_id, db)
    get_interaction_or_404(interaction_id, db)
    user = ensure_default_user(db)

    acknowledgment = db.scalar(
        select(InteractionAcknowledgment)
        .where(
            InteractionAcknowledgment.patient_id == patient_id,
            InteractionAcknowledgment.interaction_id == interaction_id,
            InteractionAcknowledgment.is_active.is_(True),
        )
        .order_by(desc(InteractionAcknowledgment.acknowledged_at))
    )
    if acknowledgment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acknowledgment not found")

    acknowledgment.is_active = False
    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="interaction_acknowledgment_removed",
            target_type="interaction",
            target_id=interaction_id,
            payload={"patient_id": patient_id},
        )
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
