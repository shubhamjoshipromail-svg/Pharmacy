#!/usr/bin/env python3
"""Audit RxCheck's unchanged LLM response validator against frozen cases."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[5]


class ScalarResultStub:
    def __init__(self, values: list[str]) -> None:
        self._values = values

    def all(self) -> list[str]:
        return list(self._values)


class SessionStub:
    def __init__(self, known_drug_names: list[str]) -> None:
        self._known_drug_names = known_drug_names
        self.scalar_queries = 0

    def scalars(self, _statement: Any) -> ScalarResultStub:
        self.scalar_queries += 1
        return ScalarResultStub(self._known_drug_names)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, required=True)
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


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def materialize_raw_text(base_payload: dict[str, Any], case: dict[str, Any]) -> str:
    if "raw_text_override" in case:
        return case["raw_text_override"]
    if "raw_json_value" in case:
        value: Any = case["raw_json_value"]
    else:
        value = copy.deepcopy(base_payload)
        value.update(copy.deepcopy(case.get("payload_patch", {})))
        for key in case.get("remove_keys", []):
            value.pop(key, None)
    raw_text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if case.get("code_fence"):
        raw_text = f"```json\n{raw_text}\n```"
    return f"{case.get('prefix_text', '')}{raw_text}{case.get('suffix_text', '')}"


def audit_case(
    case: dict[str, Any],
    raw_text: str,
    interaction: Any,
    db: SessionStub,
    parse_payload: Any,
    validate_drugs: Any,
    build_result: Any,
) -> dict[str, Any]:
    parser_errors: list[str] = []
    drug_errors: list[str] = []
    parsed_payload: Any = None
    exception: dict[str, str] | None = None
    built_result: dict[str, Any] | None = None

    try:
        parsed_payload, parser_errors = parse_payload(raw_text)
        drug_errors = validate_drugs(raw_text, interaction, db)
        if parsed_payload is None or parser_errors or drug_errors:
            observed_outcome = "controlled_rejection"
        else:
            explanation = SimpleNamespace(
                id=f"fixture-{case['id']}",
                schema_validation_passed=True,
                validation_errors=None,
            )
            result = build_result(explanation, parsed_payload)
            built_result = result.model_dump(mode="json")
            observed_outcome = "accepted"
    except Exception as exc:  # The exception type is an explicit audit outcome.
        observed_outcome = "unhandled_exception"
        exception = {"type": type(exc).__name__, "message": str(exc)}

    expected_outcome = case["expected_outcome"]
    expectation_met = (
        observed_outcome == "accepted"
        if expected_outcome == "accept"
        else observed_outcome == "controlled_rejection"
    )
    return {
        "id": case["id"],
        "category": case["category"],
        "description": case["description"],
        "expected_outcome": expected_outcome,
        "observed_outcome": observed_outcome,
        "expectation_met": expectation_met,
        "false_accept": expected_outcome == "reject" and observed_outcome == "accepted",
        "false_reject": expected_outcome == "accept" and observed_outcome != "accepted",
        "unhandled_exception": observed_outcome == "unhandled_exception",
        "raw_text": raw_text,
        "parsed_payload": parsed_payload,
        "parser_errors": parser_errors,
        "drug_mention_errors": drug_errors,
        "exception": exception,
        "built_result": built_result,
    }


def main() -> int:
    args = parse_args()
    fixtures_path = args.fixtures.resolve()
    fixture_sha256 = sha256_file(fixtures_path)
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from app.services.llm import (
        _build_result_from_payload,
        _parse_explanation_payload,
        _validate_drug_mentions,
    )

    contract = fixtures["contract"]
    interaction = SimpleNamespace(
        drug_a=SimpleNamespace(preferred_name=contract["allowed_drugs"][0]),
        drug_b=SimpleNamespace(preferred_name=contract["allowed_drugs"][1]),
    )
    db = SessionStub(contract["known_database_drugs"])
    case_results = []
    for case in fixtures["cases"]:
        raw_text = materialize_raw_text(fixtures["base_payload"], case)
        case_results.append(
            audit_case(
                case,
                raw_text,
                interaction,
                db,
                _parse_explanation_payload,
                _validate_drug_mentions,
                _build_result_from_payload,
            )
        )

    observed_counts = Counter(result["observed_outcome"] for result in case_results)
    category_data: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in case_results:
        category_data[result["category"]].append(result)
    category_summary = {
        category: {
            "total": len(results),
            "expectations_met": sum(result["expectation_met"] for result in results),
            "false_accepts": sum(result["false_accept"] for result in results),
            "unhandled_exceptions": sum(result["unhandled_exception"] for result in results),
        }
        for category, results in sorted(category_data.items())
    }

    expected_valid = [result for result in case_results if result["expected_outcome"] == "accept"]
    expected_invalid = [result for result in case_results if result["expected_outcome"] == "reject"]
    false_accepts = [result["id"] for result in case_results if result["false_accept"]]
    false_rejects = [result["id"] for result in case_results if result["false_reject"]]
    exceptions = [result["id"] for result in case_results if result["unhandled_exception"]]
    summary = {
        "total_cases": len(case_results),
        "expected_valid_cases": len(expected_valid),
        "expected_invalid_cases": len(expected_invalid),
        "valid_controls_accepted": sum(result["observed_outcome"] == "accepted" for result in expected_valid),
        "invalid_cases_controlled_rejected": sum(
            result["observed_outcome"] == "controlled_rejection" for result in expected_invalid
        ),
        "false_accept_count": len(false_accepts),
        "false_accept_case_ids": false_accepts,
        "false_reject_count": len(false_rejects),
        "false_reject_case_ids": false_rejects,
        "unhandled_exception_count": len(exceptions),
        "unhandled_exception_case_ids": exceptions,
        "expectations_met": sum(result["expectation_met"] for result in case_results),
        "overall_conformance_rate": round(
            sum(result["expectation_met"] for result in case_results) / len(case_results), 6
        ),
        "observed_outcomes": dict(sorted(observed_counts.items())),
    }
    summary["validator_contract_passed"] = (
        summary["valid_controls_accepted"] == len(expected_valid)
        and summary["invalid_cases_controlled_rejected"] == len(expected_invalid)
        and summary["false_accept_count"] == 0
        and summary["false_reject_count"] == 0
        and summary["unhandled_exception_count"] == 0
    )

    source_paths = [
        "app/services/llm.py",
        "app/schemas/interaction.py",
        "research/explanation_quality_rubric.md",
        "research/explanation_eval_template.md",
    ]
    payload = {
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "repository_head_at_execution": git_output("rev-parse", "HEAD"),
            "evaluated_source_commit": git_output(
                "log", "-1", "--format=%H", "--", "app/services/llm.py", "app/schemas/interaction.py"
            ),
            "fixture_version": fixtures["fixture_version"],
            "fixture_sha256": fixture_sha256,
            "runner_sha256": sha256_file(SCRIPT_PATH),
            "source_sha256": {
                path: sha256_file(PROJECT_ROOT / path) for path in source_paths
            },
            "environment": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "python": sys.version,
                "anthropic": package_version("anthropic"),
                "pydantic": package_version("pydantic"),
                "sqlalchemy": package_version("sqlalchemy"),
            },
            "external_api_calls": 0,
            "database_connections": 0,
            "stubbed_drug_name_queries": db.scalar_queries,
        },
        "contract": contract,
        "summary": summary,
        "category_summary": category_summary,
        "cases": case_results,
        "limitations": [
            "This is an automated validator-conformance audit, not a live-model or clinical evaluation.",
            "Expected outcomes reflect the prompt, rubric, and review contract rather than an external standard.",
            "Grounding and prompt-injection probes are finite and deliberately obvious.",
            "The stored-drug-name query result is stubbed; the production name-scanning function is unchanged.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"cases={summary['total_cases']}; valid_accepted={summary['valid_controls_accepted']}/"
        f"{summary['expected_valid_cases']}; invalid_controlled_rejected="
        f"{summary['invalid_cases_controlled_rejected']}/{summary['expected_invalid_cases']}; "
        f"false_accepts={summary['false_accept_count']}; exceptions="
        f"{summary['unhandled_exception_count']}; contract_passed="
        f"{summary['validator_contract_passed']}"
    )
    return 0 if summary["validator_contract_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
