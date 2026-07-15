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
| Evidence 04 | Complete and pushed | 2026-07-15 | Benchmark core-check latency and repeatability | Commit `285167e`; 720/720 count-correct calls; 0 exceptions/external calls; 8/8 workloads met local p95 and repeatability rules; p95 2.586–245.124 ms | Bounded operational behavior of the deterministic DDI path | Methods, Results, Threats to Validity, Discussion | One machine; synthetic warm-cache sequential core calls; no end-to-end, concurrency, real-data, or clinical inference | Audit selected persistence/traceability semantics before final claim classification |
| Evidence 05 | Complete and pushed; broad contract failed | 2026-07-15 | Audit selected persistence and traceability semantics | Commit `6d2d120`; 10/15 criteria passed; failures in insufficient-attempt history, duplicate pair count, run source reporting, prior-display reconstruction, and removal-event actor attribution | Audit-oriented persistence, workflow history, provenance snapshots, pair metrics, identity | Architecture/Methods, Results, Discussion, Limitations, Security/Governance | Direct synthetic function-level audit; no auth/read/tamper/concurrency/compliance assessment | Build an independently specified normalization benchmark if a non-circular reference axis is feasible |
| Evidence 06 | Complete; strict benchmark failed | 2026-07-15 | Benchmark medication normalization against frozen official-reference mappings | References 30/30 verified; application 22/30 strict passes; failures: 2 misspelling/status, 4 combinations, 1 constructed unknown, 1 injected outage | Ingredient-level normalization, explicit non-resolution, combination products, NDCs, failure handling | Methods, Results, Discussion, Limitations, Future Work | Purposive small set; shared RxNorm vocabulary; no expert adjudication or population estimate | Stop empirical expansion; verify related-work/citation support, then perform consolidated evidence review |
| Evidence 07 | Complete; broad novelty narrowed | 2026-07-14 | Verify all citations and compare the closest related work | 15/15 reference identities verified; 9 direct and 6 bounded/context-only uses; 6/6 comparison categories covered; prior DDI explanation and hybrid rule-plus-LLM work preclude broad novelty | Citation accuracy, RAG/LLM framing, DDI explanation novelty, provenance positioning, clinical-outcome boundaries | Introduction, Related Work, Discussion, Conclusions, References | Targeted non-systematic review; no duplicate reviewer, librarian, pharmacist, legal review, or exhaustive database search | Perform the consolidated final evidence review and classify every manuscript claim before writing v2 |
| Final synthesis | Complete | 2026-07-15 | Consolidate Evidence 01–07 and reassess publication readiness | `final_evidence_review.md`; score 61/100; GO for candid manuscript v2, NO-GO for submission or clinical use | Every major architecture, validation, provenance, performance, traceability, normalization, novelty, safety, and availability claim | Entire manuscript | Security/rights/declarations and all external clinical/human validation remain incomplete | Create the new v2 manuscript and its change log, claim map, and submission checklist |

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

Evidence 07 completed the last bounded scholarly task. All technically feasible essential tests and reviews identified for this cycle are now documented. Further progress on clinical correctness, explanation usefulness, usability, outcomes, independent reproduction, licensing, security remediation, and regulatory status requires external expertise or author/provider authority. The next required step is the consolidated evidence-completion review; manuscript v2 remains gated until that review is complete.

## Evidence 05 execution record

- Files: `research/journal_revision/evidence/05_traceability_semantics/`.
- Command:

```bash
PG_BIN=/tmp/rxcheck-pg16.14/install/bin \
PYTHON_BIN=/tmp/rxcheck-evidence-venv/bin/python \
bash research/journal_revision/evidence/05_traceability_semantics/scripts/run_audit.sh
```

- Pass/fail: MIXED / broad contract FAIL (runner exit 1 by prespecified rule).
- Files created: protocol, guarded audit runner, disposable-cluster runner, raw JSON, environment lock, execution/server logs, results, limitations, and manuscript notes.
- Claim impact: selected completed-run, finding, acknowledgment, and override persistence is supported; complete history/display reconstruction, accurate pair/source reporting, and reliable identity are not.
- Original-file check: original manuscript hash unchanged; no application source or historical research file modified.
- Residual risk: authentication, read auditing, immutability, concurrency, retention, compliance, and clinical appropriateness remain untested or unimplemented.

## Evidence 06 execution record

- Files: `research/journal_revision/evidence/06_normalization_benchmark/`.
- Command:

```bash
PG_BIN=/tmp/rxcheck-pg16.14/install/bin \
PYTHON_BIN=/tmp/rxcheck-evidence-venv/bin/python \
bash research/journal_revision/evidence/06_normalization_benchmark/scripts/run_benchmark.sh
```

- Pass/fail: FAIL (22/30; runner exit 1 by prespecified strict rule).
- Files created: frozen cases, protocol, independent verifier/application runner, disposable-cluster runner, reference verification, application results, complete API response log, environment lock, execution/server logs, results, limitations, and manuscript notes.
- Claim impact: bounded exact/brand/NDC behavior is supported; general ingredient-level resolution, complete combination representation, reliable explicit non-resolution, and outage degradation are not.
- Original-file check: original manuscript hash unchanged; no application source or historical research file modified.
- Residual risk: purposive case selection, shared RxNorm service, no real error distribution, no expert adjudication, and no clinical inference.

## Evidence 07 execution record

- Files: `research/journal_revision/evidence/07_citation_related_work_review/`.
- Source-check record: `raw_results/source_inventory.tsv` and `raw_results/search_log.md`.
- Validation command:

```bash
awk -F '\t' 'NF != 8 {print NR ":" NF; bad=1} END {if (!bad) print "all rows have 8 fields"}' \
  research/journal_revision/evidence/07_citation_related_work_review/raw_results/source_inventory.tsv
```

- Pass/fail: REVIEW COMPLETE; bibliographic identity PASS; broad novelty position FAIL.
- Files created: protocol, source inventory, search log, results, structured comparison, limitations, and manuscript notes.
- Claim impact: permits only a modest incremental authority-boundary/design-science contribution; prohibits first/novel claims for DDI checking, RAG, provenance, natural-language DDI explanation, or deterministic/rule-based logic plus LLM explanation.
- Manuscript sections: Introduction, Related Work, Discussion, Conclusions, and References.
- Original-file check: original manuscript hash unchanged; no application source or historical research file modified.
- Residual risk: targeted rather than systematic review, mutable web sources, no second reviewer, and no professional literature, clinical, legal, or regulatory adjudication.

## Final evidence-review execution record

- File: `research/journal_revision/final_evidence_review.md`.
- Validation: all ten required synthesis sections present; score table arithmetic verified at 61/100; original manuscript hash unchanged.
- Result: GO to draft manuscript v2; NO-GO for submission, clinical use, real patient data, or regulatory/safety claims.
- Claim impact: establishes the controlling full/partial/remove classifications for manuscript v2.
- Manuscript sections: all.
- Residual risk: the synthesis is based on one research process and the bounded Evidence 01–07 record; external clinical, human-factors, security, legal, rights, ethics, and independent-reproduction work remains.
- Recommended next action: create manuscript v2 as a new file, then validate it line by line against the synthesis.
