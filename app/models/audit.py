from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import OverrideAction, SeverityLevel, sql_enum


class InteractionAcknowledgment(Base):
    __tablename__ = "interaction_acknowledgments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    interaction_id: Mapped[str] = mapped_column(ForeignKey("interactions.id"), nullable=False)
    acknowledged_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    severity_at_ack: Mapped[SeverityLevel] = mapped_column(
        sql_enum(SeverityLevel, "ack_severity_level"),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    patient = relationship("Patient", back_populates="acknowledgments")
    interaction = relationship("Interaction", back_populates="acknowledgments")

    __table_args__ = (
        UniqueConstraint("patient_id", "interaction_id", "acknowledged_at", name="uq_ack_patient_interaction_time"),
        Index("ia_patient_idx", "patient_id", "interaction_id", "is_active"),
    )


class InteractionOverride(Base):
    __tablename__ = "interaction_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("interaction_check_findings.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[OverrideAction] = mapped_column(
        sql_enum(OverrideAction, "override_action"),
        nullable=False,
    )
    severity_overridden: Mapped[SeverityLevel] = mapped_column(
        sql_enum(SeverityLevel, "override_severity_level"),
        nullable=False,
    )
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    finding = relationship("InteractionCheckFinding", back_populates="overrides")

    __table_args__ = (
        Index("io_finding_idx", "finding_id"),
        Index("io_user_time_idx", "user_id", "occurred_at"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    payload: Mapped[Any] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index("audit_events_user_time_idx", "user_id", "occurred_at"),
        Index("audit_events_target_idx", "target_type", "target_id"),
    )
