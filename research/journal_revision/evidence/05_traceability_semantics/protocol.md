# Protocol: Persistence and Traceability Semantics Audit

## Research question

Does the unchanged RxCheck implementation preserve a faithful, internally consistent record of selected check attempts, pair accounting, source use, displayed evidence, acknowledgments, and overrides at the level implied by the manuscript's audit-oriented persistence claim?

## Rationale

The claim–evidence audit classified review activity as only partially supported. The journal-readiness review identified specific discrepancies: checks below two verified medications are not persisted, duplicate medication rows can distort pair counts, run-level source reporting is hard-coded, and audit identity is not authenticated. The original manuscript also says the system preserves “what was checked, what was found, what was displayed, what was acknowledged, [and] what was overridden.” These are testable database semantics, not clinical claims.

## Scope

The audit exercises unchanged production functions and models in a new disposable loopback-only PostgreSQL 16.14 database. It does not modify application code.

Four synthetic patient fixtures cover:

1. one verified medication plus one excluded placeholder;
2. duplicate active medication rows and a manual-only DDI assertion;
3. medication/finding snapshots followed by mutations to live medication, drug, and assertion rows;
4. acknowledgment, severity escalation, deactivation, override, and audit-event workflows.

No external API is needed. The LLM, OpenFDA, and normalization entry points are patched with failing sentinels around core checks.

## Prespecified criteria

| ID | Domain | Criterion |
|---|---|---|
| T01 | Insufficient input | A below-threshold invocation returns a controlled warning. |
| T02 | Attempt history | Every check invocation, including a below-threshold attempt, has a persisted run/attempt record. |
| T03 | Duplicate medication | Duplicate active medication rows do not create duplicate findings. |
| T04 | Pair accounting | `total_pairs_checked` equals unordered pairs of distinct evaluated RxCUIs. |
| T05 | Source reporting | Run-level `sources_used` equals the union of the persisted finding source snapshots. |
| T06 | Medication snapshot | A completed run's medication snapshot remains unchanged after live rows are edited. |
| T07 | Finding snapshot | Severity, source list, conflict state, and suppression state remain unchanged after live assertions are edited. |
| T08 | Display reconstruction | The persisted run/finding snapshot alone preserves the displayed evidence details (mechanism, effect/management, evidence URL, source record, raw payload) needed to reconstruct the prior display. |
| T09 | Acknowledgment record | Acknowledgment state and its creation audit event persist with the tested user and payload. |
| T10 | Suppression snapshot | A same-severity acknowledgment suppresses presentation without deleting the finding, and this state is stored on the finding. |
| T11 | Escalation | A later higher current severity resurfaces the finding relative to the stored acknowledgment severity. |
| T12 | Deactivation | Acknowledgment deactivation persists and creates a removal audit event. |
| T13 | Deactivation identity | The removal audit event is bound to the user whose tested workflow initiated the review action. |
| T14 | Override record | Override metadata and its audit event persist with the tested user, action, severity, and note. |
| T15 | Override semantics | An override remains attached to its original finding and does not silently suppress or mutate a later check. |

## Decision rule

Each criterion is reported independently. The broad traceability contract passes only if all 15 criteria pass. A mixed result supports only the specific passing behaviors and requires the manuscript to disclose each failed semantic explicitly.

This is intentionally stricter than checking table existence: audit-oriented claims require completeness, internal consistency, historical fidelity, and reliable action attribution.

## Outputs

- Machine-readable result for every criterion.
- Fixture and observed database identifiers sufficient to audit the run, but no credentials.
- Environment, source, and runner hashes.
- PostgreSQL lifecycle log and exact package lock.
- Human-readable results, limitations, and manuscript implications created after execution.

## Reproduction command

```bash
PG_BIN=/path/to/postgresql/bin \
PYTHON_BIN=/path/to/python \
bash research/journal_revision/evidence/05_traceability_semantics/scripts/run_audit.sh
```

The runner returns exit status 1 when the broad 15-criterion contract fails, even when execution itself completes correctly.

## Limitations

- Synthetic fixtures and direct Python function calls, not authenticated HTTP clients or a user study.
- One database/version and one execution.
- Selected write events only; read access, concurrency, tamper resistance, retention, authorization, and regulatory compliance are out of scope.
- The audit assesses recorded semantics, not clinical appropriateness of acknowledgments or overrides.
