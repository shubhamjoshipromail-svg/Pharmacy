# Evidence 05: Persistence and Traceability Semantics

## Status

**MIXED — 10/15 criteria passed; the broad traceability contract failed.**

The unchanged production implementation was exercised in a disposable loopback-only PostgreSQL 16.14 database. Selected persistence behavior is real: controlled insufficient-input handling, duplicate-finding prevention, medication and selected finding snapshots, acknowledgment creation/suppression/escalation/deactivation, override persistence, and non-suppression by later override all behaved as tested.

Five material semantics failed:

1. an invocation with only one verified medication produced no persisted attempt/run;
2. duplicate active medication rows reported two pairs for two distinct RxCUIs instead of one;
3. a manual-only finding was stored under a run whose `sources_used` said DDInter;
4. prior mechanism, management/effect, evidence URL, source record, and raw payload could not be reconstructed from run/finding snapshots after live assertion mutation; and
5. acknowledgment removal was attributed to the hard-coded default user instead of the tested workflow user.

## Publication conclusion

The project supports “audit-oriented persistence of selected completed runs, finding fields, acknowledgments, overrides, and selected events.” It does not support “complete audit trail,” “preserves everything displayed,” reliable actor attribution, or compliance-grade audit logging. The paper must state each boundary explicitly.

## Evidence map

- `protocol.md` — research question, 15 criteria, decision rule, and limitations.
- `scripts/run_traceability_audit.py` — guarded fixtures, production-function execution, and database assertions.
- `scripts/run_audit.sh` — disposable PostgreSQL lifecycle and environment capture.
- `raw_results/traceability_results.json` — all criterion results, fixture IDs, table counts, versions, and hashes.
- `raw_results/environment_lock.txt` — exact Python package environment.
- `logs/execution.log` — completed audit summary and expected nonzero contract status.
- `logs/execution_attempt_01.log` — first and only execution attempt.
- `logs/postgres.log` — loopback bind and clean shutdown.
- `results.md` — interpreted result table.
- `limitations.md` — scope and remaining risks.
- `manuscript_notes.md` — exact claim changes.
