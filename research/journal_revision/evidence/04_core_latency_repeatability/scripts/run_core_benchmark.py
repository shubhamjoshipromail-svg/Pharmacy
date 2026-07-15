#!/usr/bin/env python3
"""Benchmark the unchanged RxCheck core checker in a guarded local database."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import importlib.metadata
import itertools
import json
import math
import platform
import statistics
import subprocess
import sys
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

from psycopg2.extras import Json, execute_values
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[5]
BACKGROUND_DRUGS = 600
BACKGROUND_INTERACTIONS = 150_000
WARMUPS = 5
PASSES = 3
ITERATIONS_PER_PASS = 30
P95_THRESHOLD_MS = 1_000.0
RELATIVE_MEDIAN_RANGE_LIMIT = 0.25
ABSOLUTE_MEDIAN_RANGE_LIMIT_MS = 2.0
WORKLOAD_SIZES = [2, 10, 25, 50]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    return parser.parse_args()


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
    if url.database != "rxcheck_benchmark":
        raise RuntimeError("Refusing a database outside the benchmark naming convention.")
    if not url.port:
        raise RuntimeError("An explicit local database port is required.")
    return url.host, url.database or "", url.port


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def execute_batch(cursor: Any, statement: str, rows: list[tuple[Any, ...]]) -> None:
    if rows:
        execute_values(cursor, statement, rows, page_size=5_000)


def seed_database(engine: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    started = time.perf_counter()
    now = datetime.now(UTC).replace(tzinfo=None)
    user_id = str(uuid.uuid4())
    background_rxcuis = [f"bg-{index:04d}" for index in range(BACKGROUND_DRUGS)]
    workloads: list[dict[str, Any]] = []

    raw_connection = engine.raw_connection()
    try:
        cursor = raw_connection.cursor()
        cursor.execute(
            """
            INSERT INTO users (id, email, full_name, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, "benchmark@rxcheck.local", "Benchmark User", "pharmacist", True, now),
        )
        drug_rows = [
            (rxcui, f"Background Drug {index:04d}", "IN", True, False, now, now)
            for index, rxcui in enumerate(background_rxcuis)
        ]
        execute_batch(
            cursor,
            """
            INSERT INTO drugs
            (rxcui, preferred_name, tty, is_active, is_placeholder, created_at, updated_at)
            VALUES %s
            """,
            drug_rows,
        )

        interaction_statement = """
            INSERT INTO interactions
            (id, interaction_type, drug_a_rxcui, drug_b_rxcui, created_at, updated_at)
            VALUES %s
        """
        assertion_statement = """
            INSERT INTO interaction_source_assertions
            (interaction_id, source, source_severity_raw, severity, mechanism, management,
             source_record_id, imported_at, raw_payload)
            VALUES %s
        """
        interaction_batch: list[tuple[Any, ...]] = []
        assertion_batch: list[tuple[Any, ...]] = []
        for index, (drug_a, drug_b) in enumerate(
            itertools.islice(itertools.combinations(background_rxcuis, 2), BACKGROUND_INTERACTIONS)
        ):
            interaction_id = str(uuid.uuid4())
            interaction_batch.append((interaction_id, "DDI", drug_a, drug_b, now, now))
            assertion_batch.append(
                (
                    interaction_id,
                    "DDInter",
                    "Moderate",
                    "moderate",
                    "Synthetic background mechanism.",
                    "Synthetic background management.",
                    f"benchmark-bg-{index}",
                    now,
                    Json({"benchmark_background": True, "index": index}),
                )
            )
            if len(interaction_batch) == 5_000:
                execute_batch(cursor, interaction_statement, interaction_batch)
                execute_batch(cursor, assertion_statement, assertion_batch)
                interaction_batch.clear()
                assertion_batch.clear()
        execute_batch(cursor, interaction_statement, interaction_batch)
        execute_batch(cursor, assertion_statement, assertion_batch)

        for medication_count in WORKLOAD_SIZES:
            pair_count = math.comb(medication_count, 2)
            for density in ("zero", "ten_percent"):
                matched_count = 0 if density == "zero" else max(1, math.ceil(pair_count * 0.10))
                workload_id = f"n{medication_count}_{density}"
                patient_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO patients (id, created_at, created_by, is_synthetic)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (patient_id, now, user_id, True),
                )
                medication_rxcuis = [
                    f"wl-{workload_id}-{index:03d}" for index in range(medication_count)
                ]
                workload_drugs = [
                    (rxcui, f"Workload {workload_id} Drug {index:03d}", "IN", True, False, now, now)
                    for index, rxcui in enumerate(medication_rxcuis)
                ]
                execute_batch(
                    cursor,
                    """
                    INSERT INTO drugs
                    (rxcui, preferred_name, tty, is_active, is_placeholder, created_at, updated_at)
                    VALUES %s
                    """,
                    workload_drugs,
                )
                medication_rows = [
                    (
                        str(uuid.uuid4()),
                        patient_id,
                        rxcui,
                        rxcui,
                        "matched_exact",
                        True,
                        user_id,
                        now,
                    )
                    for rxcui in medication_rxcuis
                ]
                execute_batch(
                    cursor,
                    """
                    INSERT INTO patient_medications
                    (id, patient_id, rxcui, raw_input, normalization_status, is_active, added_by, added_at)
                    VALUES %s
                    """,
                    medication_rows,
                )
                matched_pairs = list(itertools.islice(itertools.combinations(medication_rxcuis, 2), matched_count))
                workload_interactions: list[tuple[Any, ...]] = []
                workload_assertions: list[tuple[Any, ...]] = []
                for pair_index, (drug_a, drug_b) in enumerate(matched_pairs):
                    interaction_id = str(uuid.uuid4())
                    workload_interactions.append((interaction_id, "DDI", drug_a, drug_b, now, now))
                    workload_assertions.append(
                        (
                            interaction_id,
                            "DDInter",
                            "Moderate",
                            "moderate",
                            "Synthetic benchmark mechanism.",
                            "Synthetic benchmark management.",
                            f"benchmark-{workload_id}-{pair_index}",
                            now,
                            Json({"benchmark_workload": workload_id, "pair_index": pair_index}),
                        )
                    )
                execute_batch(cursor, interaction_statement, workload_interactions)
                execute_batch(cursor, assertion_statement, workload_assertions)
                workloads.append(
                    {
                        "workload_id": workload_id,
                        "patient_id": patient_id,
                        "user_id": user_id,
                        "medication_count": medication_count,
                        "pair_count": pair_count,
                        "matched_interaction_count": matched_count,
                        "density": density,
                    }
                )

        raw_connection.commit()
        cursor.execute("ANALYZE")
        raw_connection.commit()
        cursor.close()
    finally:
        raw_connection.close()

    with engine.connect() as connection:
        table_counts = {
            table: int(connection.scalar(text(f'SELECT COUNT(*) FROM "{table}"')))
            for table in (
                "drugs",
                "patients",
                "patient_medications",
                "interactions",
                "interaction_source_assertions",
            )
        }
        relation_sizes = {
            table: int(
                connection.scalar(
                    text("SELECT pg_total_relation_size(CAST(:table AS regclass))"),
                    {"table": table},
                )
            )
            for table in ("interactions", "interaction_source_assertions")
        }
    return workloads, {
        "seed_duration_seconds": round(time.perf_counter() - started, 6),
        "table_counts": table_counts,
        "relation_size_bytes": relation_sizes,
    }


