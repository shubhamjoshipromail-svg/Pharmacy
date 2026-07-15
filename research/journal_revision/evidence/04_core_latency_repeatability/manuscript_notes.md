# Manuscript Notes From Evidence 04

## Permitted methods wording

> We conducted a single-machine, warm-cache, single-request formative benchmark of the unchanged core interaction-check orchestrator against a disposable loopback-only PostgreSQL 16.14 database. The database contained 150,000 synthetic background DDI interactions and assertions. Eight workloads combined active medication counts of 2, 10, 25, and 50 with zero or approximately 10% matched candidate pairs. After five warm-ups, each workload was measured in three passes of 30 calls. The timed interval included the orchestrator's database reads, run/finding writes, and commit, but excluded session creation, correctness queries, and cleanup.

## Permitted results wording

> All 720 measured calls returned the expected medication, candidate-pair, interaction, run, and finding counts without exceptions or external-service calls. Across the eight workloads, median latency ranged from 2.24 to 231.77 ms and p95 latency from 2.59 to 245.12 ms. All workloads met the prespecified local p95 threshold of 1,000 ms and the prespecified between-pass repeatability rule.

Immediately qualify the result:

> These measurements characterize one synthetic, warm-cache, sequential local environment and are not a production service-level agreement, scalability result, or clinical validation.

## Claim-status changes

| Claim | Status after Evidence 04 |
|---|---|
| Core DDI check latency has been measured | Supported for the specified local protocol |
| The measured checks returned expected counts | Supported for all 720 measured calls |
| Short-run local latency was repeatable | Supported by the prespecified pass-median rule |
| The core check requires no external API | Supported on the exercised DDI paths |
| End-to-end application latency is known | Not supported |
| Concurrent performance or throughput is known | Not supported |
| Production scalability or an SLA is established | Not supported |
| Latency on the real DDInter-derived database is established | Not supported |
| Clinical usefulness or safety follows from latency | Not supported |

## Placement

- Add the protocol to Methods under formative operational evaluation.
- Add the eight-workload table to Results.
- Add the limitations above to Threats to Validity/Limitations.
- Keep the full raw measurements and environment only in the repository; the article can cite the evidence folder.
