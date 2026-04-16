from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import Json, execute_values

DATABASE_URL = "postgresql://postgres:QYgkiqCSPhykgsPfYRMkkrPrZMsVyhkG@nozomi.proxy.rlwy.net:49544/railway"
DDINTER_DIR = Path("/Users/shubhamjoshi/Desktop/pharmacy/ddinter")
CSV_FILES = [
    DDINTER_DIR / "ddinter_downloads_code_A.csv",
    DDINTER_DIR / "ddinter_downloads_code_B.csv",
    DDINTER_DIR / "ddinter_downloads_code_D.csv",
    DDINTER_DIR / "ddinter_downloads_code_H.csv",
    DDINTER_DIR / "ddinter_downloads_code_L.csv",
    DDINTER_DIR / "ddinter_downloads_code_P.csv",
    DDINTER_DIR / "ddinter_downloads_code_R.csv",
    DDINTER_DIR / "ddinter_downloads_code_V.csv",
]
BATCH_SIZE = 10_000


def normalize_name(value: str) -> str:
    return str(value).strip().lower()


def map_severity(raw: str) -> str:
    mapping = {
        "major": "major",
        "moderate": "moderate",
        "minor": "minor",
    }
    return mapping.get(normalize_name(raw), "unknown")


def load_alias_map(cur) -> dict[str, str]:
    alias_map: dict[str, str] = {}

    cur.execute("SELECT alias, rxcui FROM drug_aliases")
    for alias, rxcui in cur.fetchall():
        alias_map[normalize_name(alias)] = rxcui

    cur.execute("SELECT preferred_name, rxcui FROM drugs WHERE is_placeholder = FALSE")
    for preferred_name, rxcui in cur.fetchall():
        alias_map[normalize_name(preferred_name)] = rxcui

    print(f"Loaded {len(alias_map)} drug name mappings from database")
    return alias_map


def load_csvs() -> pd.DataFrame:
    all_dfs = []
    for filename in CSV_FILES:
        df = pd.read_csv(filename)
        print(f"Loaded {filename.name}: {len(df)} rows")
        all_dfs.append(df)

    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"Total rows across all files: {len(combined)}")
    return combined


def resolve_rows(combined: pd.DataFrame, alias_map: dict[str, str]) -> tuple[list[dict], list[dict], Counter]:
    resolved_rows: list[dict] = []
    quarantine_rows: list[dict] = []
    severity_counter: Counter[str] = Counter()

    for row in combined.itertuples(index=False):
        raw_a = str(row.Drug_A).strip()
        raw_b = str(row.Drug_B).strip()
        norm_a = normalize_name(raw_a)
        norm_b = normalize_name(raw_b)
        rxcui_a = alias_map.get(norm_a)
        rxcui_b = alias_map.get(norm_b)

        if not rxcui_a or not rxcui_b:
            quarantine_rows.append(
                {
                    "DDInterID_A": row.DDInterID_A,
                    "Drug_A": raw_a,
                    "DDInterID_B": row.DDInterID_B,
                    "Drug_B": raw_b,
                    "Level": row.Level,
                    "reason": "drug not found in alias map",
                }
            )
            continue

        drug_a_rxcui, drug_b_rxcui = sorted([rxcui_a, rxcui_b])
        severity = map_severity(row.Level)
        severity_counter[severity] += 1
        resolved_rows.append(
            {
                "DDInterID_A": row.DDInterID_A,
                "Drug_A": raw_a,
                "DDInterID_B": row.DDInterID_B,
                "Drug_B": raw_b,
                "level_raw": str(row.Level).strip(),
                "severity": severity,
                "drug_a_rxcui": drug_a_rxcui,
                "drug_b_rxcui": drug_b_rxcui,
                "raw": {
                    "DDInterID_A": row.DDInterID_A,
                    "Drug_A": raw_a,
                    "DDInterID_B": row.DDInterID_B,
                    "Drug_B": raw_b,
                    "Level": str(row.Level).strip(),
                },
            }
        )

    print(f"Total rows resolved successfully: {len(resolved_rows)}")
    print(f"Total rows quarantined (drug not found): {len(quarantine_rows)}")
    return resolved_rows, quarantine_rows, severity_counter


def chunked(items: list, size: int):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def bulk_upsert_interactions(cur, resolved_rows: list[dict]) -> int:
    pair_to_uuid: dict[tuple[str, str], str] = {}
    for row in resolved_rows:
        pair_to_uuid.setdefault(
            (row["drug_a_rxcui"], row["drug_b_rxcui"]),
            str(uuid.uuid4()),
        )

    interaction_rows = [
        (interaction_id, "DDI", drug_a_rxcui, drug_b_rxcui, datetime.utcnow(), datetime.utcnow())
        for (drug_a_rxcui, drug_b_rxcui), interaction_id in pair_to_uuid.items()
    ]

    total = len(interaction_rows)
    for offset, batch in enumerate(chunked(interaction_rows, BATCH_SIZE), start=1):
        execute_values(
            cur,
            """
            INSERT INTO interactions (id, interaction_type, drug_a_rxcui, drug_b_rxcui, created_at, updated_at)
            VALUES %s
            ON CONFLICT (interaction_type, drug_a_rxcui, drug_b_rxcui) DO NOTHING
            """,
            batch,
            page_size=BATCH_SIZE,
        )
        processed = min(offset * BATCH_SIZE, total)
        print(f"[interactions] processed {processed}/{total} pairs")

    return total


