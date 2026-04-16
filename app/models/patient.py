from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import NormalizationStatus, sql_enum


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    license_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False, default="pharmacist")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('pharmacist','admin','readonly')", name="ck_users_role"),
    )


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sex_at_birth: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    identifiers = relationship("PatientIdentifier", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    conditions = relationship("PatientCondition", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("PatientMedication", back_populates="patient", cascade="all, delete-orphan")
    check_runs = relationship("InteractionCheckRun", back_populates="patient")
    acknowledgments = relationship("InteractionAcknowledgment", back_populates="patient")

    __table_args__ = (
        CheckConstraint("sex_at_birth IN ('M','F','I','U')", name="ck_patients_sex_at_birth"),
    )


class PatientIdentifier(Base):
    __tablename__ = "patient_identifiers"

    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        primary_key=True,
    )
    given_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    family_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mrn: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    external_patient_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="identifiers")


class PatientCondition(Base):
    __tablename__ = "patient_conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    condition_id: Mapped[int] = mapped_column(ForeignKey("conditions.id"), nullable=False)
    onset_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resolved_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    patient = relationship("Patient", back_populates="conditions")

    __table_args__ = (
        UniqueConstraint("patient_id", "condition_id", "onset_date", name="uq_patient_conditions_patient_condition_onset"),
        Index("patient_conditions_patient_idx", "patient_id"),
    )


class PatientMedication(Base):
    __tablename__ = "patient_medications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    rxcui: Mapped[str] = mapped_column(ForeignKey("drugs.rxcui"), nullable=False)
    raw_input: Mapped[str] = mapped_column(String, nullable=False)
    normalization_status: Mapped[NormalizationStatus] = mapped_column(
        sql_enum(NormalizationStatus, "normalization_status"),
        nullable=False,
    )
    dose: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dose_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    dose_unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    route: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    started_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ended_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    added_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    patient = relationship("Patient", back_populates="medications")
    drug = relationship("Drug", back_populates="patient_medications")

    __table_args__ = (
        Index("pm_patient_active_idx", "patient_id", "is_active"),
        Index("pm_rxcui_idx", "rxcui"),
    )
