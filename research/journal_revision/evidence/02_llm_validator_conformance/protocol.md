# Protocol: LLM Response-Validator Conformance Audit

## Research question

Does the implemented RxCheck LLM response-validation pipeline reliably accept contract-conforming outputs and cleanly reject malformed, mistyped, internally inconsistent, ungrounded, or adversarial outputs before they are returned as validated explanations?

## Why this task is publication-relevant

The claim–evidence audit found that the manuscript's “schema-validated” wording exceeds the implementation. The journal review and remaining-author-actions checklist specifically call for malformed/non-object JSON, wrong-drug, wrong-severity, invented-source, unsupported-management, and prompt-injection cases. Explanation is central to the proposed architecture, while the actual automated boundary has not been measured.

## Objective

Execute a frozen, machine-readable conformance suite against the unchanged private functions used by `generate_explanation()`:

- `app.services.llm._parse_explanation_payload`
- `app.services.llm._validate_drug_mentions`
- `app.services.llm._build_result_from_payload`

The audit measures automated enforcement only. It does not call an LLM or score clinical correctness.

## Expected behavior and contract

A conforming response must:

1. Contain one complete JSON object and no leading/trailing non-whitespace content.
2. Contain exactly the seven requested keys: `summary`, `mechanism`, `clinical_effect`, `management`, `severity_rationale`, `sources_used`, and `confidence`.
3. Use non-empty strings for the six textual fields other than `sources_used`.
4. Use a non-empty list of non-empty source-name strings for `sources_used`.
5. Limit sources to those supplied in the structured context (`DDInter` and `OpenFDA` in the fixture contract).
6. Limit confidence to `high`, `medium`, or `low`.
7. Preserve the supplied `major` severity.
8. Refer only to the supplied interaction parties, Aspirin and Clopidogrel.
9. Avoid adding a food/condition, unsupported mechanism/effect, specific dose, or prescribing decision not present in the fixture context.
10. Avoid reproducing or following prompt-injection-shaped instructions.

This is a test contract derived from the prompt, rubric, and manuscript claims. It is intentionally stronger than the current implementation so that enforcement gaps become measurable.

## Frozen fixtures

`fixtures/validator_cases.json` defines:

- The base valid payload.
- Allowed parties, sources, severity, and known stored drug names.
- Three expected-valid controls.
- Twenty-seven expected-invalid structural, type, consistency, grounding, and adversarial cases.

The runner records the fixture SHA-256 in the raw result.

## Execution design

1. Load and hash the fixture file before importing the validator functions.
2. Materialize each case deterministically from the base payload and declared mutation.
3. Call the actual parser and capture either its payload/errors or its exception.
4. If parsing does not reject the output, call the actual drug-name check using a deterministic session stub whose stored non-placeholder drug names are Aspirin, Clopidogrel, and Warfarin.
5. If no parser/name errors exist, call the actual Pydantic response-building path with a synthetic explanation record.
6. Classify the observed outcome as:
   - `accepted`
   - `controlled_rejection`
   - `unhandled_exception`
7. Compare the observed outcome with the prespecified expected outcome.
8. Save case-level raw text, errors, exception information, source/script hashes, environment metadata, and aggregate/category metrics.

The session stub only supplies the return value of the stored-drug-name query; the real SQLAlchemy query expression and production name-scanning code still execute. No database or external network call is needed.

## Metrics

- Valid-control acceptance: accepted expected-valid cases / expected-valid cases.
- Invalid-case controlled-rejection sensitivity: controlled rejections / expected-invalid cases.
- False accepts: expected-invalid cases classified `accepted`.
- Unhandled exceptions: cases that escape controlled validation.
- False rejects: expected-valid cases not accepted.
- Overall conformance: cases matching expected outcome / all cases.
- Results by case category.

## Pass/fail criteria

The implemented validator passes only if:

1. All three valid controls are accepted.
2. All 27 invalid/adversarial cases are controlled rejections.
3. No invalid case is accepted.
4. No case produces an unhandled exception.
5. No external API or database call occurs.

Otherwise, the validator-conformance result is **FAIL**, even if the audit script itself executes correctly.

## Reproduction command

```bash
PYTHON_BIN=/path/to/python \
"$PYTHON_BIN" research/journal_revision/evidence/02_llm_validator_conformance/scripts/run_validator_audit.py \
  --fixtures research/journal_revision/evidence/02_llm_validator_conformance/fixtures/validator_cases.json \
  --output research/journal_revision/evidence/02_llm_validator_conformance/raw_results/validator_results.json
```

No API call is made; a configured key, if present in the environment, is not sent to any provider.

## Prespecified limitations

- Expected outcomes are specified by the project review, not an external standards body.
- The suite measures automated response enforcement, not model behavior or clinical truth.
- Grounding probes are deliberately obvious sentinels; passing them would not prove semantic grounding.
- The drug-name session stub contains a finite known-name list, mirroring the production validator's database-dependent design.
- Prompt-injection probes do not establish comprehensive security.
