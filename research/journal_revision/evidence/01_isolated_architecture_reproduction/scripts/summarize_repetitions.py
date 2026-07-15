#!/usr/bin/env python3
"""Aggregate isolated reproduction runs without discarding scenario detail."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = sorted(args.input_dir.glob("run_*.json"))
    if not paths:
        raise RuntimeError("No run_*.json files found.")

    runs = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    scenario_maps = [
        {item["name"]: item["passed"] for item in run["evaluation"]["scenarios"]}
        for run in runs
    ]
    reference = scenario_maps[0]
    agreement = all(mapping == reference for mapping in scenario_maps[1:])
    all_assertions_passed = all(
        all(run["reproduction_assertions"].values()) for run in runs
    )
    summaries = [run["evaluation"]["summary"] for run in runs]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run_count": len(runs),
        "run_files": [path.name for path in paths],
        "scenario_outcome_agreement": agreement,
        "all_reproduction_assertions_passed": all_assertions_passed,
        "all_runs_26_of_26": all(
            summary == {"total_scenarios": 26, "passed": 26, "failed": 0}
            for summary in summaries
        ),
        "summaries": summaries,
        "wall_duration_seconds": [
            run["reproduction_metadata"]["wall_duration_seconds"] for run in runs
        ],
        "scenario_outcomes": reference,
    }
    args.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    passed = (
        len(runs) == 3
        and payload["scenario_outcome_agreement"]
        and payload["all_reproduction_assertions_passed"]
        and payload["all_runs_26_of_26"]
    )
    print(
        f"repetitions={len(runs)}; all_runs_26_of_26={payload['all_runs_26_of_26']}; "
        f"scenario_outcome_agreement={agreement}; pass={passed}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
