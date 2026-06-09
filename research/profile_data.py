"""Generate a conservative, read-only profile of the configured RxCheck database."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal


RESEARCH_DIR = Path(__file__).resolve().parent
RESULTS_JSON = RESEARCH_DIR / "data_profile.json"
RESULTS_MD = RESEARCH_DIR / "data_profile.md"

SUPPORTED_DDINTER_FILES = [
    "ddinter_downloads_code_A.csv",
    "ddinter_downloads_code_B.csv",
    "ddinter_downloads_code_D.csv",
    "ddinter_downloads_code_H.csv",
    "ddinter_downloads_code_L.csv",
    "ddinter_downloads_code_P.csv",
    "ddinter_downloads_code_R.csv",
    "ddinter_downloads_code_V.csv",
]


def scalar(db, sql: str) -> int | float:
    value = db.execute(text(sql)).scalar_one()
    return float(value) if isinstance(value, float) else int(value)


def distribution(db, sql: str) -> dict[str, int]:
    return {str(label): int(count) for label, count in db.execute(text(sql)).all()}


def build_profile(db) -> dict[str, Any]:
    interaction_types = distribution(
        db,
        """
        SELECT interaction_type, COUNT(*)
        FROM interactions
        GROUP BY interaction_type
        ORDER BY interaction_type
        """,
    )
    severity_distribution = distribution(
        db,
        """
        SELECT severity, COUNT(*)
        FROM interaction_source_assertions
        GROUP BY severity
        ORDER BY severity
        """,
    )
    source_distribution = distribution(
        db,
        """
        SELECT source, COUNT(*)
        FROM interaction_source_assertions
        GROUP BY source
        ORDER BY source
        """,
    )
    hub_rows = db.execute(
        text(
            """
            SELECT d.rxcui, d.preferred_name, COUNT(*) AS interaction_count
            FROM interactions i
            JOIN drugs d
              ON d.rxcui = i.drug_a_rxcui OR d.rxcui = i.drug_b_rxcui
            WHERE d.is_placeholder = FALSE
            GROUP BY d.rxcui, d.preferred_name
            ORDER BY interaction_count DESC, d.preferred_name
            LIMIT 10
            """
        )
    ).all()

    profile = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "Current configured RxCheck database; descriptive architecture/data profile only.",
        "counts": {
            "interactions": scalar(db, "SELECT COUNT(*) FROM interactions"),
            "source_assertions": scalar(db, "SELECT COUNT(*) FROM interaction_source_assertions"),
            "drugs": scalar(db, "SELECT COUNT(*) FROM drugs"),
            "drug_aliases": scalar(db, "SELECT COUNT(*) FROM drug_aliases"),
            "unresolved_drug_entries": scalar(db, "SELECT COUNT(*) FROM unresolved_drug_entries"),
            "drug_external_ids": scalar(db, "SELECT COUNT(*) FROM drug_external_ids"),
            "research_fixture_interactions": scalar(
                db,
                """
                SELECT COUNT(DISTINCT interaction_id)
                FROM interaction_source_assertions
                WHERE raw_payload ->> 'evaluation_fixture' = 'true'
                """,
            ),
            "research_fixture_assertions": scalar(
                db,
                """
                SELECT COUNT(*)
                FROM interaction_source_assertions
                WHERE raw_payload ->> 'evaluation_fixture' = 'true'
                """,
            ),
        },
        "interaction_type_distribution": interaction_types,
        "severity_distribution_by_assertion": severity_distribution,
        "source_distribution_by_assertion": source_distribution,
        "ddi_rows": interaction_types.get("DDI", 0),
        "dfi_rows": interaction_types.get("DFI", 0),
        "ddsi_rows": interaction_types.get("DDSI", 0),
        "source_conflict_count": scalar(
            db,
            """
            SELECT COUNT(*)
            FROM (
                SELECT interaction_id
                FROM interaction_source_assertions
                GROUP BY interaction_id
                HAVING COUNT(DISTINCT severity) > 1
            ) conflicts
            """,
        ),
        "assertions_per_interaction": {
            "average": round(
                float(
                    db.execute(
                        text(
                            """
                            SELECT COALESCE(AVG(assertion_count), 0)
                            FROM (
                                SELECT i.id, COUNT(a.id) AS assertion_count
                                FROM interactions i
                                LEFT JOIN interaction_source_assertions a ON a.interaction_id = i.id
                                GROUP BY i.id
                            ) counts
                            """
                        )
                    ).scalar_one()
                ),
                4,
            ),
            "maximum": scalar(
                db,
                """
                SELECT COALESCE(MAX(assertion_count), 0)
                FROM (
                    SELECT i.id, COUNT(a.id) AS assertion_count
                    FROM interactions i
                    LEFT JOIN interaction_source_assertions a ON a.interaction_id = i.id
                    GROUP BY i.id
                ) counts
                """,
            ),
        },
        "top_hub_drugs": [
            {"rxcui": rxcui, "preferred_name": name, "interaction_count": int(count)}
            for rxcui, name, count in hub_rows
        ],
        "ddinter_import": {
            "supported_files": SUPPORTED_DDINTER_FILES,
            "expected_columns": ["DDInterID_A", "Drug_A", "DDInterID_B", "Drug_B", "Level"],
            "represented_interaction_type": "DDI",
            "limitations": [
                "The current importer is tailored to eight locally named DDInter CSV partitions.",
                "It imports DDI pairs and severity labels but the listed files do not supply mechanism or management text.",
                "Drug-name resolution depends on aliases and preferred names already present in the database.",
                "Unresolved names are quarantined rather than imported as verified interactions.",
                "This profile does not establish completeness, clinical validity, or equivalence to the full DDInter release.",
                "Source coverage checks are append-only in the current bulk importer and are not profiled as unique evidence records.",
            ],
        },
        "manuscript_safe_claims": [
            "The configured prototype database contains the reported counts at the recorded generation time.",
            "The repository includes a bulk importer for eight named DDInter CSV partitions with DDI severity mapping.",
            "Interaction records can retain one or more source assertions, enabling descriptive source-conflict detection.",
            "Hub counts are database-derived interaction-degree counts and are not a measure of clinical risk.",
        ],
        "claims_not_supported": [
            "The database provides complete DDI coverage.",
            "The imported interactions are clinically validated by this profiling procedure.",
            "Hub ranking identifies the most dangerous drugs.",
            "The source-conflict count measures clinical disagreement quality or correctness.",
            "The database profile demonstrates FDA clearance, HIPAA compliance, or clinical effectiveness.",
        ],
    }
    return profile


def write_markdown(profile: dict[str, Any]) -> None:
    counts = profile["counts"]
    lines = [
        "# RxCheck Data And Source Profile",
        "",
        f"Generated: `{profile['generated_at']}`",
        "",
        "> This is a descriptive profile of the configured prototype database. It is not clinical validation, "
        "a completeness assessment, or a gold-standard comparison.",
        "",
        "## Core Counts",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Interactions | {counts['interactions']:,} |",
        f"| Source assertions | {counts['source_assertions']:,} |",
        f"| Drugs | {counts['drugs']:,} |",
        f"| Drug aliases | {counts['drug_aliases']:,} |",
        f"| Unresolved drug entries | {counts['unresolved_drug_entries']:,} |",
        f"| Drug external IDs | {counts['drug_external_ids']:,} |",
        f"| Research-fixture interactions identifiable by assertion payload | {counts['research_fixture_interactions']:,} |",
        f"| Research-fixture assertions | {counts['research_fixture_assertions']:,} |",
        "",
        "Research fixtures are counted explicitly because formative evaluation runs write synthetic rows to the "
        "configured database. Aggregate totals above include those rows.",
        "",
        "## Interaction Types",
        "",
        "| Type | Rows |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {interaction_type} | {count:,} |"
        for interaction_type, count in profile["interaction_type_distribution"].items()
    )
    lines.extend(
        [
            "",
            f"- DDI rows: **{profile['ddi_rows']:,}**",
            f"- DFI rows: **{profile['dfi_rows']:,}**",
            f"- DDSI rows: **{profile['ddsi_rows']:,}**",
            "",
            "## Assertion Severity And Sources",
            "",
            "| Severity | Assertions |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| {severity} | {count:,} |"
        for severity, count in profile["severity_distribution_by_assertion"].items()
    )
    lines.extend(["", "| Source | Assertions |", "|---|---:|"])
    lines.extend(
        f"| {source} | {count:,} |"
        for source, count in profile["source_distribution_by_assertion"].items()
    )
    lines.extend(
        [
            "",
            "## Assertion Structure",
            "",
            f"- Interactions with more than one distinct asserted severity: **{profile['source_conflict_count']:,}**",
            f"- Average assertions per interaction: **{profile['assertions_per_interaction']['average']:.4f}**",
            f"- Maximum assertions on one interaction: **{profile['assertions_per_interaction']['maximum']:,}**",
            "",
            "A source conflict means that stored assertions for one interaction contain more than one severity value. "
            "It does not establish which source is correct.",
            "",
            "## Top Hub Drugs",
            "",
            "| Rank | RxCUI | Preferred Name | Interaction Count |",
            "|---:|---|---|---:|",
        ]
    )
    lines.extend(
        f"| {index} | {row['rxcui']} | {row['preferred_name']} | {row['interaction_count']:,} |"
        for index, row in enumerate(profile["top_hub_drugs"], start=1)
    )
    lines.extend(
        [
            "",
            "These values are graph-degree counts in the stored interaction table, not clinical risk scores.",
            "",
            "## DDInter Import Support",
            "",
            "The current bulk importer names these files:",
            "",
        ]
    )
    lines.extend(f"- `{filename}`" for filename in profile["ddinter_import"]["supported_files"])
    lines.extend(["", "Current importer limitations:", ""])
    lines.extend(f"- {item}" for item in profile["ddinter_import"]["limitations"])
    lines.extend(["", "## Manuscript-Safe Claims", ""])
    lines.extend(f"- {item}" for item in profile["manuscript_safe_claims"])
    lines.extend(["", "## Claims Not Supported", ""])
    lines.extend(f"- {item}" for item in profile["claims_not_supported"])
    RESULTS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    db = SessionLocal()
    try:
        profile = build_profile(db)
        RESULTS_JSON.write_text(json.dumps(profile, indent=2, sort_keys=True), encoding="utf-8")
        write_markdown(profile)
    except Exception as exc:
        db.rollback()
        print(f"Data profiling failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        db.close()

    print(f"Wrote {RESULTS_JSON}")
    print(f"Wrote {RESULTS_MD}")
    print(
        f"Profiled {profile['counts']['interactions']:,} interactions and "
        f"{profile['counts']['source_assertions']:,} source assertions."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