def clean_patient_runs(engine: Any, patient_id: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM interaction_check_runs WHERE patient_id = :patient_id"),
            {"patient_id": patient_id},
        )
        remaining_runs = int(
            connection.scalar(
                text("SELECT COUNT(*) FROM interaction_check_runs WHERE patient_id = :patient_id"),
                {"patient_id": patient_id},
            )
        )
        remaining_findings = int(
            connection.scalar(
                text(
                    """
                    SELECT COUNT(*)
                    FROM interaction_check_findings f
                    JOIN interaction_check_runs r ON r.id = f.run_id
                    WHERE r.patient_id = :patient_id
                    """
                ),
                {"patient_id": patient_id},
            )
        )
    if remaining_runs or remaining_findings:
        raise RuntimeError("Benchmark run cleanup failed.")


async def timed_check(workload: dict[str, Any], SessionLocal: Any, engine: Any, run_check: Any) -> dict[str, Any]:
    db = SessionLocal()
    try:
        started_ns = time.perf_counter_ns()
        result = await run_check(workload["patient_id"], workload["user_id"], db)
        elapsed_ms = (time.perf_counter_ns() - started_ns) / 1_000_000
    finally:
        db.close()

    errors = []
    expected = {
        "patient_id": workload["patient_id"],
        "total_medications": workload["medication_count"],
        "total_pairs_checked": workload["pair_count"],
        "total_interactions_found": workload["matched_interaction_count"],
        "summary_count": workload["matched_interaction_count"],
    }
    observed = {
        "patient_id": result.patient_id,
        "total_medications": result.total_medications,
        "total_pairs_checked": result.total_pairs_checked,
        "total_interactions_found": result.total_interactions_found,
        "summary_count": len(result.summaries),
    }
    for key, expected_value in expected.items():
        if observed[key] != expected_value:
            errors.append(f"{key}: expected {expected_value!r}, observed {observed[key]!r}")
    if not result.run_id:
        errors.append("run_id was empty")

    with engine.connect() as connection:
        persisted_findings = int(
            connection.scalar(
                text("SELECT COUNT(*) FROM interaction_check_findings WHERE run_id = :run_id"),
                {"run_id": result.run_id},
            )
        )
    if persisted_findings != workload["matched_interaction_count"]:
        errors.append(
            f"persisted_findings: expected {workload['matched_interaction_count']}, observed {persisted_findings}"
        )
    clean_patient_runs(engine, workload["patient_id"])
    return {
        "elapsed_ms": round(elapsed_ms, 6),
        "application_duration_ms": result.duration_ms,
        "correct": not errors,
        "errors": errors,
    }


