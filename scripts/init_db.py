from __future__ import annotations

import sys
from pathlib import Path

import psycopg2
from sqlalchemy import inspect, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.db.session import Base, engine
import app.models.audit  # noqa: F401
import app.models.check  # noqa: F401
import app.models.drug  # noqa: F401
import app.models.interaction  # noqa: F401
import app.models.patient  # noqa: F401


EXPECTED_TABLES = [
    "drugs",
    "drug_aliases",
    "drug_external_ids",
    "unresolved_drug_entries",
    "foods",
    "conditions",
    "interactions",
    "interaction_source_assertions",
    "source_coverage_checks",
    "users",
    "patients",
    "patient_identifiers",
    "patient_conditions",
    "patient_medications",
    "interaction_check_runs",
    "interaction_check_findings",
    "llm_explanations",
    "interaction_acknowledgments",
    "interaction_overrides",
    "audit_events",
]


def main() -> None:
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    cur.execute("CREATE EXTENSION IF NOT EXISTS citext;")
    cur.close()
    conn.close()
    print("Extensions enabled")

    # Ensure the public schema exists and create all mapped tables.
    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
    Base.metadata.create_all(bind=engine)
    print("Tables created")

    inspector = inspect(engine)
    existing_tables = sorted(inspector.get_table_names())
    print(f"Tables found ({len(existing_tables)}):")
    for table_name in existing_tables:
        print(f" - {table_name}")

    missing_tables = [table_name for table_name in EXPECTED_TABLES if table_name not in existing_tables]
    if missing_tables:
        raise RuntimeError(f"Missing expected tables: {', '.join(missing_tables)}")

    print(f"Confirmed {len(EXPECTED_TABLES)} expected tables exist")


if __name__ == "__main__":
    main()
