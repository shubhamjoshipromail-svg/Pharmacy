from __future__ import annotations

import asyncio
import hashlib
import re
import time
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.drug import Drug, DrugAlias, UnresolvedDrugEntry
from app.models.enums import NormalizationStatus

RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST/"
RXNORM_DELAY_SECONDS = 0.1
BRAND_ALIAS_KINDS = {"brand", "tradename"}
BRAND_TTYS = {"BN", "BPCK", "GPCK", "SBD", "SBDC", "SBDG"}
_last_rxnorm_call = 0.0


class NormalizationResult(BaseModel):
    rxcui: Optional[str]
    preferred_name: Optional[str]
    normalization_status: NormalizationStatus
    confidence_score: Optional[float]
    candidates: Optional[list[dict[str, Any]]]
    is_placeholder: bool = False


def _normalize_text(raw_input: str) -> str:
    return re.sub(r"\s+", " ", raw_input.strip()).lower()


def _looks_like_ndc(raw_input: str) -> bool:
    digits = re.sub(r"\D", "", raw_input)
    return len(digits) in {10, 11}


def _clean_ndc(raw_input: str) -> str:
    return re.sub(r"\D", "", raw_input)


def _placeholder_rxcui(normalized_input: str) -> str:
    digest = hashlib.sha1(normalized_input.encode("utf-8")).hexdigest()[:24]
    return f"placeholder:{digest}"


async def _rate_limited_get_json(client: httpx.AsyncClient, path: str, params: dict[str, Any]) -> dict[str, Any]:
    global _last_rxnorm_call

    elapsed = time.monotonic() - _last_rxnorm_call
    if elapsed < RXNORM_DELAY_SECONDS:
        await asyncio.sleep(RXNORM_DELAY_SECONDS - elapsed)

    response = await client.get(urljoin(RXNORM_BASE_URL, path), params=params, timeout=20.0)
    response.raise_for_status()
    _last_rxnorm_call = time.monotonic()
    return response.json()


async def _get_concept_properties(client: httpx.AsyncClient, rxcui: str) -> dict[str, Any]:
    payload = await _rate_limited_get_json(client, f"rxcui/{rxcui}/properties.json", {})
    return payload.get("properties", {}) or {}


async def _resolve_ingredient_concept(client: httpx.AsyncClient, rxcui: str) -> tuple[str, str, str]:
    payload = await _rate_limited_get_json(client, f"rxcui/{rxcui}/related.json", {"tty": "IN"})
    concept_groups = payload.get("relatedGroup", {}).get("conceptGroup", []) or []

    for group in concept_groups:
        for concept in group.get("conceptProperties", []) or []:
            concept_rxcui = concept.get("rxcui")
            if concept_rxcui:
                return concept_rxcui, concept.get("name", concept_rxcui), concept.get("tty", "IN")

    properties = await _get_concept_properties(client, rxcui)
    return rxcui, properties.get("name", rxcui), properties.get("tty", "UNKNOWN")


async def _search_exact(client: httpx.AsyncClient, name: str) -> list[str]:
    payload = await _rate_limited_get_json(client, "rxcui.json", {"name": name, "search": 2})
    return payload.get("idGroup", {}).get("rxnormId", []) or []


async def _search_fuzzy(client: httpx.AsyncClient, name: str) -> list[dict[str, Any]]:
    payload = await _rate_limited_get_json(client, "approximateTerm.json", {"term": name, "maxEntries": 5})
    candidates = payload.get("approximateGroup", {}).get("candidate", []) or []
    normalized_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        if not candidate.get("rxcui"):
            continue
        normalized_candidates.append(
            {
                "rxcui": candidate["rxcui"],
                "score": float(candidate.get("score", 0)),
                "rank": int(candidate.get("rank", 9999)),
            }
        )
    return normalized_candidates


async def _search_ndc(client: httpx.AsyncClient, ndc: str) -> list[str]:
    payload = await _rate_limited_get_json(client, "rxcui.json", {"idtype": "NDC", "id": ndc})
    return payload.get("idGroup", {}).get("rxnormId", []) or []


