#!/usr/bin/env python3
"""Recover and profile DDInter provenance without connecting to the database."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import plistlib
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[5]
EXPECTED_FILES = [
    "ddinter_downloads_code_A.csv",
    "ddinter_downloads_code_B.csv",
    "ddinter_downloads_code_D.csv",
    "ddinter_downloads_code_H.csv",
    "ddinter_downloads_code_L.csv",
    "ddinter_downloads_code_P.csv",
    "ddinter_downloads_code_R.csv",
    "ddinter_downloads_code_V.csv",
]
EXPECTED_COLUMNS = ["DDInterID_A", "Drug_A", "DDInterID_B", "Drug_B", "Level"]
ALLOWED_LEVELS = {"major", "moderate", "minor", "unknown"}
DATA_EXTENSIONS = {
    ".backup",
    ".bz2",
    ".csv",
    ".db",
    ".dump",
    ".gz",
    ".parquet",
    ".sql",
    ".sqlite",
    ".tar",
    ".tsv",
    ".xz",
    ".zip",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--live-verify-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
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


def utc_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, UTC).isoformat()


def extended_attributes(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "where_from_urls": [],
        "quarantine_agent": None,
        "quarantine_timestamp": None,
    }
    def read_xattr(name: str) -> bytes:
        output = subprocess.check_output(
            ["xattr", "-px", name, str(path)],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return bytes.fromhex("".join(output.split()))

    try:
        raw_where_from = read_xattr("com.apple.metadata:kMDItemWhereFroms")
        parsed = plistlib.loads(raw_where_from)
        result["where_from_urls"] = list(parsed) if isinstance(parsed, (list, tuple)) else []
    except (KeyError, OSError, subprocess.CalledProcessError, plistlib.InvalidFileException, ValueError):
        pass
    try:
        raw_quarantine = read_xattr("com.apple.quarantine").decode("utf-8", errors="replace")
        parts = raw_quarantine.split(";")
        if len(parts) >= 3:
            result["quarantine_agent"] = parts[2] or None
        if len(parts) >= 2 and parts[1]:
            result["quarantine_timestamp"] = utc_iso(int(parts[1], 16))
    except (OSError, subprocess.CalledProcessError, ValueError):
        pass
    return result


def profile_csv(
    path: Path,
    global_rows: Counter[tuple[str, ...]],
    pair_levels: dict[tuple[str, str], set[str]],
    id_names: dict[str, set[str]],
    global_pairs: Counter[tuple[str, str]],
) -> dict[str, Any]:
    row_count = 0
    level_counts: Counter[str] = Counter()
    empty_counts: Counter[str] = Counter()
    file_rows: Counter[tuple[str, ...]] = Counter()
    self_pairs = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        for row in reader:
            row_count += 1
            values = tuple((row.get(column) or "").strip() for column in EXPECTED_COLUMNS)
            file_rows[values] += 1
            global_rows[values] += 1
            for column, value in zip(EXPECTED_COLUMNS, values):
                if not value:
                    empty_counts[column] += 1
            id_a, name_a, id_b, name_b, level_raw = values
            level = level_raw.lower()
            level_counts[level] += 1
            canonical_pair = tuple(sorted((id_a, id_b)))
            global_pairs[canonical_pair] += 1
            pair_levels[canonical_pair].add(level)
            if id_a == id_b:
                self_pairs += 1
            id_names[id_a].add(name_a)
            id_names[id_b].add(name_b)

    stat = path.stat()
    attrs = extended_attributes(path)
    return {
        "filename": path.name,
        "size_bytes": stat.st_size,
        "sha256": sha256_file(path),
        "filesystem_birth_time": utc_iso(stat.st_birthtime) if hasattr(stat, "st_birthtime") else None,
        "filesystem_modified_time": utc_iso(stat.st_mtime),
        "where_from_urls": attrs["where_from_urls"],
        "quarantine_agent": attrs["quarantine_agent"],
        "quarantine_timestamp": attrs["quarantine_timestamp"],
        "header": header,
        "header_matches_expected": header == EXPECTED_COLUMNS,
        "row_count": row_count,
        "severity_distribution": dict(sorted(level_counts.items())),
        "unknown_severity_rows": level_counts.get("unknown", 0),
        "unexpected_severity_rows": sum(
            count for level, count in level_counts.items() if level not in ALLOWED_LEVELS
        ),
        "empty_cell_counts": {column: empty_counts.get(column, 0) for column in EXPECTED_COLUMNS},
        "exact_duplicate_rows_within_file": sum(count - 1 for count in file_rows.values() if count > 1),
        "self_pair_rows": self_pairs,
    }


def git_inventory() -> dict[str, Any]:
    object_lines = git_output("rev-list", "--objects", "--all").splitlines()
    paths = [line.split(" ", 1)[1] for line in object_lines if " " in line]
    data_paths = sorted({path for path in paths if Path(path).suffix.lower() in DATA_EXTENSIONS})
    keyword_paths = sorted(
        {
            path
            for path in paths
            if any(keyword in path.lower() for keyword in ("ddinter", "quarantine", "import", "data_profile"))
        }
    )
    real_source_paths = sorted(path for path in paths if Path(path).name in EXPECTED_FILES)
    importer_history = git_output(
        "log",
        "--format=%H%x09%cI%x09%s",
        "--all",
        "--",
        "scripts/import_ddinter.py",
    ).splitlines()
    return {
        "reachable_ref_names": git_output("for-each-ref", "--format=%(refname)").splitlines(),
        "tags": git_output("tag", "--list").splitlines(),
        "historical_data_paths": data_paths,
        "historical_keyword_paths": keyword_paths,
        "real_source_files_in_git_history": real_source_paths,
        "importer_history": importer_history,
    }


def main() -> int:
    args = parse_args()
    source_dir = args.source_dir.resolve()
    missing_files = [name for name in EXPECTED_FILES if not (source_dir / name).is_file()]
    if missing_files:
        raise FileNotFoundError(f"Missing expected files: {', '.join(missing_files)}")

    global_rows: Counter[tuple[str, ...]] = Counter()
    global_pairs: Counter[tuple[str, str]] = Counter()
    pair_levels: dict[tuple[str, str], set[str]] = defaultdict(set)
    id_names: dict[str, set[str]] = defaultdict(set)
    files = [
        profile_csv(
            source_dir / name,
            global_rows,
            pair_levels,
            id_names,
            global_pairs,
        )
        for name in EXPECTED_FILES
    ]

    level_totals: Counter[str] = Counter()
    for file_profile in files:
        level_totals.update(file_profile["severity_distribution"])
    total_rows = sum(file_profile["row_count"] for file_profile in files)
    conflicting_id_names = {
        drug_id: sorted(names) for drug_id, names in id_names.items() if len(names) > 1
    }

    live_comparison: dict[str, Any] | None = None
    if args.live_verify_dir:
        live_dir = args.live_verify_dir.resolve()
        live_files = []
        for file_profile in files:
            live_path = live_dir / file_profile["filename"]
            live_hash = sha256_file(live_path) if live_path.is_file() else None
            live_files.append(
                {
                    "filename": file_profile["filename"],
                    "present": live_path.is_file(),
                    "sha256": live_hash,
                    "byte_identical": live_hash == file_profile["sha256"],
                }
            )
        live_comparison = {
            "retrieval_date": "2026-07-15",
            "files": live_files,
            "all_files_byte_identical": all(item["byte_identical"] for item in live_files),
        }

    profile_path = PROJECT_ROOT / "research/data_profile.json"
    committed_profile = json.loads(profile_path.read_text(encoding="utf-8"))
    git_data = git_inventory()
    acquisition_timestamps = [file_profile["quarantine_timestamp"] for file_profile in files]
    origin_coverage = all(
        any(url.startswith("https://ddinter.scbdd.com/") for url in file_profile["where_from_urls"])
        for file_profile in files
    )
    historical_data_paths = git_data["historical_data_paths"]
    historical_keyword_paths = git_data["historical_keyword_paths"]
    alias_snapshots = [
        path
        for path in historical_data_paths
        if "alias" in path.lower() or "drug_map" in path.lower()
    ]
    quarantine_artifacts = [
        path for path in historical_data_paths if "quarantine" in path.lower()
    ]
    import_logs = [
        path
        for path in historical_keyword_paths
        if "import" in path.lower() and Path(path).suffix.lower() in {".json", ".log", ".md", ".txt"}
    ]
    observable_checks = {
        "all_eight_source_files_present": not missing_files,
        "all_headers_match_expected": all(file_profile["header_matches_expected"] for file_profile in files),
        "all_source_sha256_computed": all(bool(file_profile["sha256"]) for file_profile in files),
        "official_origin_metadata_for_all_files": origin_coverage,
        "acquisition_timestamp_for_all_files": all(acquisition_timestamps),
        "all_source_files_byte_identical_to_2026_07_15_official_download": (
            live_comparison is not None and live_comparison["all_files_byte_identical"]
        ),
        "real_source_files_committed_in_git_history": bool(git_data["real_source_files_in_git_history"]),
        "exact_semantic_release_label_present_in_source_filenames_or_headers": False,
        "historical_alias_mapping_snapshot_present": bool(alias_snapshots),
        "persisted_quarantine_rows_present": bool(quarantine_artifacts),
        "complete_import_execution_log_present": bool(import_logs),
        "raw_to_database_accounting_reconstructable": bool(
            alias_snapshots and quarantine_artifacts and import_logs
        ),
    }
    full_provenance_passed = (
        observable_checks["all_eight_source_files_present"]
        and observable_checks["all_source_sha256_computed"]
        and observable_checks["official_origin_metadata_for_all_files"]
        and observable_checks["acquisition_timestamp_for_all_files"]
        and observable_checks["exact_semantic_release_label_present_in_source_filenames_or_headers"]
        and observable_checks["historical_alias_mapping_snapshot_present"]
        and observable_checks["persisted_quarantine_rows_present"]
        and observable_checks["complete_import_execution_log_present"]
        and observable_checks["raw_to_database_accounting_reconstructable"]
    )

    payload = {
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "repository_head_at_execution": git_output("rev-parse", "HEAD"),
            "evaluated_source_commit": git_output(
                "log",
                "-1",
                "--format=%H",
                "--",
                "scripts/import_ddinter.py",
                "research/data_profile.json",
                "research/profile_data.py",
            ),
            "platform": platform.platform(),
            "python": sys.version,
            "runner_sha256": sha256_file(SCRIPT_PATH),
            "database_connections": 0,
            "source_data_copied_into_repository": False,
        },
        "source_directory": str(source_dir),
        "files": files,
        "combined_profile": {
            "total_rows": total_rows,
            "unique_exact_rows": len(global_rows),
            "exact_duplicate_rows": sum(count - 1 for count in global_rows.values() if count > 1),
            "distinct_canonical_ddinter_id_pairs": len(global_pairs),
            "duplicate_pair_rows": sum(count - 1 for count in global_pairs.values() if count > 1),
            "pairs_with_multiple_severity_labels": sum(
                1 for levels in pair_levels.values() if len(levels) > 1
            ),
            "severity_distribution": dict(sorted(level_totals.items())),
            "unknown_severity_rows": level_totals.get("unknown", 0),
            "unexpected_severity_rows": sum(
                count for level, count in level_totals.items() if level not in ALLOWED_LEVELS
            ),
            "distinct_drug_ids": len(id_names),
            "drug_ids_with_multiple_names": len(conflicting_id_names),
            "conflicting_id_name_examples": dict(list(sorted(conflicting_id_names.items()))[:25]),
            "self_pair_rows": sum(file_profile["self_pair_rows"] for file_profile in files),
            "empty_cell_counts": {
                column: sum(file_profile["empty_cell_counts"][column] for file_profile in files)
                for column in EXPECTED_COLUMNS
            },
        },
        "live_official_comparison": live_comparison,
        "git_inventory": git_data,
        "lineage_artifact_candidates": {
            "alias_mapping_snapshots": alias_snapshots,
            "quarantine_artifacts": quarantine_artifacts,
            "import_logs": import_logs,
        },
        "committed_database_profile": {
            "path": "research/data_profile.json",
            "sha256": sha256_file(profile_path),
            "generated_at": committed_profile["generated_at"],
            "scope": committed_profile["scope"],
            "counts": committed_profile["counts"],
            "ddi_rows": committed_profile["ddi_rows"],
            "ddinter_assertions": committed_profile["source_distribution_by_assertion"].get("DDInter"),
            "profile_limitations": committed_profile["ddinter_import"]["limitations"],
        },
        "observable_checks": observable_checks,
        "full_provenance_passed": full_provenance_passed,
        "interpretation_guardrails": [
            "Raw source rows cannot be subtracted from database assertions and labeled quarantine rows without the historical alias map and import log.",
            "Filesystem/download metadata does not provide a semantic DDInter release identifier.",
            "Byte identity with the current official download establishes file identity, not clinical completeness or validity.",
            "The committed database profile contains research fixtures and is not a source-release manifest.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"files={len(files)}; raw_rows={total_rows}; exact_duplicates="
        f"{payload['combined_profile']['exact_duplicate_rows']}; live_identical="
        f"{live_comparison['all_files_byte_identical'] if live_comparison else 'not_checked'}; "
        f"semantic_release_recorded={observable_checks['exact_semantic_release_label_present_in_source_filenames_or_headers']}; "
        f"raw_to_db_accounting={observable_checks['raw_to_database_accounting_reconstructable']}; "
        f"full_provenance_passed={full_provenance_passed}"
    )
    return 0 if full_provenance_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
