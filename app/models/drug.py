from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Drug(Base):
    __tablename__ = "drugs"

    rxcui: Mapped[str] = mapped_column(String, primary_key=True)
    preferred_name: Mapped[str] = mapped_column(String, nullable=False)
    tty: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_placeholder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rxnorm_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    aliases = relationship("DrugAlias", back_populates="drug", cascade="all, delete-orphan")
    external_ids = relationship("DrugExternalId", back_populates="drug", cascade="all, delete-orphan")
    unresolved_entries = relationship("UnresolvedDrugEntry", back_populates="resolved_drug")
    patient_medications = relationship("PatientMedication", back_populates="drug")

    __table_args__ = (
        Index("drugs_preferred_name_idx", "preferred_name"),
    )


class DrugAlias(Base):
    __tablename__ = "drug_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rxcui: Mapped[str] = mapped_column(ForeignKey("drugs.rxcui", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String, nullable=False)
    alias_kind: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="RxNorm")

    drug = relationship("Drug", back_populates="aliases")

    __table_args__ = (
        CheckConstraint(
            "alias_kind IN ('brand','synonym','misspelling','foreign','tradename','obsolete')",
            name="ck_drug_aliases_alias_kind",
        ),
        UniqueConstraint("alias", "alias_kind", "rxcui", name="uq_drug_aliases_alias_kind_rxcui"),
        Index("drug_aliases_alias_idx", "alias"),
        Index("drug_aliases_rxcui_idx", "rxcui"),
    )


class DrugExternalId(Base):
    __tablename__ = "drug_external_ids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rxcui: Mapped[str] = mapped_column(ForeignKey("drugs.rxcui", ondelete="CASCADE"), nullable=False)
    system: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[str] = mapped_column(String, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    drug = relationship("Drug", back_populates="external_ids")

    __table_args__ = (
        CheckConstraint(
            "system IN ('NDC','DrugBank','DDInter','UNII','ATC','SPL_SET_ID','SPL_ID')",
            name="ck_drug_external_ids_system",
        ),
        UniqueConstraint("system", "external_id", "rxcui", name="uq_drug_external_ids_system_external_id_rxcui"),
        Index("drug_external_ids_lookup_idx", "system", "external_id"),
        Index("drug_external_ids_rxcui_idx", "rxcui"),
    )


class UnresolvedDrugEntry(Base):
    __tablename__ = "unresolved_drug_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_input: Mapped[str] = mapped_column(String, nullable=False)
    normalized_input: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_to_rxcui: Mapped[Optional[str]] = mapped_column(ForeignKey("drugs.rxcui"), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    resolved_drug = relationship("Drug", back_populates="unresolved_entries")
