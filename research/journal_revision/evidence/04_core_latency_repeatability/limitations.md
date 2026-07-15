# Limitations: Core-Check Latency and Repeatability

1. **Formative local benchmark only.** The 1,000 ms threshold was a project-defined engineering criterion, not a clinical requirement or production SLA.
2. **One machine and environment.** Results were obtained once on ARM64 macOS 15.7.7 with Python 3.12.13 and PostgreSQL 16.14. Independent and cross-platform repetitions remain absent.
3. **Warm-cache behavior.** Five warm-ups preceded measurement. Cold start, cache eviction, restart, and degraded-resource behavior were not measured.
4. **No concurrency.** Calls were sequential. Throughput, contention, connection-pool behavior, long-tail latency under load, and availability are unknown.
5. **Synthetic topology.** Background interactions were generated uniformly from 600 drugs. They approximate table cardinality but not DDInter graph structure, source multiplicity, row width, distribution, or query statistics.
6. **Limited interaction types.** Workloads exercised DDI rows only. DFI, DDSI, therapeutic duplication, conditions, acknowledgments, overrides, conflicting sources, LLM explanation retrieval, and citation retrieval were outside scope.
7. **Core function, not end to end.** HTTP routing, authentication, serialization, browser rendering, user-perceived latency, external networking, and deployment infrastructure were excluded.
8. **History cleanup.** Runs and findings were deleted after verification, outside the timed interval. The benchmark therefore does not capture performance with a large accumulated history.
9. **Model metadata schema setup.** The fresh database used `Base.metadata.create_all()` because the committed Alembic migration is empty. This does not prove migration-based reproducibility.
10. **No clinical inference.** Fast and count-correct execution does not establish source completeness, clinical correctness, sensitivity, specificity, safety, usability, or patient benefit.

The paper must retain these boundaries and avoid phrases such as “real-time clinical performance,” “production ready,” “scalable,” or “validated for clinical use.”
