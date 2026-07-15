# Publication-Readiness Evidence Index

| Evidence ID | Status | Question | Method | Result | Main files | Claim implication |
|---|---|---|---|---|---|---|
| 01 — Isolated architecture reproduction | Pass with limitations | Can the historical 26-scenario evaluator run from an empty local PostgreSQL database without external APIs? | Three repetitions in three new databases within a disposable loopback-only PostgreSQL 16.14 cluster; unchanged evaluator and production orchestrator | 26/26 in every repetition; 78/78 scenario executions; identical outcomes; no external APIs reported | `evidence/01_isolated_architecture_reproduction/README.md`, `protocol.md`, `results.md`, `raw_results/reproduction_summary.json`, `raw_results/run_*.json` | Supports repeated clean-database architecture verification in one recorded environment; does not support clinical or full data reproducibility claims |

## Evidence quality note

Evidence 01 is direct executed software evidence with retained raw outputs and environment metadata. Confidence is limited by self-authored scenarios, one machine/platform, synthetic fixtures, schema creation outside Alembic, unpinned repository dependencies, and absence of independently specified clinical cases.
