# Publication-Readiness Progress Tracker

## Scope and safeguards

- Working branch: `research/journal-ready-paper`.
- Original manuscript: `paper/rxcheck_manuscript_0.1v.md`.
- Original manuscript Git object hash: `cd5c4ab332461544a1f083bfcfd65fd60b2b49e4`.
- Evidence root: `research/journal_revision/evidence/`.
- Original paper, application code, historical research files, and numbered review package are treated as read-only.

## Completed work

| ID | Status | Date | Task | Result | Claim affected | Manuscript section | Residual risk | Recommended next action |
|---|---|---|---|---|---|---|---|---|
| Preparation | Complete and pushed | 2026-07-14 | Preserve the six-file journal-readiness review package | Commit `63fb4c0` on the remote research branch | Establishes the review baseline | Author-facing planning materials | Review conclusions still require executed evidence | Execute the highest-priority reproducibility task |
| Evidence 01 | Complete and pushed | 2026-07-15 | Reproduce the 26-scenario architecture evaluation from fresh local PostgreSQL databases | Commit `db6cd98`; three repetitions passed 26/26; identical outcomes; no external APIs reported | Clean-database architecture reproducibility and deterministic/generative boundary | Methods, Results, Threats to Validity, Data/Code Availability | Self-authored synthetic scenarios; empty migration; unpinned dependencies; no real data reconstruction | Audit the LLM output-validation boundary with malformed and adversarial structured outputs |
| Evidence 02 | Complete; implementation failed contract | 2026-07-15 | Audit LLM response-validator conformance | 3/3 valid controls accepted; only 5/27 invalid cases cleanly rejected; 15 false accepts; 7 unhandled exceptions | Schema validation, source/severity consistency, grounding, hallucination resistance, prompt-injection handling | Methods, Results, Discussion, Limitations, Future Work | No live model/clinical assessment; finite project-defined cases; no remediation tested | Recover source-data provenance from repository/history, then decide whether a credible independent validation set is feasible |

## Evidence 01 execution record

- Files: `research/journal_revision/evidence/01_isolated_architecture_reproduction/`.
- Command:

```bash
PG_BIN=/tmp/rxcheck-pg16.14/install/bin \
PYTHON_BIN=/tmp/rxcheck-evidence-venv/bin/python \
bash research/journal_revision/evidence/01_isolated_architecture_reproduction/scripts/run_repetitions.sh
```

- Pass/fail: PASS.
- Original-file check: original manuscript hash unchanged; no diff in historical evaluation JSON/Markdown.
- Temporary-data check: disposable cluster stopped and removed.
- Publication implication: the 26/26 result is now locally reproduced, but neither clinically validated nor independently reproduced.

## Evidence 02 execution record

- Files: `research/journal_revision/evidence/02_llm_validator_conformance/`.
- Command:

```bash
/tmp/rxcheck-evidence-venv/bin/python \
research/journal_revision/evidence/02_llm_validator_conformance/scripts/run_validator_audit.py \
  --fixtures research/journal_revision/evidence/02_llm_validator_conformance/fixtures/validator_cases.json \
  --output research/journal_revision/evidence/02_llm_validator_conformance/raw_results/validator_results.json
```

- Pass/fail: FAIL (runner exit 1 by prespecified contract).
- Claim impact: keep the finding-authority boundary; remove or explicitly negate strong output-validation/grounding claims.
- Residual action: do not treat live generated prose as validated until a remediated implementation passes the suite and receives appropriate human review.

## Current selection rationale

The next highest-value feasible task is recovery-oriented source-data provenance auditing. Exact DDInter release/files/checksums and import accounting remain submission-critical, and repository/history inspection can determine what is recoverable now versus what requires author-supplied source files.