def load_pair_to_id(cur) -> dict[tuple[str, str], str]:
    cur.execute(
        """
        SELECT id, drug_a_rxcui, drug_b_rxcui
        FROM interactions
        WHERE interaction_type = 'DDI'
        """
    )
    return {(drug_a_rxcui, drug_b_rxcui): interaction_id for interaction_id, drug_a_rxcui, drug_b_rxcui in cur.fetchall()}


def bulk_upsert_assertions(cur, resolved_rows: list[dict], pair_to_id: dict[tuple[str, str], str]) -> int:
    assertion_rows = []
    for row in resolved_rows:
        interaction_id = pair_to_id.get((row["drug_a_rxcui"], row["drug_b_rxcui"]))
        if interaction_id is None:
            continue

        source_record_id = f"{row['DDInterID_A']}_{row['DDInterID_B']}"
        assertion_rows.append(
            (
                interaction_id,
                "DDInter",
                row["level_raw"],
                row["severity"],
                source_record_id,
                datetime.utcnow(),
                Json(row["raw"]),
            )
        )

    total = len(assertion_rows)
    for offset, batch in enumerate(chunked(assertion_rows, BATCH_SIZE), start=1):
        execute_values(
            cur,
            """
            INSERT INTO interaction_source_assertions
            (interaction_id, source, source_severity_raw, severity, source_record_id, imported_at, raw_payload)
            VALUES %s
            ON CONFLICT (interaction_id, source, source_record_id) DO NOTHING
            """,
            batch,
            page_size=BATCH_SIZE,
        )
        processed = min(offset * BATCH_SIZE, total)
        print(f"[assertions] processed {processed}/{total} rows")

    return total


def bulk_insert_coverage_checks(cur, resolved_rows: list[dict]) -> int:
    coverage_rows = [
        (row["drug_a_rxcui"], row["drug_b_rxcui"], "DDInter", datetime.utcnow(), True)
        for row in resolved_rows
    ]

    total = len(coverage_rows)
    for offset, batch in enumerate(chunked(coverage_rows, BATCH_SIZE), start=1):
        execute_values(
            cur,
            """
            INSERT INTO source_coverage_checks
            (drug_a_rxcui, drug_b_rxcui, source, checked_at, found_interaction)
            VALUES %s
            """,
            batch,
            page_size=BATCH_SIZE,
        )
        processed = min(offset * BATCH_SIZE, total)
        print(f"[coverage] processed {processed}/{total} rows")

    return total


def fetch_db_counts(cur) -> dict[str, int]:
    counts = {}
    cur.execute("SELECT COUNT(*) FROM interactions")
    counts["interactions"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM interaction_source_assertions WHERE source = 'DDInter'")
    counts["assertions"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM source_coverage_checks WHERE source = 'DDInter'")
    counts["coverage_checks"] = cur.fetchone()[0]
    return counts


def fetch_hub_scores(cur) -> list[tuple[str, int]]:
    cur.execute(
        """
        SELECT d.preferred_name, COUNT(*) as interaction_count
        FROM interactions i
        JOIN drugs d ON (d.rxcui = i.drug_a_rxcui OR d.rxcui = i.drug_b_rxcui)
        WHERE d.is_placeholder = FALSE
        GROUP BY d.preferred_name
        ORDER BY interaction_count DESC
        LIMIT 10
        """
    )
    return cur.fetchall()


def main() -> None:
    start_time = datetime.utcnow()
    combined = load_csvs()

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            alias_map = load_alias_map(cur)
            resolved_rows, quarantine_rows, severity_counter = resolve_rows(combined, alias_map)

            bulk_upsert_interactions(cur, resolved_rows)
            conn.commit()
            print("Interactions upserted")

            pair_to_id = load_pair_to_id(cur)
            attempted_assertions = bulk_upsert_assertions(cur, resolved_rows, pair_to_id)
            conn.commit()
            print(f"Assertions upserted attempt count: {attempted_assertions}")

            written_coverage = bulk_insert_coverage_checks(cur, resolved_rows)
            conn.commit()
            print(f"Coverage checks written: {written_coverage}")

            counts = fetch_db_counts(cur)
            hub_scores = fetch_hub_scores(cur)

    duration = datetime.utcnow() - start_time

    print("=====================================")
    print("DDInter Import Complete")
    print("=====================================")
    print(f"Total CSV rows:          {len(combined):,}")
    print(f"Successfully resolved:   {len(resolved_rows):,}")
    print(f"Quarantined:             {len(quarantine_rows):,}")
    print(f"Interactions in DB:      {counts['interactions']:,}")
    print(f"Assertions in DB:        {counts['assertions']:,}")
    print(f"Coverage checks written: {counts['coverage_checks']:,}")
    print(f"Duration:                {duration}")
    print()
    print("Severity distribution:")
    print(f"  Major:          {severity_counter['major']:,}")
    print(f"  Moderate:       {severity_counter['moderate']:,}")
    print(f"  Minor:          {severity_counter['minor']:,}")
    print(f"  Unknown:        {severity_counter['unknown']:,}")
    print()
    print("Top 10 hub drugs:")
    for index, (drug_name, interaction_count) in enumerate(hub_scores, start=1):
        print(f"  {index}. {drug_name} - {interaction_count} interactions")
    print("=====================================")


if __name__ == "__main__":
    main()
