# Results: LLM Response-Validator Conformance Audit

## Prespecified decision

**FAIL.** The audit script executed successfully and produced complete evidence, but the implementation failed the validator contract and exited with status 1 as designed.

## Execution context

- Execution date: July 15, 2026 UTC.
- Repository HEAD: `db6cd9899b575e0f4a169da4db6b6631a8b2d9b2`.
- Most recent commit affecting the evaluated LLM service/schema paths: `40965a8d53969bc2e5daa12d8cb61193a0da70c2`.
- Python: 3.12.13.
- Pydantic: 2.13.4.
- SQLAlchemy: 2.0.51.
- Fixture SHA-256: `cf294945f0d7349a76c454c24be6f1ae5cd127cd53fae206b0cb09313c3feb7f`.
- Runner SHA-256: `4eb12b6c25a67bd2d906d6ee48f3978a75416137fb2ab6417536f326c783f128`.
- External API calls: 0.
- Database connections: 0.

## Aggregate metrics

| Metric | Count | Rate |
|---|---:|---:|
| Expected-valid cases accepted | 3/3 | 100.0% |
| Expected-invalid cases controlled-rejected | 5/27 | 18.5% |
| Expected-invalid cases falsely accepted | 15/27 | 55.6% |
| Expected-invalid cases with unhandled exception | 7/27 | 25.9% |
| False rejects | 0/3 | 0.0% |
| All expectations met | 8/30 | 26.7% |

These are deterministic conformance-suite proportions, not estimates of how often a live model will produce each defect.

## Case-level outcomes

### Valid controls accepted

| Case | Observed |
|---|---|
| `valid_minimal_object` | Accepted |
| `valid_fenced_object` | Accepted |
| `valid_both_allowed_sources` | Accepted |

### Invalid cases cleanly rejected

| Case | Rejection evidence |
|---|---|
| `malformed_json` | JSON parse error |
| `leading_prose` | JSON parse error at first character |
| `missing_management` | Missing-key error |
| `sources_is_string` | `sources_used must be a list` |
| `known_unexpected_drug` | Stored-name scan detected Warfarin |

### Invalid cases falsely accepted

| Case | Unenforced contract dimension |
|---|---|
| `trailing_prose` | Full input consumption |
| `second_json_object` | Full input consumption / single object |
| `duplicate_summary_key` | Duplicate-key ambiguity |
| `extra_top_level_key` | Exact schema / additional fields |
| `empty_required_strings` | Non-empty value constraints |
| `invalid_confidence_vocabulary` | Confidence enumeration |
| `wrong_severity` | Stored-severity preservation |
| `invented_source` | Allowed-source consistency |
| `empty_sources` | Source completeness/non-empty constraint |
| `unknown_unexpected_drug` | Drug-name detection limited to stored names |
| `unexpected_food` | Non-drug party/factor consistency |
| `unsupported_specific_dose` | Unsupported dosing instruction |
| `unsupported_new_mechanism` | Semantic grounding |
| `prompt_injection_instruction` | Injection-shaped output detection |
| `fence_with_trailing_text` | Full input consumption after fence handling |

### Invalid cases producing unhandled exceptions

| Case | Exception | Interpretation |
|---|---|---|
| `top_level_array` | `AttributeError` | Parser assumes `.keys()` exists |
| `top_level_null` | `AttributeError` | Parser assumes `.keys()` exists |
| `summary_is_number` | Pydantic `ValidationError` | Custom parser does not check text-field type |
| `mechanism_is_object` | Pydantic `ValidationError` | Custom parser does not check text-field type |
| `clinical_effect_is_array` | Pydantic `ValidationError` | Custom parser does not check text-field type |
| `sources_contains_number` | Pydantic `ValidationError` | Parser checks list container but not element types |
| `confidence_is_number` | Pydantic `ValidationError` | Custom parser does not check confidence type |

## Category performance

| Category | Expectations met | Total | False accepts | Unhandled exceptions |
|---|---:|---:|---:|---:|
| Valid controls | 3 | 3 | 0 | 0 |
| Structure | 3 | 10 | 5 | 2 |
| Type | 1 | 6 | 0 | 5 |
| Value constraints | 0 | 3 | 3 | 0 |
| Consistency | 0 | 2 | 2 | 0 |
| Drug consistency | 1 | 3 | 2 | 0 |
| Grounding | 0 | 2 | 2 | 0 |
| Injection | 0 | 1 | 1 | 0 |

## Code-path interpretation

The parser calls `JSONDecoder.raw_decode()` but ignores the returned end position, explaining acceptance of trailing prose and a second object. It immediately calls `payload.keys()` without verifying an object type, explaining the two `AttributeError` cases. It checks only required-key presence and the outer list type of `sources_used`.

Wrong primitive/container types reach `_build_result_from_payload()`, where the Pydantic response model raises. Code inspection shows that `generate_explanation()` computes `schema_validation_passed`, persists the explanation, commits, and only then calls `_build_result_from_payload()`. The audit directly confirms the builder exceptions; persistence-before-error is an inference from the inspected call order and was not separately database-tested here.

The stored-name scan correctly detects Warfarin because the stubbed database result includes it. It cannot detect Fictivex because the algorithm searches only names already stored in the database, and it does not inspect foods, conditions, sources, severity, management support, or injection patterns.

## Claim-level conclusion

Supported wording:

> The current explanation path applies custom JSON parsing, checks for seven required keys, verifies that `sources_used` is a list, and scans the raw response for stored non-party drug names.

Unsupported wording:

- Strict or typed schema validation.
- Source or severity consistency validation.
- Semantic grounding validation.
- Comprehensive drug/factor hallucination detection.
- Unsupported-dose or management rejection.
- Prompt-injection resistance.
- Safe or clinically reliable generated explanations.

The structural rule that an explanation requires an existing finding remains separately supported; this audit concerns output content enforcement after that boundary.
