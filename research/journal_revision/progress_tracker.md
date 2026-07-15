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
| Preparation | Complete locally; push blocked | 2026-07-14 | Preserve the six-file journal-readiness review package | Local commit `63fb4c0`; HTTPS push failed because no GitHub credentials were available in the shell | Establishes the review baseline | Author-facing planning materials | Remote branch does not yet contain the commit | Push when an authenticated GitHub path is available |
| Evidence 01 | Complete | 2026-07-15 | Reproduce the 26-scenario architecture evaluation from fresh local PostgreSQL databases | Three repetitions passed 26/26; identical outcomes; no external APIs reported | Clean-database architecture reproducibility and deterministic/generative boundary | Methods, Results, Threats to Validity, Data/Code Availability | Self-authored synthetic scenarios; empty migration; unpinned dependencies; no real data reconstruction | Audit the LLM output-validation boundary with malformed and adversarial structured outputs |

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

## Current selection rationale

The next highest-value feasible task is a structured-output and failure-mode audit of the actual LLM parser/validator. It directly tests a central article component, requires no clinical data or paid model call, and can reveal whether the manuscript's “bounded explanation” language is technically proportional to the implementation.
