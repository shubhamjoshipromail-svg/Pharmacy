from __future__ import annotations

from typing import Optional

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.drug import Drug, DrugExternalId
from app.models.interaction import Interaction

OPENFDA_BASE_URL = "https://api.fda.gov/drug/label.json"
DAILYMED_LABEL_URL = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={spl_set_id}"
_OPENFDA_CACHE: dict[str, Optional[dict]] = {}


def _coalesce_text(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        return "\n\n".join(str(item).strip() for item in value if str(item).strip()) or None
    if isinstance(value, str):
        return value.strip() or None
    return str(value).strip() or None


def _build_label_payload(result: dict) -> Optional[dict]:
    openfda = result.get("openfda", {}) or {}
    spl_set_ids = openfda.get("spl_set_id", []) or []
    spl_set_id = spl_set_ids[0] if spl_set_ids else result.get("set_id")

    drug_interactions_text = _coalesce_text(result.get("drug_interactions"))
    warnings_text = _coalesce_text(result.get("warnings")) or _coalesce_text(result.get("warnings_and_precautions"))
    boxed_warning_text = _coalesce_text(result.get("boxed_warning"))
    contraindications_text = _coalesce_text(result.get("contraindications"))

    if not any([spl_set_id, drug_interactions_text, warnings_text, boxed_warning_text, contraindications_text]):
        return None

    return {
        "spl_set_id": spl_set_id,
        "drug_interactions_text": drug_interactions_text,
        "warnings_text": warnings_text,
        "boxed_warning_text": boxed_warning_text,
        "contraindications_text": contraindications_text,
        "label_url": DAILYMED_LABEL_URL.format(spl_set_id=spl_set_id) if spl_set_id else None,
    }


async def _fetch_label_by_query(search: str) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            OPENFDA_BASE_URL,
            params={"search": search, "limit": 1},
            timeout=20.0,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        results = response.json().get("results", []) or []
        if not results:
            return None
        return _build_label_payload(results[0])


def _persist_spl_set_id(rxcui: str, spl_set_id: str, db: Session) -> None:
    existing = db.scalar(
        select(DrugExternalId).where(
            DrugExternalId.rxcui == rxcui,
            DrugExternalId.system == "SPL_SET_ID",
            DrugExternalId.external_id == spl_set_id,
        )
    )
    if existing is not None:
        return

    db.add(
        DrugExternalId(
            rxcui=rxcui,
            system="SPL_SET_ID",
            external_id=spl_set_id,
            is_primary=True,
        )
    )
    db.flush()


async def fetch_label_for_drug(rxcui: str, db: Session) -> Optional[dict]:
    if rxcui in _OPENFDA_CACHE:
        return _OPENFDA_CACHE[rxcui]

    label = None
    spl_set_id_row = db.scalar(
        select(DrugExternalId).where(
            DrugExternalId.rxcui == rxcui,
            DrugExternalId.system == "SPL_SET_ID",
        )
    )
    if spl_set_id_row is not None:
        label = await _fetch_label_by_query(f'openfda.spl_set_id:"{spl_set_id_row.external_id}"')

    if label is None:
        drug = db.get(Drug, rxcui)
        if drug is None:
            _OPENFDA_CACHE[rxcui] = None
            return None

        label = await _fetch_label_by_query(f'openfda.rxcui:"{rxcui}"')
        if label is None:
            preferred_name = drug.preferred_name.strip()
            label = await _fetch_label_by_query(f'openfda.generic_name:"{preferred_name}"')

    if label and label.get("spl_set_id"):
        _persist_spl_set_id(rxcui, label["spl_set_id"], db)

    _OPENFDA_CACHE[rxcui] = label
    return label


async def fetch_citations_for_interaction(
    interaction_id: str,
    db: Session,
) -> dict:
    interaction = db.get(Interaction, interaction_id)
    if interaction is None:
        return {
            "drug_a_label": None,
            "drug_b_label": None,
            "interaction_mentioned_in_a": False,
            "interaction_mentioned_in_b": False,
        }

    drug_a = db.get(Drug, interaction.drug_a_rxcui)
    drug_b = db.get(Drug, interaction.drug_b_rxcui) if interaction.drug_b_rxcui else None

    drug_a_label = await fetch_label_for_drug(interaction.drug_a_rxcui, db)
    drug_b_label = await fetch_label_for_drug(interaction.drug_b_rxcui, db) if interaction.drug_b_rxcui else None

    drug_b_name = drug_b.preferred_name.lower() if drug_b else ""
    drug_a_name = drug_a.preferred_name.lower() if drug_a else ""
    interaction_mentioned_in_a = bool(
        drug_b_name
        and drug_a_label
        and drug_a_label.get("drug_interactions_text")
        and drug_b_name in drug_a_label["drug_interactions_text"].lower()
    )
    interaction_mentioned_in_b = bool(
        drug_a_name
        and drug_b_label
        and drug_b_label.get("drug_interactions_text")
        and drug_a_name in drug_b_label["drug_interactions_text"].lower()
    )

    return {
        "drug_a_label": drug_a_label,
        "drug_b_label": drug_b_label,
        "interaction_mentioned_in_a": interaction_mentioned_in_a,
        "interaction_mentioned_in_b": interaction_mentioned_in_b,
    }
