#!/usr/bin/env python3
"""Run the existing RxCheck evaluator against a guarded local-only database."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[5]
EXPECTED_TABLES = {
    "audit_events",
    "conditions",
    "drug_aliases",
    "drug_external_ids",
    "drugs",
    "foods",
    "interaction_acknowledgments",
    "interaction_check_findings",
    "interaction_check_runs",
    "interaction_overrides",
    "interaction_source_assertions",
    "interactions",
    "llm_explanations",
    "patient_conditions",
    "patient_identifiers",
    "patient_medications",
    "patients",
    "source_coverage_checks",
    "unresolved_drug_entries",
    "users",
}
COUNTED_TABLES = [
    "users",
    "patients",
    "drugs",
    "foods",
    "conditions",
    "patient_medications",
    "patient_conditions",
    "interactions",
    "interaction_source_assertions",
    "interaction_check_runs",
    "interaction_check_findings",
    "interaction_acknowledgments",
    "interaction_overrides",
    "audit_events",
]
HASHED_SOURCES = [
    "paper/rxcheck_manuscript_0.1v.md",
    "research/evaluate_rxcheck.py",
    "app/services/orchestrator.py",
    "app/api/interactions.py",
    "app/schemas/interaction.py",
    "app/models/audit.py",
    "app/models/check.py",
    "app/models/drug.py",
    "app/models/interaction.py",
    "app/models/patient.py",
    "app/db/session.py",
    "requirements.txt",
]
EVIDENCE_SCRIPTS = [
    SCRIPT_PATH.parent / "run_isolated_evaluation.py",
    SCRIPT_PATH.parent / "run_repetitions.sh",
    SCRIPT_PATH.parent / "summarize_repetitions.py",
]


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
    raw_url = os.environ.get("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("DATABASE_URL must be set explicitly.")

    url = make_url(raw_url)
    if not url.drivername.startswith("postgresql"):
        raise RuntimeError("Only PostgreSQL URLs are allowed for this reproduction.")
    if url.host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Refusing non-loopback database host.")
    if not (url.database or "").startswith("rxcheck_evidence_run_"):
        raise RuntimeError("Refusing a database outside the evidence-run naming convention.")
    if not url.port:
        raise RuntimeError("An explicit local database port is required.")
    return url.host, url.database or "", url.port


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    return parser.parse_args()


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
    from research.evaluate_rxcheck import run_evaluation

    started_at = datetime.now(UTC)
    monotonic_start = time.perf_counter()
    preexisting_tables = sorted(inspect(engine).get_table_names())
    if preexisting_tables:
        raise RuntimeError(f"Expected an empty database; found tables: {preexisting_tables}")

    with engine.connect() as connection:
        server_address = connection.scalar(text("SELECT host(inet_server_addr())"))
        server_version = connection.scalar(text("SHOW server_version"))
    if server_address not in {"127.0.0.1", "::1"}:
        raise RuntimeError(f"Server-side address is not loopback: {server_address!r}")

    Base.metadata.create_all(bind=engine)
    created_tables = sorted(inspect(engine).get_table_names())
    missing_tables = sorted(EXPECTED_TABLES - set(created_tables))
    unexpected_tables = sorted(set(created_tables) - EXPECTED_TABLES)

    db = SessionLocal()
    try:
        evaluation = await run_evaluation(db)
        row_counts = {
            table: int(db.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one())
            for table in COUNTED_TABLES
        }
    finally:
        db.close()

    completed_at = datetime.now(UTC)
    source_hashes = {
        relative_path: sha256_file(PROJECT_ROOT / relative_path)
        for relative_path in HASHED_SOURCES
    }
    evaluated_source_commit = git_output(
        "log",
        "-1",
        "--format=%H",
        "--",
        "app",
        "research/evaluate_rxcheck.py",
        "requirements.txt",
    )
    assertions = {
        "empty_database_before_setup": len(preexisting_tables) == 0,
        "expected_schema_created": not missing_tables and not unexpected_tables,
        "all_26_scenarios_passed": evaluation["summary"]
        == {"total_scenarios": 26, "passed": 26, "failed": 0},
        "no_paid_external_apis_called": evaluation["metadata"]["external_paid_apis_called"] is False,
        "no_free_external_apis_called": evaluation["metadata"]["external_free_apis_called"] is False,
        "loopback_url_guard_passed": host in {"127.0.0.1", "localhost"},
        "loopback_server_verified": server_address in {"127.0.0.1", "::1"},
    }
    payload: dict[str, Any] = {
        "reproduction_metadata": {
            "run_id": args.run_id,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "wall_duration_seconds": round(time.perf_counter() - monotonic_start, 6),
            "repository_head_at_execution": git_output("rev-parse", "HEAD"),
            "evaluated_source_commit": evaluated_source_commit,
            "working_tree_status_at_execution": git_output("status", "--short"),
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
                    "anthropic": package_version("anthropic"),
                    "fastapi": package_version("fastapi"),
                    "psycopg2-binary": package_version("psycopg2-binary"),
                    "pydantic": package_version("pydantic"),
                    "pydantic-settings": package_version("pydantic-settings"),
                    "sqlalchemy": package_version("sqlalchemy"),
                },
            },
            "schema_setup": "SQLAlchemy Base.metadata.create_all (not Alembic)",
            "preexisting_tables": preexisting_tables,
            "created_tables": created_tables,
            "missing_expected_tables": missing_tables,
            "unexpected_tables": unexpected_tables,
            "source_sha256": source_hashes,
            "evidence_script_sha256": {
                path.name: sha256_file(path) for path in EVIDENCE_SCRIPTS
            },
        },
        "reproduction_assertions": assertions,
        "post_run_row_counts": row_counts,
        "evaluation": evaluation,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    passed = all(assertions.values())
    print(
        f"{args.run_id}: scenarios={evaluation['summary']['passed']}/"
        f"{evaluation['summary']['total_scenarios']}; assertions_passed={passed}; "
        f"postgres={server_version}; database={database_name}@{host}:{port}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(execute()))
