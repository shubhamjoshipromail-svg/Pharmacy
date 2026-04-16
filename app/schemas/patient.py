from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import NormalizationStatus
from app.services.normalization import NormalizationResult


class MedicationAdd(BaseModel):
    raw_input: str
    dose: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    notes: Optional[str] = None


class MedicationResponse(BaseModel):
    id: str
    rxcui: str
    preferred_name: str
    raw_input: str
    normalization_status: NormalizationStatus
    is_placeholder: bool
    dose: Optional[str]
    route: Optional[str]
    frequency: Optional[str]
    is_active: bool
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicationCreateResponse(BaseModel):
    medication: MedicationResponse
    normalization: NormalizationResult
    warning: Optional[str] = None


class MedicationCandidateResponse(BaseModel):
    message: str
    normalization_status: NormalizationStatus
    candidates: list[dict]


class PatientCreate(BaseModel):
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    sex_at_birth: Optional[str] = None
    weight_kg: Optional[float] = None

    @field_validator("sex_at_birth")
    @classmethod
    def validate_sex_at_birth(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in {"M", "F", "I", "U"}:
            raise ValueError("sex_at_birth must be one of M, F, I, U")
        return value


class PatientResponse(BaseModel):
    id: str
    date_of_birth: Optional[date]
    sex_at_birth: Optional[str]
    weight_kg: Optional[float]
    is_synthetic: bool
    created_at: datetime
    medications: list[MedicationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CheckRunRequest(BaseModel):
    user_id: Optional[str] = None


class CheckRunHistoryResponse(BaseModel):
    run_id: str
    patient_id: str
    run_by: str
    run_at: datetime
    duration_ms: Optional[int]
    findings_count: int


class PatientListResponse(BaseModel):
    id: str
    created_at: datetime
    is_synthetic: bool
    medication_count: int
    most_recent_check_run_at: Optional[datetime]
