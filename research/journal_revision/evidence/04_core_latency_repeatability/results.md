# Results: Core-Check Latency and Repeatability

## Aggregate decision

| Criterion | Result |
|---|---:|
| Expected measured calls | 720 |
| Completed measured calls | 720 |
| Correct measured calls | 720 |
| Exceptions | 0 |
| External-service calls | 0 |
| Workloads passing all criteria | 8/8 |
| Check runs remaining after cleanup | 0 |
| Findings remaining after cleanup | 0 |
| Overall prespecified decision | PASS |

The disposable database contained 150,159 interactions and 150,159 assertions after seeding: 150,000 unrelated background rows plus 159 workload-matched rows. Seeding took 4.800 seconds. The interaction and assertion relations occupied 31,637,504 and 60,792,832 bytes, respectively.

## Workload statistics

| Medications | Candidate pairs | Expected findings | Median (ms) | p95 (ms) | Maximum (ms) | Pass-median range | Decision |
|---:|---:|---:|---:|---:|---:|---:|---|
| 2 | 1 | 0 | 2.237 | 2.586 | 4.088 | 0.492 ms / 22.1% | Pass |
| 2 | 1 | 1 | 3.007 | 3.174 | 3.208 | 0.039 ms / 1.3% | Pass |
| 10 | 45 | 0 | 3.076 | 3.510 | 4.986 | 0.125 ms / 4.1% | Pass |
| 10 | 45 | 5 | 5.448 | 6.035 | 21.418 | 0.719 ms / 12.2% | Pass |
| 25 | 300 | 0 | 17.720 | 18.787 | 20.080 | 0.636 ms / 3.6% | Pass |
| 25 | 300 | 30 | 25.136 | 26.493 | 28.200 | 0.506 ms / 2.0% | Pass |
| 50 | 1,225 | 0 | 204.722 | 209.953 | 211.843 | 2.211 ms / 1.1% | Pass |
| 50 | 1,225 | 123 | 231.768 | 245.124 | 251.869 | 2.452 ms / 1.1% | Pass |

Each row contains 90 measured calls. Percentiles use linear interpolation over ordered observations. Repeatability passed when the three pass medians had a relative range no greater than 25%, or an absolute range no greater than 2 ms for very fast calls.

## Correctness result

Every call was checked against its workload's expected patient ID, active-medication count, unique candidate-pair count, returned interaction count, summary count, nonempty run ID, and persisted finding count. Each saved run was then removed, cascade cleanup was verified, and the final history tables were empty.

## Reliability and isolation result

The runner patched the LLM, OpenFDA, and normalization service entry points with failing sentinels during all warm-up and measured checks. None fired. PostgreSQL logged a `127.0.0.1` bind and clean fast shutdown. The shell wrapper removed the temporary cluster after capturing the log.

## Integrity record

- Execution-time repository HEAD: `1cd6b29ae976247e87a2cc55165270039b3ca4d4`.
- Last commit affecting evaluated orchestrator/check/model sources: `c33c6581f5b577f10af421e4ebfd311add281317`.
- Results JSON SHA-256: `19a347af8db74006d74a643aac76605343bf122a9d83a30ff6718ec2142b3989`.
- Measurements CSV SHA-256: `4ff7626779f99f06634e455c5dd8c687c6880ea34e5988ef312eca7d287f7778`.
- Environment lock SHA-256: `b6169f706047c4b5763d2157110cdcd96a79b347c8151a3f1c0c324b2c70350e`.

The results JSON also records the runner and evaluated source-file hashes, environment versions, protocol parameters, table counts, relation sizes, and all workload decisions.
