# Evidence 01: Isolated Architecture Reproduction

## Status

**PASS — locally reproduced with important limitations.**

On July 15, 2026 UTC, the existing RxCheck architecture evaluator completed three repetitions against three newly created databases in a disposable loopback-only PostgreSQL 16.14 cluster. Every repetition passed all 26 predefined scenarios, reported no paid or free external API calls, began with an empty database, and created the expected 20-table schema.

## Why this task was selected

The prior research-readiness, claim, and journal audits all identified the same high-impact gap: the paper relied on a historical 26/26 run coupled to an unarchived configured database. A clean rerun is directly relevant to the central architecture claim and can be completed without clinical data, a pharmacist reviewer, or paid model calls.

## What was tested

- The production `run_interaction_check()` path through the unchanged committed evaluator.
- Deterministic stored-row finding creation.
- Medication/placeholder filtering and canonical pair behavior.
- DFI and condition-gated DDSI fixture behavior.
- Ranking, provenance, run/finding persistence, acknowledgment, and override behavior.
- The existing-finding precondition for explanation.
- Failing sentinels showing that Anthropic, OpenFDA, and RxNorm are not called on the exercised core-check paths.

## Method in brief

PostgreSQL 16.14 was built under `/tmp` from the official source archive after SHA-256 verification. A temporary Python 3.12 environment was resolved from the repository's `requirements.txt`. The evidence runner refused non-loopback database URLs and verified the server-side address before schema creation. Each repetition used a new empty database; the disposable cluster was stopped and deleted after the run.

The application, evaluator, original manuscript, and historical research results were not edited.

## Main result

| Repetition | Passed | Failed | Empty before setup | Tables after setup | External APIs | Evaluator wall time (s) |
|---|---:|---:|---:|---:|---|---:|
| 1 | 26 | 0 | Yes | 20 | None reported | 0.154543 |
| 2 | 26 | 0 | Yes | 20 | None reported | 0.145649 |
| 3 | 26 | 0 | Yes | 20 | None reported | 0.155756 |

Scenario names and pass/fail outcomes were identical in all three repetitions.

## Conclusion

The historical architecture result is reproducible on a fresh local PostgreSQL schema under the recorded environment. This materially strengthens the narrow claim that the implementation enforces the predefined deterministic/generative boundary on the tested synthetic paths.

It does not establish clinical correctness, interaction-source completeness, normalization accuracy, explanation factuality, pharmacist usefulness, security, or deployment readiness. It also does not resolve the repository's empty migration or unpinned-dependency problems.

## Evidence map

- `protocol.md` — prespecified question, method, metrics, and pass/fail criteria.
- `results.md` — audited findings and interpretation.
- `limitations.md` — residual methodological and reproducibility risks.
- `manuscript_notes.md` — exact future manuscript implications.
- `raw_results/run_01.json` to `run_03.json` — full scenario-level results and metadata.
- `raw_results/reproduction_summary.json` — cross-run agreement.
- `raw_results/environment_lock.txt` — resolved Python environment.
- `scripts/` — guarded runner, repetition harness, and aggregator.
- `logs/` — final execution, per-run, PostgreSQL lifecycle, and corrected preliminary-attempt logs.

## Reproduction

See `protocol.md` and run:

```bash
PG_BIN=/path/to/postgresql/bin \
PYTHON_BIN=/path/to/python \
bash research/journal_revision/evidence/01_isolated_architecture_reproduction/scripts/run_repetitions.sh
```

The Python environment must contain the dependencies in `raw_results/environment_lock.txt`. The harness creates and removes the database cluster automatically; it never accepts a non-loopback host.