def get_or_create_drug(rxcui: str, preferred_name: str, tty: str, db: Session) -> Drug:
    drug = db.get(Drug, rxcui)
    if drug is not None:
        if drug.is_placeholder:
            drug.is_placeholder = False
        if preferred_name and drug.preferred_name != preferred_name:
            drug.preferred_name = preferred_name
        if tty and drug.tty != tty:
            drug.tty = tty
        drug.is_active = True
        drug.rxnorm_synced_at = datetime.utcnow()
        db.flush()
        return drug

    drug = Drug(
        rxcui=rxcui,
        preferred_name=preferred_name,
        tty=tty,
        is_active=True,
        is_placeholder=False,
        rxnorm_synced_at=datetime.utcnow(),
    )
    db.add(drug)
    db.flush()
    return drug


def add_alias(rxcui: str, alias: str, alias_kind: str, db: Session) -> None:
    normalized_alias = _normalize_text(alias)
    existing = db.scalar(
        select(DrugAlias).where(func.lower(DrugAlias.alias) == normalized_alias).where(DrugAlias.alias_kind == alias_kind).where(DrugAlias.rxcui == rxcui)
    )
    if existing is not None:
        return

    db.add(
        DrugAlias(
            rxcui=rxcui,
            alias=alias.strip(),
            alias_kind=alias_kind,
            source="RxNorm",
        )
    )
    db.flush()


def _record_unresolved(raw_input: str, normalized_input: str, db: Session) -> Drug:
    unresolved = db.scalar(
        select(UnresolvedDrugEntry).where(UnresolvedDrugEntry.normalized_input == normalized_input)
    )
    if unresolved is None:
        unresolved = UnresolvedDrugEntry(
            raw_input=raw_input,
            normalized_input=normalized_input,
            occurrences=1,
            last_seen_at=datetime.utcnow(),
        )
        db.add(unresolved)
    else:
        unresolved.raw_input = raw_input
        unresolved.occurrences += 1
        unresolved.last_seen_at = datetime.utcnow()

    placeholder_rxcui = _placeholder_rxcui(normalized_input)
    placeholder = db.get(Drug, placeholder_rxcui)
    if placeholder is None:
        placeholder = Drug(
            rxcui=placeholder_rxcui,
            preferred_name=raw_input.strip() or normalized_input,
            tty="PLACEHOLDER",
            is_active=True,
            is_placeholder=True,
        )
        db.add(placeholder)
    else:
        placeholder.preferred_name = raw_input.strip() or normalized_input
        placeholder.is_placeholder = True
        placeholder.is_active = True

    db.flush()
    return placeholder


