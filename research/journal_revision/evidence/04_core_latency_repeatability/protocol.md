# Protocol: Core-Check Latency and Repeatability Benchmark

## Research question

What single-request latency and short-run repeatability does the unchanged RxCheck core orchestrator exhibit in a controlled local PostgreSQL environment across increasing medication-list sizes and finding counts, while operating over interaction/assertion tables near the order of magnitude of the committed database profile?

## Why this task is publication-relevant

The author-action checklist requests a core-check latency summary with environment and sample size. The existing paper discusses cost-conscious service separation but reports no operational measurement. A bounded local benchmark is feasible without clinical data, paid services, or the unsafe database.

## Objective

Measure `app.services.orchestrator.run_interaction_check()` under controlled synthetic workloads and determine whether it meets a prespecified local formative threshold and repeatability rule.

## Environment design

- Disposable PostgreSQL 16.14 cluster bound to `127.0.0.1` on an ephemeral port.
- Fresh database created from `Base.metadata.create_all()`.
- 150,000 unrelated background DDI rows and 150,000 corresponding source assertions.
- Separate benchmark interactions/assertions for each matched workload.
- No DFI/DDSI rows, acknowledgments, or overrides.
- One request/session at a time; no concurrency.
- Local loopback database; warm operating-system/PostgreSQL caches after five warm-ups.
- Anthropic, OpenFDA, and RxNorm functions patched with failing sentinels during measured checks.

The background cardinality approximates the committed profile's 152,413 DDI rows and 172,713 DDInter assertions but is entirely synthetic and not distribution-matched.

## Workloads

For each medication-list size, two finding densities are evaluated:

| Active medications | Candidate pairs | Zero-findings workload | 10%-matched workload |
|---:|---:|---:|---:|
| 2 | 1 | 0 findings | 1 finding |
| 10 | 45 | 0 findings | 5 findings |
| 25 | 300 | 0 findings | 30 findings |
| 50 | 1,225 | 0 findings | 123 findings |

The 10%-matched count uses `ceil(candidate_pairs × 0.10)`.

## Repetitions

For each of the eight workloads:

1. Five untimed warm-up calls.
2. Three measured passes.
3. Thirty measured calls per pass.

Total measured calls: `8 × 3 × 30 = 720`.

Each call uses a new SQLAlchemy session. The timed interval begins immediately before awaiting the orchestrator and ends immediately after it returns. The function's own reads, finding/run inserts, and commit are included. Session construction, post-call correctness queries, and deletion of the benchmark run/findings are outside the timed interval.

## Correctness and reliability checks

Every call must return the expected:

- patient ID;
- medication count;
- candidate-pair count;
- interaction/finding count;
- persisted run ID;
- persisted finding count.

After each call, its run is deleted and cascade deletion of findings is verified. External-service sentinels must never fire.

## Metrics

For each workload:

- measured calls and successful/correct calls;
- minimum, median, mean, population standard deviation, p95, and maximum wall time in milliseconds;
- mean application-reported integer duration;
- three pass medians;
- pass-median absolute range and relative range;
- threshold and repeatability decision.

Aggregate metrics include total correct calls, exception count, external-call count, seed time, table cardinalities, database relation sizes, source hashes, and environment versions.

Percentiles use linear interpolation between adjacent ordered observations.

## Pass/fail criteria

This local formative benchmark passes only if:

1. All 720 measured calls complete and match every expected count.
2. No unhandled exception occurs.
3. No external-service sentinel fires.
4. Every workload's p95 is below 1,000 ms.
5. For every workload, pass-median relative range is at most 25%, or its absolute pass-median range is at most 2 ms for very low-latency measurements.
6. Every timed run and its findings are cleaned up after correctness verification.

The 1-second threshold is a prespecified local engineering criterion, not a clinical requirement or production service-level agreement.

## Reproduction command

```bash
PG_BIN=/path/to/postgresql/bin \
PYTHON_BIN=/path/to/python \
bash research/journal_revision/evidence/04_core_latency_repeatability/scripts/run_benchmark.sh
```

## Prespecified limitations

- Synthetic uniform background data do not reproduce DDInter topology, assertion multiplicity, or production query statistics.
- One local machine and one PostgreSQL version are tested.
- The benchmark is single-threaded and excludes HTTP/frontend/network latency beyond loopback database traffic.
- Warm-cache results should not be interpreted as cold-start latency.
- Cleanup prevents history-table growth from influencing later calls and therefore does not model a long-running database with accumulated check history.
- `Base.metadata.create_all()` bypasses the empty Alembic migration.
- Latency does not establish clinical accuracy, workflow value, scalability, availability, or deployment readiness.
