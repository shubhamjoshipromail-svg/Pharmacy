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
| Evidence 03 | Partial; full lineage failed | 2026-07-15 | Recover DDInter source provenance and reconcile data claims | Eight official files found and hashed; all byte-identical to current downloads; 222,383 rows, 160,235 unique, 62,148 duplicates; no semantic release or reconstructable import accounting | Data provenance, database counts, DDInter version/coverage, data availability | Data/Implementation Context, Methods, Results, Limitations, Availability | Missing alias snapshot, quarantine rows, import log, semantic release, database row-level reconciliation | Benchmark core-check latency/repeatability in the isolated synthetic environment; list independent clinical/reference validation as externally blocked |
| Evidence 04 | Complete; pass with limitations | 2026-07-15 | Benchmark core-check latency and repeatability | 720/720 count-correct calls; 0 exceptions/external calls; 8/8 workloads met local p95 and repeatability rules; p95 2.586–245.124 ms | Bounded operational behavior of the deterministic DDI path | Methods, Results, Threats to Validity, Discussion | One machine; synthetic warm-cache sequential core calls; no end-to-end, concurrency, real-data, or clinical inference | Audit selected persistence/traceability semantics before final claim classification |

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

## Evidence 03 execution record

- Files: `research/journal_revision/evidence/03_ddinter_provenance_recovery/`.
- Command:

```bash
/tmp/rxcheck-evidence-venv/bin/python \
research/journal_revision/evidence/03_ddinter_provenance_recovery/scripts/audit_ddinter_provenance.py \
  --source-dir /Users/shubhamjoshi/Desktop/pharmacy/ddinter \
  --live-verify-dir /tmp/ddinter-live-verify-20260715 \
  --output research/journal_revision/evidence/03_ddinter_provenance_recovery/raw_results/provenance_inventory.json
```

- Pass/fail: PARTIAL / full-provenance FAIL (runner exit 1 by prespecified criterion).
- Files created: protocol, streaming audit script, manifest, raw JSON, HTTP metadata, verification logs, results, limitations, and manuscript notes.
- Claim impact: source-file identity/acquisition/hashes are now supported; semantic release and database transformation counts remain unsupported.
- Residual risk: source CSVs remain external to Git; license review and a fresh manifest-driven reimport are still required.

## Evidence 04 execution record

- Files: `research/journal_revision/evidence/04_core_latency_repeatability/`.
- Command:

```bash
PG_BIN=/tmp/rxcheck-pg16.14/install/bin \
PYTHON_BIN=/tmp/rxcheck-evidence-venv/bin/python \
bash research/journal_revision/evidence/04_core_latency_repeatability/scripts/run_benchmark.sh
```

- Pass/fail: PASS WITH LIMITATIONS.
- Files created: protocol, guarded Python runner, disposable-cluster shell runner, 720-row CSV, results JSON, environment lock, execution/server logs, results, limitations, and manuscript notes.
- Claim impact: permits a bounded single-machine warm-cache latency/repeatability result; does not permit production, scalability, end-to-end, or clinical-performance claims.
- Original-file check: original manuscript hash unchanged; no application source or historical research file modified.
- Residual risk: one environment, synthetic topology, no concurrency, and model-metadata schema setup.

## Current selection rationale

The next highest-value feasible task is a narrow persistence and traceability semantics audit. The reviews specifically question whether attempted checks, pair counts, sources, acknowledgments, overrides, and evidence snapshots mean what the paper implies. This can be tested without external clinical resources and may support or require narrowing the auditability contribution. A genuinely independent clinical/reference benchmark remains externally blocked.
