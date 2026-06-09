# Pytest Result Summary

Run date: June 9, 2026

Environment:

- Fresh virtual environment: `/private/tmp/rxcheck-research-venv`
- Python: 3.13.5
- Dependencies installed from `requirements.txt`
- Command: `/private/tmp/rxcheck-research-venv/bin/pytest -q`

## Result

```text
3 passed, 3 warnings in 4.96s
```

Tests executed:

- `tests/test_health.py::test_health_check`
- `tests/test_interaction_summary.py::test_build_summary_uses_max_severity_and_marks_source_conflict`
- `tests/test_interaction_summary.py::test_build_summary_uses_condition_name_for_ddsi`

## Warnings

The run produced three deprecation warnings:

1. Starlette reported that its current `TestClient` integration with `httpx` is deprecated.
2. FastAPI reported that `@app.on_event("startup")` is deprecated in favor of lifespan event handlers.
3. FastAPI emitted the corresponding router-level startup-event deprecation warning.

These warnings did not fail the tests and do not change the formative evaluation result. They identify future maintenance work rather than evidence of clinical or architectural correctness.

## Interpretation

The test suite confirms:

- The FastAPI health endpoint imports and returns its expected response.
- Interaction summary construction selects the highest source severity.
- Conflicting source severities set `sources_conflict=true`.
- DDI summary output includes drug names and hub scores.
- DDSI summary output uses the associated condition name.

The test suite does not establish:

- Clinical validity.
- Interaction-source completeness.
- RxNorm accuracy.
- OpenFDA availability.
- LLM factual accuracy.
- Authentication, privacy, or regulatory compliance.
- Full orchestrator correctness beyond the separate formative evaluation script.
