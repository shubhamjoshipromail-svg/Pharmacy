# Evidence 02: LLM Response-Validator Conformance

## Status

**FAIL — the implemented validator did not meet the prespecified contract.**

On July 15, 2026 UTC, 30 frozen response fixtures were executed against the unchanged parser, stored-drug-name check, and Pydantic response-building functions used by the RxCheck explanation path. All 3 valid controls were accepted. Of 27 invalid/adversarial cases, only 5 were cleanly rejected, 15 were falsely accepted, and 7 produced unhandled exceptions.

## Why this task was selected

The claim audit found that “schema-validated” overstated the custom checks. The journal review identified missing evaluation of malformed JSON, field types, severity/source preservation, invented drug names, unsupported management, and prompt injection. This audit directly tests that high-risk boundary without using clinical data or paying for a model call.

## Method in brief

- Frozen fixture version: 1.0.
- Cases: 3 expected-valid and 27 expected-invalid.
- Actual functions exercised:
  - `_parse_explanation_payload`
  - `_validate_drug_mentions`
  - `_build_result_from_payload`
- Known stored names supplied to the unchanged name scan: Aspirin, Clopidogrel, Warfarin.
- Allowed interaction parties: Aspirin and Clopidogrel.
- Allowed context sources: DDInter and OpenFDA.
- Expected stored severity: major.
- External API calls: 0.
- Database connections: 0.

The database query result was supplied by a deterministic session stub; the production SQLAlchemy query expression and name-scanning logic executed unchanged.

## Main result

| Metric | Result |
|---|---:|
| Valid controls accepted | 3/3 (100%) |
| Invalid cases cleanly rejected | 5/27 (18.5%) |
| Invalid cases falsely accepted | 15/27 (55.6%) |
| Invalid cases causing unhandled exceptions | 7/27 (25.9%) |
| All case expectations met | 8/30 (26.7%) |
| Validator contract | **Failed** |

## What the validator rejected

- Malformed JSON.
- Leading prose before JSON.
- A missing `management` key.
- `sources_used` supplied as a string rather than a list.
- A reference to Warfarin, which appeared in the supplied stored-drug-name list but was not an interaction party.

## What it falsely accepted

The implementation accepted 15 outputs that violated the prespecified prompt/rubric contract, including trailing text or a second object, duplicate and extra keys, empty required values, invalid confidence vocabulary, severity downgrade, invented/empty sources, an unknown fabricated drug, an unexpected food, unsupported dose/mechanism text, and prompt-injection-shaped instructions.

## What crashed

Top-level array/null values caused `AttributeError` at the parser's `.keys()` call. Five wrong-type payloads passed the custom parser and reached the Pydantic response model, which raised `ValidationError` rather than producing a controlled validation failure.

## Conclusion

The application supports only the narrower statement that it performs custom JSON parsing, required-key checks, a list check for `sources_used`, and a database-dependent stored-drug-name scan. The current result does not support claims of strict schema validation, source/severity consistency enforcement, hallucination resistance, semantic grounding, or prompt-injection resistance.

This negative result does not overturn Evidence 01's finding-authority boundary: the LLM remains downstream of an existing persisted interaction finding. It does show that prose returned within that downstream layer is not adequately bounded by the implemented automated validator.

## Evidence map

- `protocol.md` — frozen contract, cases, metrics, and pass/fail rule.
- `fixtures/validator_cases.json` — all case specifications and base payload.
- `scripts/run_validator_audit.py` — deterministic runner.
- `raw_results/validator_results.json` — complete raw text, parsed payloads, errors, exceptions, hashes, and metrics.
- `raw_results/environment_lock.txt` — exact resolved Python environment.
- `logs/execution.log` — console summary and nonzero contract-test exit.
- `results.md` — audited case-level findings.
- `limitations.md` — scope and interpretation constraints.
- `manuscript_notes.md` — required manuscript changes.
