from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.check import InteractionCheckFinding, InteractionCheckRun
from app.models.drug import Drug
from app.models.patient import Patient, PatientIdentifier, PatientMedication, User
from app.schemas.patient import (
    CheckRunHistoryResponse,
    CheckRunRequest,
    MedicationAdd,
    MedicationCandidateResponse,
    MedicationCreateResponse,
    MedicationResponse,
    PatientCreate,
    PatientListResponse,
    PatientResponse,
)
from app.services.normalization import normalize_drug_name
from app.services.orchestrator import InteractionCheckResult, run_interaction_check

router = APIRouter()

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_EMAIL = "default@drugchecker.local"


def ensure_default_user(db: Session) -> User:
    user = db.get(User, DEFAULT_USER_ID)
    if user is not None:
        return user

    user = User(
        id=DEFAULT_USER_ID,
        email=DEFAULT_USER_EMAIL,
        full_name="Default Pharmacist",
        role="pharmacist",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_patient_or_404(patient_id: str, db: Session) -> Patient:
    patient = db.scalar(
        select(Patient)
        .options(selectinload(Patient.medications).selectinload(PatientMedication.drug))
        .where(Patient.id == patient_id)
    )
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def medication_to_response(medication: PatientMedication) -> MedicationResponse:
    return MedicationResponse(
        id=medication.id,
        rxcui=medication.rxcui,
        preferred_name=medication.drug.preferred_name,
        raw_input=medication.raw_input,
        normalization_status=medication.normalization_status,
        is_placeholder=medication.drug.is_placeholder,
        dose=medication.dose,
        route=medication.route,
        frequency=medication.frequency,
        is_active=medication.is_active,
        added_at=medication.added_at,
    )


async def create_patient_medication(
    patient: Patient,
    payload: MedicationAdd,
    db: Session,
    user_id: str | None = None,
) -> MedicationCreateResponse | MedicationCandidateResponse:
    normalization = await normalize_drug_name(payload.raw_input, db)
    if normalization.candidates:
        return MedicationCandidateResponse(
            message="Drug could not be auto-resolved. Please confirm one of the candidates.",
            normalization_status=normalization.normalization_status,
            candidates=normalization.candidates,
        )

    drug = db.get(Drug, normalization.rxcui)
    if drug is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Normalized drug could not be loaded")

    medication = PatientMedication(
        patient_id=patient.id,
        rxcui=drug.rxcui,
        raw_input=payload.raw_input,
        normalization_status=normalization.normalization_status,
        dose=payload.dose,
        route=payload.route,
        frequency=payload.frequency,
        notes=payload.notes,
        added_by=user_id,
    )
    db.add(medication)
    db.commit()
    medication = db.scalar(
        select(PatientMedication)
        .options(selectinload(PatientMedication.drug))
        .where(PatientMedication.id == medication.id)
    )

    warning = None
    if normalization.is_placeholder:
        warning = "Medication could not be matched to RxNorm and was stored as a placeholder."

    return MedicationCreateResponse(
        medication=medication_to_response(medication),
        normalization=normalization,
        warning=warning,
    )


@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)) -> PatientResponse:
    patient = Patient(
        date_of_birth=payload.date_of_birth,
        sex_at_birth=payload.sex_at_birth,
        weight_kg=Decimal(str(payload.weight_kg)) if payload.weight_kg is not None else None,
        is_synthetic=True,
    )
    db.add(patient)
    db.flush()

    if payload.given_name or payload.family_name:
        db.add(
            PatientIdentifier(
                patient_id=patient.id,
                given_name=payload.given_name,
                family_name=payload.family_name,
            )
        )

    db.commit()
    db.refresh(patient)
    return PatientResponse(
        id=patient.id,
        date_of_birth=patient.date_of_birth,
        sex_at_birth=patient.sex_at_birth,
        weight_kg=float(patient.weight_kg) if patient.weight_kg is not None else None,
        is_synthetic=patient.is_synthetic,
        created_at=patient.created_at,
        medications=[],
    )


@router.get("/patients", response_model=list[PatientListResponse])
def list_patients(db: Session = Depends(get_db)) -> list[PatientListResponse]:
    rows = db.execute(
        select(
            Patient.id,
            Patient.created_at,
            Patient.is_synthetic,
            func.count(PatientMedication.id).label("medication_count"),
            func.max(InteractionCheckRun.run_at).label("most_recent_check_run_at"),
        )
        .outerjoin(
            PatientMedication,
            (PatientMedication.patient_id == Patient.id) & (PatientMedication.is_active.is_(True)),
        )
        .outerjoin(InteractionCheckRun, InteractionCheckRun.patient_id == Patient.id)
        .group_by(Patient.id, Patient.created_at, Patient.is_synthetic)
        .order_by(func.max(InteractionCheckRun.run_at).desc(), Patient.created_at.desc())
    ).all()

    return [
        PatientListResponse(
            id=patient_id,
            created_at=created_at,
            is_synthetic=is_synthetic,
            medication_count=medication_count,
            most_recent_check_run_at=most_recent_check_run_at,
        )
        for patient_id, created_at, is_synthetic, medication_count, most_recent_check_run_at in rows
    ]


