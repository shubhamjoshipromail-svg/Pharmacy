#!/usr/bin/env python3
"""Verify frozen RxNorm references and benchmark the unchanged normalizer."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import make_url


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[5]
RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-output", type=Path, required=True)
    parser.add_argument("--api-log", type=Path, required=True)
    return parser.parse_args()


def validate_database_url() -> tuple[str, str, int]:
    from os import environ

    raw_url = environ.get("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("DATABASE_URL must be set explicitly.")
    url = make_url(raw_url)
    if not url.drivername.startswith("postgresql"):
        raise RuntimeError("Only PostgreSQL is allowed.")
    if url.host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Refusing non-loopback database host.")
    if url.database != "rxcheck_normalization":
        raise RuntimeError("Refusing a database outside the normalization naming convention.")
    if not url.port:
        raise RuntimeError("An explicit local database port is required.")
    return url.host, url.database or "", url.port


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=PROJECT_ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def rxnorm_ids(payload: dict[str, Any]) -> list[str]:
    return payload.get("idGroup", {}).get("rxnormId", []) or []


def related_ingredients(payload: dict[str, Any]) -> list[dict[str, str]]:
    ingredients: list[dict[str, str]] = []
    for group in payload.get("relatedGroup", {}).get("conceptGroup", []) or []:
        for concept in group.get("conceptProperties", []) or []:
            if concept.get("rxcui"):
                ingredients.append(
                    {
                        "rxcui": concept["rxcui"],
                        "name": concept.get("name", ""),
                        "tty": concept.get("tty", ""),
                    }
                )
    return ingredients


async def official_get(
    client: httpx.AsyncClient,
    path: str,
    params: dict[str, Any],
    *,
    phase: str,
    case_id: str | None,
    log: list[dict[str, Any]],
) -> dict[str, Any]:
    response = await client.get(path, params=params)
    response.raise_for_status()
    payload = response.json()
    log.append(
        {
            "phase": phase,
            "case_id": case_id,
            "fetched_at": datetime.now(UTC).isoformat(),
            "url": str(response.url),
            "status_code": response.status_code,
            "response": payload,
        }
    )
    return payload


async def verify_references(
    fixtures: dict[str, Any],
    api_log: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_release = fixtures["metadata"]["rxnorm_release"]
    expected_api_version = fixtures["metadata"]["rxnorm_api_version"]
    results: list[dict[str, Any]] = []

    async with httpx.AsyncClient(
        base_url=RXNORM_BASE_URL,
        timeout=20.0,
        headers={"User-Agent": "RxCheck-publication-normalization-audit/1.0"},
    ) as client:
        version_payload = await official_get(
            client,
            "version.json",
            {},
            phase="reference_verification",
            case_id=None,
            log=api_log,
        )
        version_passed = (
            version_payload.get("version") == expected_release
            and version_payload.get("apiVersion") == expected_api_version
        )

        for case in fixtures["cases"]:
            if case["reference_type"] == "synthetic_negative":
                results.append(
                    {
                        "case_id": case["id"],
                        "verified": True,
                        "method": "prespecified_constructed_negative",
                        "source_hits": [],
                        "observed_ingredient_rxcuis": [],
                        "expected_ingredient_rxcuis": case["expected_ingredient_rxcuis"],
                    }
                )
                continue

            if case["reference_type"] == "name":
                source_payload = await official_get(
                    client,
                    "rxcui.json",
                    {"name": case["reference_value"], "search": 2},
                    phase="reference_verification",
                    case_id=case["id"],
                    log=api_log,
                )
            elif case["reference_type"] == "ndc":
                source_payload = await official_get(
                    client,
                    "rxcui.json",
                    {"idtype": "NDC", "id": case["reference_value"]},
                    phase="reference_verification",
                    case_id=case["id"],
                    log=api_log,
                )
            else:
                raise RuntimeError(f"Unsupported reference type: {case['reference_type']}")

            source_hits = rxnorm_ids(source_payload)
            source_rxcui = case["reference_source_rxcui"]
            related_payload = await official_get(
                client,
                f"rxcui/{source_rxcui}/related.json",
                {"tty": "IN"},
                phase="reference_verification",
                case_id=case["id"],
                log=api_log,
            )
            ingredients = related_ingredients(related_payload)
            observed_ingredients = sorted({item["rxcui"] for item in ingredients})
            expected_ingredients = sorted(case["expected_ingredient_rxcuis"])
            verified = source_rxcui in source_hits and observed_ingredients == expected_ingredients
            results.append(
                {
                    "case_id": case["id"],
                    "verified": verified,
                    "method": f"official_rxnorm_{case['reference_type']}_plus_related_IN",
                    "reference_value": case["reference_value"],
                    "source_hits": source_hits,
                    "expected_source_rxcui": source_rxcui,
                    "observed_ingredients": ingredients,
                    "observed_ingredient_rxcuis": observed_ingredients,
                    "expected_ingredient_rxcuis": expected_ingredients,
                    "independent_label_url": case.get("independent_label_url"),
                }
            )
            await asyncio.sleep(0.05)

    verified_count = sum(item["verified"] for item in results)
    return {
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "expected_release": expected_release,
            "expected_api_version": expected_api_version,
            "observed_version_payload": version_payload,
            "version_passed": version_passed,
            "independence_note": (
                "Frozen expected outcomes were checked through separate official-endpoint logic "
                "before application execution; most mappings still share the RxNorm vocabulary/service."
            ),
        },
        "summary": {
            "cases": len(results),
            "verified": verified_count,
            "failed": len(results) - verified_count,
            "all_references_verified": version_passed and verified_count == len(results),
        },
        "cases": results,
    }


def evaluate_case(case: dict[str, Any], observed: dict[str, Any] | None, exception: dict[str, str] | None) -> tuple[bool, str]:
    mode = case["expected_mode"]
    expected_status = case["expected_status"]
    expected_rxcuis = set(case["expected_ingredient_rxcuis"])

    if exception is not None:
        return False, f"escaped {exception['type']}: {exception['message']}"
    if observed is None:
        return False, "no result and no captured exception"

    status = observed["normalization_status"]
    rxcui = observed.get("rxcui")
    candidates = observed.get("candidates") or []
    candidate_rxcuis = {item.get("rxcui") for item in candidates if item.get("rxcui")}

    if mode == "resolved_single":
        passed = (
            status == expected_status
            and rxcui in expected_rxcuis
            and len(expected_rxcuis) == 1
            and not observed["is_placeholder"]
            and not candidates
        )
        return passed, f"status={status}; rxcui={rxcui}; placeholder={observed['is_placeholder']}"
    if mode == "candidate_contains":
        passed = (
            status == expected_status
            and rxcui is None
            and expected_rxcuis.issubset(candidate_rxcuis)
            and not observed["is_placeholder"]
        )
        return passed, f"status={status}; rxcui={rxcui}; candidate_rxcuis={sorted(candidate_rxcuis)}"
    if mode == "resolved_set":
        observed_set = {rxcui} if rxcui else set()
        passed = (
            status == expected_status
            and observed_set == expected_rxcuis
            and not observed["is_placeholder"]
        )
        return passed, f"status={status}; represented_set={sorted(observed_set)}; expected_set={sorted(expected_rxcuis)}"
    if mode == "unmatched_placeholder":
        passed = (
            status == expected_status
            and observed["is_placeholder"]
            and isinstance(rxcui, str)
            and rxcui.startswith("placeholder:")
            and not candidates
        )
        return passed, f"status={status}; rxcui={rxcui}; placeholder={observed['is_placeholder']}"
    if mode == "controlled_service_failure":
        passed = (
            status == expected_status
            and observed["is_placeholder"]
            and isinstance(rxcui, str)
            and rxcui.startswith("placeholder:")
        )
        return passed, f"status={status}; rxcui={rxcui}; placeholder={observed['is_placeholder']}"
    raise RuntimeError(f"Unsupported expected mode: {mode}")


async def execute() -> int:
    args = parse_args()
    host, database_name, port = validate_database_url()
    fixtures = json.loads(args.fixtures.read_text(encoding="utf-8"))
    if fixtures["metadata"]["case_count"] != 30 or len(fixtures["cases"]) != 30:
        raise RuntimeError("Expected exactly 30 frozen cases.")
    if len({case["id"] for case in fixtures["cases"]}) != 30:
        raise RuntimeError("Case IDs must be unique.")

    api_log: list[dict[str, Any]] = []
    reference = await verify_references(fixtures, api_log)
    args.reference_output.parent.mkdir(parents=True, exist_ok=True)
    args.reference_output.write_text(
        json.dumps(reference, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not reference["summary"]["all_references_verified"]:
        args.api_log.parent.mkdir(parents=True, exist_ok=True)
        args.api_log.write_text(
            json.dumps({"calls": api_log}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("Reference verification failed; application benchmark not executed.")
        return 2

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from app.db.session import Base, SessionLocal, engine
    import app.models.audit  # noqa: F401
    import app.models.check  # noqa: F401
    import app.models.drug  # noqa: F401
    import app.models.interaction  # noqa: F401
    import app.models.patient  # noqa: F401
    from app.models.drug import Drug, DrugAlias, UnresolvedDrugEntry
    from app.services import normalization as normalization_service

    if inspect(engine).get_table_names():
        raise RuntimeError("Normalization database must be empty.")
    with engine.connect() as connection:
        server_address = connection.scalar(text("SELECT host(inet_server_addr())"))
        server_version = connection.scalar(text("SHOW server_version"))
    if server_address not in {"127.0.0.1", "::1"}:
        raise RuntimeError(f"Server is not loopback-only: {server_address!r}")
    Base.metadata.create_all(bind=engine)

    original_get = normalization_service._rate_limited_get_json
    case_results: list[dict[str, Any]] = []
    application_call_count = 0

    for case in fixtures["cases"]:
        db = SessionLocal()
        observed: dict[str, Any] | None = None
        exception: dict[str, str] | None = None
        case_calls: list[dict[str, Any]] = []

        async def traced_get(client: httpx.AsyncClient, path: str, params: dict[str, Any]) -> dict[str, Any]:
            payload = await original_get(client, path, params)
            entry = {
                "phase": "application_execution",
                "case_id": case["id"],
                "fetched_at": datetime.now(UTC).isoformat(),
                "path": path,
                "params": params,
                "response": payload,
            }
            case_calls.append(entry)
            api_log.append(entry)
            return payload

        async def injected_failure(client: httpx.AsyncClient, path: str, params: dict[str, Any]) -> dict[str, Any]:
            entry = {
                "phase": "application_execution",
                "case_id": case["id"],
                "fetched_at": datetime.now(UTC).isoformat(),
                "path": path,
                "params": params,
                "injected_exception": "httpx.ConnectError",
            }
            case_calls.append(entry)
            api_log.append(entry)
            request = httpx.Request("GET", f"{RXNORM_BASE_URL}{path}", params=params)
            raise httpx.ConnectError("Injected RxNorm connection failure.", request=request)

        selected_get = injected_failure if case["category"] == "service_failure" else traced_get
        try:
            with patch.object(normalization_service, "_rate_limited_get_json", new=selected_get):
                result = await normalization_service.normalize_drug_name(case["raw_input"], db)
            observed = result.model_dump(mode="json")
        except Exception as exc:
            db.rollback()
            exception = {"type": type(exc).__name__, "message": str(exc)}

        database_artifacts = {
            "drugs": int(db.scalar(select(func.count(Drug.rxcui)))),
            "aliases": int(db.scalar(select(func.count(DrugAlias.id)))),
            "unresolved_entries": int(db.scalar(select(func.count(UnresolvedDrugEntry.id)))),
        }
        passed, decision_detail = evaluate_case(case, observed, exception)
        case_results.append(
            {
                "case_id": case["id"],
                "category": case["category"],
                "raw_input": case["raw_input"],
                "expected_mode": case["expected_mode"],
                "expected_status": case["expected_status"],
                "expected_ingredient_rxcuis": case["expected_ingredient_rxcuis"],
                "passed": passed,
                "decision_detail": decision_detail,
                "observed": observed,
                "exception": exception,
                "database_artifacts": database_artifacts,
                "application_api_call_count": len(case_calls),
            }
        )
        application_call_count += len(case_calls)
        db.close()
        with engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE TABLE drug_aliases, drug_external_ids, "
                    "unresolved_drug_entries, drugs RESTART IDENTITY CASCADE"
                )
            )

    category_items: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in case_results:
        category_items[item["category"]].append(item)
    category_summary = {
        category: {
            "cases": len(items),
            "passed": sum(item["passed"] for item in items),
            "failed": sum(not item["passed"] for item in items),
            "pass_rate": round(sum(item["passed"] for item in items) / len(items), 6),
        }
        for category, items in sorted(category_items.items())
    }

    passed_count = sum(item["passed"] for item in case_results)
    exception_count = sum(item["exception"] is not None for item in case_results)
    benchmark_passed = (
        reference["summary"]["all_references_verified"]
        and len(case_results) == 30
        and passed_count == 30
        and exception_count == 0
    )
    source_paths = [
        "app/services/normalization.py",
        "app/models/drug.py",
        "app/models/enums.py",
    ]
    payload = {
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "repository_head_at_execution": git_output("rev-parse", "HEAD"),
            "evaluated_source_commit": git_output(
                "log",
                "-1",
                "--format=%H",
                "--",
                *source_paths,
            ),
            "database": {
                "host": host,
                "port": port,
                "name": database_name,
                "server_address": server_address,
                "server_version": server_version,
                "credentials_recorded": False,
            },
            "environment": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "python": sys.version,
                "packages": {
                    "httpx": package_version("httpx"),
                    "pydantic": package_version("pydantic"),
                    "sqlalchemy": package_version("sqlalchemy"),
                    "psycopg2-binary": package_version("psycopg2-binary"),
                },
            },
            "schema_setup": "SQLAlchemy Base.metadata.create_all (not Alembic)",
            "fixture_sha256": sha256_file(args.fixtures),
            "runner_sha256": sha256_file(SCRIPT_PATH),
            "source_sha256": {
                path: sha256_file(PROJECT_ROOT / path) for path in source_paths
            },
            "reference_release": fixtures["metadata"]["rxnorm_release"],
            "reference_api_version": fixtures["metadata"]["rxnorm_api_version"],
        },
        "summary": {
            "expected_cases": 30,
            "completed_cases": len(case_results),
            "passed": passed_count,
            "failed": len(case_results) - passed_count,
            "pass_rate": round(passed_count / len(case_results), 6),
            "exceptions": exception_count,
            "reference_cases_verified": reference["summary"]["verified"],
            "reference_cases_failed": reference["summary"]["failed"],
            "official_api_calls_total": len(api_log),
            "application_api_calls": application_call_count,
            "benchmark_passed": benchmark_passed,
        },
        "category_summary": category_summary,
        "cases": case_results,
        "limitations": [
            "Purposive 30-case terminology-conformance set; no prevalence weighting or human adjudication.",
            "Most expected mappings and the application share the official RxNorm vocabulary/service.",
            "Misspellings are investigator-selected rather than sampled from pharmacy error logs.",
            "One injected connection-failure shape and one execution environment.",
            "Terminology conformance is not clinical validation or deployment safety evidence.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.api_log.parent.mkdir(parents=True, exist_ok=True)
    args.api_log.write_text(
        json.dumps({"calls": api_log}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"references={reference['summary']['verified']}/30; cases={len(case_results)}/30; "
        f"passed={passed_count}; failed={len(case_results) - passed_count}; "
        f"exceptions={exception_count}; benchmark_passed={benchmark_passed}"
    )
    return 0 if benchmark_passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(execute()))
