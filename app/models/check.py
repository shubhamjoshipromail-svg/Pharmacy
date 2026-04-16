from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import SeverityLevel, sql_enum


class InteractionCheckRun(Base):
    __tablename__ = "interaction_check_runs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("patients.id"), nullable=False)
    run_by: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    run_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    medications_snapshot: Mapped[Any] = mapped_column(JSONB, nullable=False)
    sources_used: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    patient = relationship("Patient", back_populates="check_runs")
    findings = relationship("InteractionCheckFinding", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("icr_patient_time_idx", "patient_id", "run_at"),
        Index("icr_run_by_idx", "run_by", "run_at"),
    )


class InteractionCheckFinding(Base):
    __tablename__ = "interaction_check_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("interaction_check_runs.id", ondelete="CASCADE"), nullable=False)
    interaction_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("interactions.id"), nullable=False)
    max_severity_at_run: Mapped[SeverityLevel] = mapped_column(
        sql_enum(SeverityLevel, "finding_severity_level"),
        nullable=False,
    )
    sources_at_run: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    sources_conflicted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    llm_explanation_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("llm_explanations.id"), nullable=True)
    suppressed_by_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    run = relationship("InteractionCheckRun", back_populates="findings")
    interaction = relationship("Interaction", back_populates="findings")
    llm_explanation = relationship("LlmExplanation", back_populates="findings")
    overrides = relationship("InteractionOverride", back_populates="finding", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("run_id", "interaction_id", name="uq_icf_run_interaction"),
        Index("icf_interaction_idx", "interaction_id"),
    )


class LlmExplanation(Base):
    __tablename__ = "llm_explanations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    interaction_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("interactions.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    prompt_template_version: Mapped[str] = mapped_column(String, nullable=False)
    structured_input: Mapped[Any] = mapped_column(JSONB, nullable=False)
    explanation_text: Mapped[str] = mapped_column(String, nullable=False)
    schema_validation_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    validation_errors: Mapped[Any] = mapped_column(JSONB, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[Any] = mapped_column(JSONB, nullable=True)

    interaction = relationship("Interaction", back_populates="llm_explanations")
    findings = relationship("InteractionCheckFinding", back_populates="llm_explanation")

    __table_args__ = (
        Index("llm_exp_interaction_idx", "interaction_id", "generated_at"),
    )