@router.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)) -> PatientResponse:
    patient = get_patient_or_404(patient_id, db)
    medications = [medication_to_response(medication) for medication in patient.medications]
    return PatientResponse(
        id=patient.id,
        date_of_birth=patient.date_of_birth,
        sex_at_birth=patient.sex_at_birth,
        weight_kg=float(patient.weight_kg) if patient.weight_kg is not None else None,
        is_synthetic=patient.is_synthetic,
        created_at=patient.created_at,
        medications=medications,
    )


@router.post(
    "/patients/{patient_id}/medications",
    response_model=MedicationCreateResponse,
    responses={202: {"model": MedicationCandidateResponse}},
)
async def add_medication(
    patient_id: str,
    payload: MedicationAdd,
    db: Session = Depends(get_db),
):
    patient = get_patient_or_404(patient_id, db)
    default_user = ensure_default_user(db)
    result = await create_patient_medication(patient, payload, db, user_id=default_user.id)
    if isinstance(result, MedicationCandidateResponse):
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=jsonable_encoder(result))
    return result


@router.delete("/patients/{patient_id}/medications/{med_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_medication(patient_id: str, med_id: str, db: Session = Depends(get_db)) -> Response:
    get_patient_or_404(patient_id, db)
    medication = db.scalar(
        select(PatientMedication).where(
            PatientMedication.id == med_id,
            PatientMedication.patient_id == patient_id,
        )
    )
    if medication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    medication.is_active = False
    medication.ended_on = medication.ended_on or datetime.utcnow().date()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/patients/{patient_id}/check", response_model=InteractionCheckResult)
async def run_patient_check(
    patient_id: str,
    payload: Optional[CheckRunRequest] = None,
    db: Session = Depends(get_db),
) -> InteractionCheckResult:
    get_patient_or_404(patient_id, db)
    default_user = ensure_default_user(db)
    user_id = payload.user_id if payload and payload.user_id else default_user.id
    return await run_interaction_check(patient_id, user_id, db)


@router.get("/patients/{patient_id}/checks", response_model=list[CheckRunHistoryResponse])
def list_patient_checks(patient_id: str, db: Session = Depends(get_db)) -> list[CheckRunHistoryResponse]:
    get_patient_or_404(patient_id, db)
    runs = db.execute(
        select(
            InteractionCheckRun.id,
            InteractionCheckRun.patient_id,
            InteractionCheckRun.run_by,
            InteractionCheckRun.run_at,
            InteractionCheckRun.duration_ms,
            func.count(InteractionCheckFinding.id).label("findings_count"),
        )
        .outerjoin(InteractionCheckFinding, InteractionCheckFinding.run_id == InteractionCheckRun.id)
        .where(InteractionCheckRun.patient_id == patient_id)
        .group_by(
            InteractionCheckRun.id,
            InteractionCheckRun.patient_id,
            InteractionCheckRun.run_by,
            InteractionCheckRun.run_at,
            InteractionCheckRun.duration_ms,
        )
        .order_by(desc(InteractionCheckRun.run_at))
    ).all()

    return [
        CheckRunHistoryResponse(
            run_id=run_id,
            patient_id=run_patient_id,
            run_by=run_by,
            run_at=run_at,
            duration_ms=duration_ms,
            findings_count=findings_count,
        )
        for run_id, run_patient_id, run_by, run_at, duration_ms, findings_count in runs
    ]


@router.post("/dev/seed", response_model=InteractionCheckResult)
async def seed_demo_patient(db: Session = Depends(get_db)) -> InteractionCheckResult:
    default_user = ensure_default_user(db)
    patient = Patient(is_synthetic=True)
    db.add(patient)
    db.commit()
    db.refresh(patient)

    seed_medications = [
        "warfarin",
        "aspirin",
        "amiodarone",
        "fluoxetine",
        "simvastatin",
        "clarithromycin",
    ]
    for drug_name in seed_medications:
        result = await create_patient_medication(patient, MedicationAdd(raw_input=drug_name), db, user_id=default_user.id)
        if isinstance(result, MedicationCandidateResponse):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Seed medication {drug_name} could not be auto-resolved",
            )

    return await run_interaction_check(patient.id, default_user.id, db)
