from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import InteractionSource, InteractionType, SeverityLevel, sql_enum


class Food(Base):
    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    fdc_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Condition(Base):
    __tablename__ = "conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    icd10_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    snomed_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    interaction_type: Mapped[InteractionType] = mapped_column(
        sql_enum(InteractionType, "interaction_type"),
        nullable=False,
    )
    drug_a_rxcui: Mapped[str] = mapped_column(ForeignKey("drugs.rxcui"), nullable=False)
    drug_b_rxcui: Mapped[Optional[str]] = mapped_column(ForeignKey("drugs.rxcui"), nullable=True)
    food_id: Mapped[Optional[int]] = mapped_column(ForeignKey("foods.id"), nullable=True)
    condition_id: Mapped[Optional[int]] = mapped_column(ForeignKey("conditions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    drug_a = relationship("Drug", foreign_keys=[drug_a_rxcui])
    drug_b = relationship("Drug", foreign_keys=[drug_b_rxcui])
    food = relationship("Food")
    condition = relationship("Condition")
    assertions = relationship(
        "InteractionSourceAssertion",
        back_populates="interaction",
        cascade="all, delete-orphan",
    )
    findings = relationship("InteractionCheckFinding", back_populates="interaction")
    acknowledgments = relationship("InteractionAcknowledgment", back_populates="interaction")
    llm_explanations = relationship("LlmExplanation", back_populates="interaction")

    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN drug_b_rxcui IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN food_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN condition_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="interactions_party_b_exactly_one",
        ),
        CheckConstraint(
            "(interaction_type IN ('DDI','therapeutic_duplication') AND drug_b_rxcui IS NOT NULL) "
            "OR (interaction_type = 'DFI' AND food_id IS NOT NULL) "
            "OR (interaction_type = 'DDSI' AND condition_id IS NOT NULL)",
            name="interactions_type_matches_party_b",
        ),
        CheckConstraint(
            "drug_b_rxcui IS NULL OR drug_a_rxcui < drug_b_rxcui",
            name="interactions_ddi_ordered",
        ),
        Index("interactions_unique_ddi_idx", "interaction_type", "drug_a_rxcui", "drug_b_rxcui", unique=True),
        Index("interactions_unique_dfi_idx", "interaction_type", "drug_a_rxcui", "food_id", unique=True),
        Index("interactions_unique_ddsi_idx", "interaction_type", "drug_a_rxcui", "condition_id", unique=True),
        Index("interactions_drug_a_idx", "drug_a_rxcui"),
        Index("interactions_drug_b_idx", "drug_b_rxcui"),
        Index("interactions_food_idx", "food_id"),
        Index("interactions_condition_idx", "condition_id"),
    )


class InteractionSourceAssertion(Base):
    __tablename__ = "interaction_source_assertions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[str] = mapped_column(
        ForeignKey("interactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[InteractionSource] = mapped_column(
        sql_enum(InteractionSource, "interaction_source"),
        nullable=False,
    )
    source_severity_raw: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    severity: Mapped[SeverityLevel] = mapped_column(
        sql_enum(SeverityLevel, "severity_level"),
        nullable=False,
    )
    mechanism: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    management: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    onset: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    documentation_quality: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_record_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    raw_payload: Mapped[Any] = mapped_column(JSONB, nullable=True)

    interaction = relationship("Interaction", back_populates="assertions")

    __table_args__ = (
        UniqueConstraint("interaction_id", "source", "source_record_id", name="uq_isa_interaction_source_record"),
        Index("isa_interaction_idx", "interaction_id"),
        Index("isa_severity_idx", "severity"),
    )


class SourceCoverageCheck(Base):
    __tablename__ = "source_coverage_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    drug_a_rxcui: Mapped[str] = mapped_column(ForeignKey("drugs.rxcui"), nullable=False)
    drug_b_rxcui: Mapped[Optional[str]] = mapped_column(ForeignKey("drugs.rxcui"), nullable=True)
    food_id: Mapped[Optional[int]] = mapped_column(ForeignKey("foods.id"), nullable=True)
    condition_id: Mapped[Optional[int]] = mapped_column(ForeignKey("conditions.id"), nullable=True)
    source: Mapped[InteractionSource] = mapped_column(
        sql_enum(InteractionSource, "source_coverage_interaction_source"),
        nullable=False,
    )
    checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    found_interaction: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index("scc_lookup_idx", "drug_a_rxcui", "drug_b_rxcui", "food_id", "condition_id", "source"),
    )
