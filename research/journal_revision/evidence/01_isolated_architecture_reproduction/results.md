# Results: Isolated Architecture Reproduction

## Prespecified decision

**PASS.** All success criteria in `protocol.md` were met in the final execution.

## Execution context

- Final execution: July 15, 2026 UTC.
- Repository HEAD at execution: `63fb4c043e6e16561f6cc9a46eaa152584de83b0`.
- Most recent commit affecting the evaluated application/evaluator paths: `5038106ada9c66fb2cd1fc0e33c8322553b4d699`.
- Original manuscript Git object hash before and after: `cd5c4ab332461544a1f083bfcfd65fd60b2b49e4`.
- Operating system: macOS 15.7.7, Darwin 24.6.0, arm64.
- Python: 3.12.13.
- PostgreSQL: 16.14, built with Apple clang 17.0.0.
- PostgreSQL source archive SHA-256: `f6d077142737920858ce958ccdb75c6ee137a63b5b0853c70693d401ac7e3471`.
- Relevant resolved packages: SQLAlchemy 2.0.51, FastAPI 0.139.0, Pydantic 2.13.4, pydantic-settings 2.14.2, psycopg2-binary 2.9.12, Anthropic 0.116.0.
- Schema setup: `Base.metadata.create_all()`, not Alembic.

The complete package set is retained in `raw_results/environment_lock.txt`. Per-run JSON files include the operating-system string, package versions, PostgreSQL version, source hashes, evidence-script hashes, schema inventory, row counts, timestamps, and full scenario payloads.

## Aggregate result

| Metric | Observed |
|---|---:|
| Fresh-database repetitions | 3 |
| Total scenario executions | 78 |
| Passing scenario executions | 78 |
| Failed scenario executions | 0 |
| Repetitions with 26/26 passing | 3 |
| Scenario-outcome agreement | Yes |
| Repetitions reporting paid external API calls | 0 |
| Repetitions reporting free external API calls | 0 |
| Pre-existing tables per database | 0 |
| Created expected tables per database | 20 |

The evaluator wall times were 0.154543, 0.145649, and 0.155756 seconds. These values describe the Python evaluation call in tiny synthetic databases and are not presented as a production latency benchmark.

## Scenario results

All of the following outcomes were `true` in every repetition:

1. Deterministic DDI from a stored row.
2. Canonical drug-pair ordering.
3. Inactive-medication exclusion.
4. Placeholder exclusion.
5. Placeholder visibility with check exclusion.
6. DDSI absence without an active condition.
7. DFI behavior independent of a condition profile.
8. Severity ranking.
9. Stored severity-label conflict flagging.
10. Source-assertion preservation.
11. Check-run persistence.
12. Finding-snapshot persistence.
13. Findings existing before an LLM request.
14. Duplicate medication not duplicating a finding.
15. Missing stored interaction not creating a finding.
16. DDSI presence with a matching active condition.
17. Ranking across DDI, DDSI, and DFI fixtures.
18. DDSI absence after condition resolution.
19. Override persistence.
20. Override not suppressing a future finding.
21. Acknowledgment severity-escalation behavior.
22. Acknowledgment suppression.
23. Existing-finding requirement for explanation.
24. Anthropic not required for core checking.
25. OpenFDA not required for core checking.
26. RxNorm not required at check time.

Full expected, observed, code-evidence, interpretation, and fixture fields are retained rather than reduced to this list.

## Database state after each repetition

Each fresh database produced the same selected row counts:

| Table or entity | Rows |
|---|---:|
| Users | 1 |
| Patients | 1 |
| Drugs | 4 |
| Patient medications | 5 |
| Foods | 1 |
| Conditions | 1 |
| Patient conditions | 1 |
| Interactions | 3 |
| Source assertions | 4 |
| Check runs | 11 |
| Check findings | 23 |
| Acknowledgments | 2 |
| Overrides | 1 |
| Audit events | 1 |

These counts demonstrate deterministic fixture lifecycle within the tested environment. They are not estimates of real data coverage.

## Safety and integrity checks

- The URL guard accepted only `localhost` or `127.0.0.1` with the `rxcheck_evidence_run_*` database naming convention.
- A server-side query confirmed `127.0.0.1` before schema creation.
- PostgreSQL logs confirm loopback binding, successful startup, fast shutdown, and completed shutdown.
- No disposable `rxcheck-evidence.*` directory remained after teardown.
- Source and evidence-script hashes matched across all final runs.
- `paper/rxcheck_manuscript_0.1v.md`, `research/evaluation_results.json`, and `research/evaluation_results.md` had no diff after execution.

## Preliminary execution notes

The first harness attempt stopped before schema creation or scenario execution because PostgreSQL returned the loopback address with a CIDR suffix (`127.0.0.1/32`) and the initial guard compared it with `127.0.0.1`. The failed attempt is retained in `logs/harness_attempt_01.log`. The query was corrected to compare the address host value.

A subsequent successful run exposed a harmless readiness-log artifact: `pg_isready` queried the username-named default database. The final harness explicitly probes the built-in `postgres` database, and the final PostgreSQL log contains no `FATAL`, `ERROR`, or `PANIC` entries. The successful pre-final console output is retained in `logs/harness_attempt_02.log`; the final outputs were regenerated after the script correction.

## Claim-level interpretation

The evidence supports this narrow statement:

> In three July 15, 2026 repetitions from newly created local PostgreSQL databases, the unchanged RxCheck formative evaluator passed all 26 predefined synthetic architecture scenarios and reported no external API calls on the exercised paths.

It does not support describing the system as clinically validated, safe, comprehensive, independently evaluated, or fully reproducible from a clean clone. The evaluator and expected outcomes remain self-authored, and repository-level migration/dependency defects remain.
