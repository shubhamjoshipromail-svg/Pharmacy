# Evidence 04: Core-Check Latency and Repeatability

## Status

**PASS WITH LIMITATIONS — all prespecified local formative criteria were met.**

The unchanged `run_interaction_check()` orchestrator was benchmarked against a disposable loopback-only PostgreSQL 16.14 database containing 150,000 synthetic background DDI rows and 150,000 corresponding assertions. Across eight medication-list/finding-density workloads, all 720 measured calls returned the expected patient, medication, candidate-pair, interaction, run, and finding counts. No exception or external-service sentinel occurred.

Every workload's p95 was below the prespecified 1,000 ms local threshold. Observed p95 values ranged from 2.586 ms for two medications with no findings to 245.124 ms for 50 medications, 1,225 candidate pairs, and 123 findings. All workloads also met the prespecified between-pass repeatability rule.

## Design

- Medication counts: 2, 10, 25, and 50.
- Finding densities: zero and 10% of candidate pairs.
- Five untimed warm-ups per workload.
- Three passes of 30 measured calls per workload.
- New SQLAlchemy session for every call.
- Timed scope: the production orchestrator call, including its database commit.
- Post-call correctness queries and cleanup outside the timed interval.
- Synthetic background scale: 150,000 interactions and 150,000 assertions.
- Execution: one local ARM64 macOS machine, Python 3.12.13, PostgreSQL 16.14, no concurrency.

## Conclusion

The result supports a narrow claim that the core deterministic check completed correctly and repeatably within the stated local warm-cache threshold for the specified synthetic workloads. It does not establish production capacity, a service-level agreement, concurrent performance, clinical accuracy, end-to-end web latency, or performance on the recovered DDInter dataset.

## Evidence map

- `protocol.md` — prespecified question, workloads, metrics, and pass/fail rules.
- `scripts/run_core_benchmark.py` — guarded seed, execution, correctness, and aggregation harness.
- `scripts/run_benchmark.sh` — disposable PostgreSQL lifecycle and environment capture.
- `raw_results/benchmark_results.json` — machine-readable metadata, statistics, decisions, and hashes.
- `raw_results/measurements.csv` — all 720 individual measurements.
- `raw_results/environment_lock.txt` — exact Python package environment.
- `logs/benchmark.log` — harness conclusion.
- `logs/harness_attempt_01.log` — first and only execution attempt.
- `logs/postgres.log` — server bind, version, startup, and clean shutdown evidence.
- `results.md` — interpreted results.
- `limitations.md` — scope boundaries and residual risks.
- `manuscript_notes.md` — permitted and prohibited manuscript wording.