async def execute() -> int:
    args = parse_args()
    host, database_name, port = validate_database_url()
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from app.db.session import Base, SessionLocal, engine
    import app.models.audit  # noqa: F401
    import app.models.check  # noqa: F401
    import app.models.drug  # noqa: F401
    import app.models.interaction  # noqa: F401
    import app.models.patient  # noqa: F401
    from app.services.orchestrator import run_interaction_check

    preexisting_tables = sorted(inspect(engine).get_table_names())
    if preexisting_tables:
        raise RuntimeError(f"Expected empty database, found: {preexisting_tables}")
    with engine.connect() as connection:
        server_address = connection.scalar(text("SELECT host(inet_server_addr())"))
        server_version = connection.scalar(text("SHOW server_version"))
    if server_address not in {"127.0.0.1", "::1"}:
        raise RuntimeError(f"Server is not loopback-only: {server_address!r}")

    Base.metadata.create_all(bind=engine)
    workloads, seed_metadata = seed_database(engine)
    measurements: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []

    sentinel_error = AssertionError("External service must not be called by the core benchmark.")
    with (
        patch("app.services.llm.generate_explanation", side_effect=sentinel_error),
        patch("app.services.openfda.fetch_citations_for_interaction", side_effect=sentinel_error),
        patch("app.services.normalization.normalize_drug_name", side_effect=sentinel_error),
    ):
        for workload in workloads:
            for warmup_index in range(WARMUPS):
                try:
                    warmup = await timed_check(workload, SessionLocal, engine, run_interaction_check)
                    if not warmup["correct"]:
                        raise RuntimeError(f"Warm-up correctness failed: {warmup['errors']}")
                except Exception as exc:
                    exceptions.append(
                        {
                            "workload_id": workload["workload_id"],
                            "phase": "warmup",
                            "index": warmup_index,
                            "type": type(exc).__name__,
                            "message": str(exc),
                        }
                    )
                    break
            if exceptions:
                break

            for pass_number in range(1, PASSES + 1):
                for iteration in range(1, ITERATIONS_PER_PASS + 1):
                    try:
                        measurement = await timed_check(
                            workload, SessionLocal, engine, run_interaction_check
                        )
                        measurements.append(
                            {
                                "workload_id": workload["workload_id"],
                                "medication_count": workload["medication_count"],
                                "pair_count": workload["pair_count"],
                                "matched_interaction_count": workload["matched_interaction_count"],
                                "density": workload["density"],
                                "pass": pass_number,
                                "iteration": iteration,
                                **measurement,
                            }
                        )
                    except Exception as exc:
                        exceptions.append(
                            {
                                "workload_id": workload["workload_id"],
                                "phase": "measured",
                                "pass": pass_number,
                                "iteration": iteration,
                                "type": type(exc).__name__,
                                "message": str(exc),
                            }
                        )
                        break
                if exceptions:
                    break
            if exceptions:
                break

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for measurement in measurements:
        grouped[measurement["workload_id"]].append(measurement)
    workload_summaries = []
    for workload in workloads:
        items = grouped[workload["workload_id"]]
        elapsed = [item["elapsed_ms"] for item in items]
        pass_medians = []
        for pass_number in range(1, PASSES + 1):
            pass_values = [
                item["elapsed_ms"] for item in items if item["pass"] == pass_number
            ]
            pass_medians.append(round(statistics.median(pass_values), 6) if pass_values else None)
        present_pass_medians = [value for value in pass_medians if value is not None]
        median_range = (
            max(present_pass_medians) - min(present_pass_medians)
            if present_pass_medians
            else float("inf")
        )
        median_of_pass_medians = (
            statistics.median(present_pass_medians) if present_pass_medians else 0
        )
        relative_range = (
            median_range / median_of_pass_medians if median_of_pass_medians else float("inf")
        )
        correct_count = sum(item["correct"] for item in items)
        p95_ms = percentile(elapsed, 0.95) if elapsed else float("inf")
        repeatability_passed = (
            relative_range <= RELATIVE_MEDIAN_RANGE_LIMIT
            or median_range <= ABSOLUTE_MEDIAN_RANGE_LIMIT_MS
        )
        workload_summaries.append(
            {
                **{key: workload[key] for key in ("workload_id", "medication_count", "pair_count", "matched_interaction_count", "density")},
                "measured_calls": len(items),
                "correct_calls": correct_count,
                "min_ms": round(min(elapsed), 6) if elapsed else None,
                "median_ms": round(statistics.median(elapsed), 6) if elapsed else None,
                "mean_ms": round(statistics.mean(elapsed), 6) if elapsed else None,
                "population_stdev_ms": round(statistics.pstdev(elapsed), 6) if elapsed else None,
                "p95_ms": round(p95_ms, 6) if elapsed else None,
                "max_ms": round(max(elapsed), 6) if elapsed else None,
                "mean_application_duration_ms": round(
                    statistics.mean(item["application_duration_ms"] for item in items), 6
                )
                if items
                else None,
                "pass_medians_ms": pass_medians,
                "pass_median_absolute_range_ms": round(median_range, 6),
                "pass_median_relative_range": round(relative_range, 6),
                "latency_threshold_passed": p95_ms < P95_THRESHOLD_MS,
                "repeatability_passed": repeatability_passed,
                "workload_passed": (
                    len(items) == PASSES * ITERATIONS_PER_PASS
                    and correct_count == len(items)
                    and p95_ms < P95_THRESHOLD_MS
                    and repeatability_passed
                ),
            }
        )

    with engine.connect() as connection:
        remaining_runs = int(connection.scalar(text("SELECT COUNT(*) FROM interaction_check_runs")))
        remaining_findings = int(
            connection.scalar(text("SELECT COUNT(*) FROM interaction_check_findings"))
        )
    expected_measured_calls = len(workloads) * PASSES * ITERATIONS_PER_PASS
    total_correct = sum(item["correct"] for item in measurements)
    benchmark_passed = (
        len(measurements) == expected_measured_calls
        and total_correct == expected_measured_calls
        and not exceptions
        and all(item["workload_passed"] for item in workload_summaries)
        and remaining_runs == 0
        and remaining_findings == 0
    )

    source_paths = [
        "app/services/orchestrator.py",
        "app/services/checks.py",
        "app/schemas/interaction.py",
        "app/models/check.py",
        "app/models/interaction.py",
        "app/models/patient.py",
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
                "app/services/orchestrator.py",
                "app/services/checks.py",
                "app/models",
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
                    "fastapi": package_version("fastapi"),
                    "psycopg2-binary": package_version("psycopg2-binary"),
                    "pydantic": package_version("pydantic"),
                    "sqlalchemy": package_version("sqlalchemy"),
                },
            },
            "schema_setup": "SQLAlchemy Base.metadata.create_all (not Alembic)",
            "runner_sha256": sha256_file(SCRIPT_PATH),
            "source_sha256": {
                path: sha256_file(PROJECT_ROOT / path) for path in source_paths
            },
            "external_api_calls": 0,
            "concurrency": 1,
            "cache_condition": "five warm-ups per workload; warm local benchmark",
            "timed_scope": "run_interaction_check call including its database commit",
        },
        "protocol_parameters": {
            "background_drugs": BACKGROUND_DRUGS,
            "background_interactions": BACKGROUND_INTERACTIONS,
            "background_assertions": BACKGROUND_INTERACTIONS,
            "warmups_per_workload": WARMUPS,
            "passes": PASSES,
            "iterations_per_pass": ITERATIONS_PER_PASS,
            "expected_measured_calls": expected_measured_calls,
            "p95_threshold_ms": P95_THRESHOLD_MS,
            "relative_pass_median_range_limit": RELATIVE_MEDIAN_RANGE_LIMIT,
            "absolute_pass_median_range_limit_ms": ABSOLUTE_MEDIAN_RANGE_LIMIT_MS,
            "percentile_method": "linear interpolation over ordered observations",
        },
        "seed_metadata": seed_metadata,
        "workload_summaries": workload_summaries,
        "summary": {
            "expected_measured_calls": expected_measured_calls,
            "completed_measured_calls": len(measurements),
            "correct_measured_calls": total_correct,
            "exception_count": len(exceptions),
            "external_api_calls": 0,
            "remaining_check_runs_after_cleanup": remaining_runs,
            "remaining_findings_after_cleanup": remaining_findings,
            "all_workloads_passed": all(item["workload_passed"] for item in workload_summaries),
            "benchmark_passed": benchmark_passed,
        },
        "exceptions": exceptions,
        "limitations": [
            "Synthetic single-machine warm-cache benchmark; not a production SLA.",
            "Background interaction/assertion topology is uniform and not DDInter-distribution matched.",
            "No concurrency, HTTP, frontend, user, clinical, or cold-start behavior is measured.",
            "History rows are cleaned after every measured call outside the timed interval.",
            "Schema creation uses model metadata because the committed migration is empty.",
        ],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "workload_id",
        "medication_count",
        "pair_count",
        "matched_interaction_count",
        "density",
        "pass",
        "iteration",
        "elapsed_ms",
        "application_duration_ms",
        "correct",
        "errors",
    ]
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for measurement in measurements:
            writer.writerow({**measurement, "errors": json.dumps(measurement["errors"])})

    print(
        f"measured={len(measurements)}/{expected_measured_calls}; correct={total_correct}; "
        f"exceptions={len(exceptions)}; workloads_passed="
        f"{sum(item['workload_passed'] for item in workload_summaries)}/{len(workload_summaries)}; "
        f"benchmark_passed={benchmark_passed}"
    )
    return 0 if benchmark_passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(execute()))
