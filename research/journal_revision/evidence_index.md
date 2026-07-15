# Publication-Readiness Evidence Index

| Evidence ID | Status | Question | Method | Result | Main files | Claim implication |
|---|---|---|---|---|---|---|
| 01 — Isolated architecture reproduction | Pass with limitations | Can the historical 26-scenario evaluator run from an empty local PostgreSQL database without external APIs? | Three repetitions in three new databases within a disposable loopback-only PostgreSQL 16.14 cluster; unchanged evaluator and production orchestrator | 26/26 in every repetition; 78/78 scenario executions; identical outcomes; no external APIs reported | `evidence/01_isolated_architecture_reproduction/README.md`, `protocol.md`, `results.md`, `raw_results/reproduction_summary.json`, `raw_results/run_*.json` | Supports repeated clean-database architecture verification in one recorded environment; does not support clinical or full data reproducibility claims |
| 02 — LLM validator conformance | Fail | Does the implemented explanation validator enforce the prompt/rubric contract over valid, malformed, mistyped, inconsistent, ungrounded, and injection-shaped outputs? | 30 frozen cases against the unchanged parser, stored-name scan, and Pydantic response builder; no model, database, or API calls | 3/3 valid controls accepted; 5/27 invalid cleanly rejected; 15 false accepts; 7 unhandled exceptions | `evidence/02_llm_validator_conformance/README.md`, `protocol.md`, `fixtures/validator_cases.json`, `results.md`, `raw_results/validator_results.json` | Supports only narrow custom-check wording; disproves strict/comprehensive schema-validation and automated grounding-resistance claims for the tested implementation |

## Evidence quality note

Evidence 01 is direct executed software evidence with retained raw outputs and environment metadata. Confidence is limited by self-authored scenarios, one machine/platform, synthetic fixtures, schema creation outside Alembic, unpinned repository dependencies, and absence of independently specified clinical cases.

Evidence 02 is direct deterministic function-level evidence with frozen cases and complete raw outputs. It measures enforcement coverage, not live-model defect frequency or clinical correctness. The failed result must narrow the explanation claims even though the separate finding-authority boundary remains supported.