async def normalize_drug_name(raw_input: str, db: Session) -> NormalizationResult:
    cleaned = raw_input.strip()
    normalized = _normalize_text(cleaned)
    if not cleaned:
        placeholder = _record_unresolved(raw_input, normalized, db)
        db.commit()
        return NormalizationResult(
            rxcui=placeholder.rxcui,
            preferred_name=placeholder.preferred_name,
            normalization_status=NormalizationStatus.unmatched,
            confidence_score=0.0,
            candidates=None,
            is_placeholder=True,
        )

    alias_hit = db.scalar(select(DrugAlias).where(func.lower(DrugAlias.alias) == normalized))
    if alias_hit is not None:
        drug = db.get(Drug, alias_hit.rxcui)
        status = NormalizationStatus.matched_brand if alias_hit.alias_kind in BRAND_ALIAS_KINDS else NormalizationStatus.matched_exact
        return NormalizationResult(
            rxcui=drug.rxcui if drug else alias_hit.rxcui,
            preferred_name=drug.preferred_name if drug else cleaned,
            normalization_status=status,
            confidence_score=100.0,
            candidates=None,
            is_placeholder=drug.is_placeholder if drug else False,
        )

    async with httpx.AsyncClient() as client:
        exact_hits = await _search_exact(client, cleaned)
        if exact_hits:
            source_rxcui = exact_hits[0]
            properties = await _get_concept_properties(client, source_rxcui)
            ingredient_rxcui, ingredient_name, ingredient_tty = await _resolve_ingredient_concept(client, source_rxcui)
            get_or_create_drug(ingredient_rxcui, ingredient_name, ingredient_tty, db)
            alias_kind = "brand" if properties.get("tty") in BRAND_TTYS else "synonym"
            add_alias(ingredient_rxcui, cleaned, alias_kind, db)
            db.commit()
            return NormalizationResult(
                rxcui=ingredient_rxcui,
                preferred_name=ingredient_name,
                normalization_status=NormalizationStatus.matched_brand if alias_kind == "brand" else NormalizationStatus.matched_exact,
                confidence_score=100.0,
                candidates=None,
                is_placeholder=False,
            )

        fuzzy_hits = await _search_fuzzy(client, cleaned)
        if fuzzy_hits:
            resolved_candidates: list[dict[str, Any]] = []
            for candidate in fuzzy_hits:
                ingredient_rxcui, ingredient_name, ingredient_tty = await _resolve_ingredient_concept(client, candidate["rxcui"])
                resolved_candidates.append(
                    {
                        "rxcui": ingredient_rxcui,
                        "preferred_name": ingredient_name,
                        "tty": ingredient_tty,
                        "score": candidate["score"],
                        "rank": candidate["rank"],
                    }
                )

            resolved_candidates.sort(key=lambda item: (-item["score"], item["rank"], item["preferred_name"]))
            top_candidate = resolved_candidates[0]
            if top_candidate["score"] > 8:
                get_or_create_drug(top_candidate["rxcui"], top_candidate["preferred_name"], top_candidate["tty"], db)
                add_alias(top_candidate["rxcui"], cleaned, "misspelling", db)
                db.commit()
                return NormalizationResult(
                    rxcui=top_candidate["rxcui"],
                    preferred_name=top_candidate["preferred_name"],
                    normalization_status=NormalizationStatus.matched_fuzzy,
                    confidence_score=top_candidate["score"],
                    candidates=None,
                    is_placeholder=False,
                )

            if 4 <= top_candidate["score"] <= 8:
                return NormalizationResult(
                    rxcui=None,
                    preferred_name=None,
                    normalization_status=NormalizationStatus.matched_fuzzy,
                    confidence_score=top_candidate["score"],
                    candidates=resolved_candidates,
                    is_placeholder=False,
                )

        if _looks_like_ndc(cleaned):
            ndc = _clean_ndc(cleaned)
            ndc_hits = await _search_ndc(client, ndc)
            if ndc_hits:
                ingredient_rxcui, ingredient_name, ingredient_tty = await _resolve_ingredient_concept(client, ndc_hits[0])
                get_or_create_drug(ingredient_rxcui, ingredient_name, ingredient_tty, db)
                add_alias(ingredient_rxcui, cleaned, "synonym", db)
                db.commit()
                return NormalizationResult(
                    rxcui=ingredient_rxcui,
                    preferred_name=ingredient_name,
                    normalization_status=NormalizationStatus.matched_ndc,
                    confidence_score=100.0,
                    candidates=None,
                    is_placeholder=False,
                )

    placeholder = _record_unresolved(raw_input, normalized, db)
    db.commit()
    return NormalizationResult(
        rxcui=placeholder.rxcui,
        preferred_name=placeholder.preferred_name,
        normalization_status=NormalizationStatus.unmatched,
        confidence_score=0.0,
        candidates=None,
        is_placeholder=True,
    )


async def batch_normalize(drug_names: list[str], db: Session) -> list[NormalizationResult]:
    results: list[NormalizationResult] = []
    for name in drug_names:
        results.append(await normalize_drug_name(name, db))
        await asyncio.sleep(RXNORM_DELAY_SECONDS)
    return results
