# Results: Persistence and Traceability Semantics

## Overall decision

The runner completed all 15 criteria without external API calls. Ten passed and five failed; the prespecified broad contract therefore failed. Exit status 1 represents the failed contract, not a harness failure.

| ID | Domain | Result | Observed behavior | Claim implication |
|---|---|---|---|---|
| T01 | Insufficient input | Pass | One verified medication returned a controlled warning and zero pairs | Controlled early return is supported |
| T02 | Attempt history | **Fail** | Empty run ID; zero persisted patient runs | Below-threshold attempts are absent from history |
| T03 | Duplicate finding | Pass | Three active rows (A, A, B) produced one returned and persisted finding | Duplicate finding prevention is supported |
| T04 | Pair accounting | **Fail** | Two distinct RxCUIs should yield one pair; result reported two | `total_pairs_checked` is not a distinct-drug-pair metric with duplicates |
| T05 | Source reporting | **Fail** | Run sources `['DDInter']`; finding source union `['manual']` | Run-level source attribution can be incorrect |
| T06 | Medication snapshot | Pass | Two-entry snapshot remained unchanged after live medication/drug edits | Selected medication fields are historical snapshots |
| T07 | Finding snapshot | Pass | Major severity, DDInter/manual sources, conflict, and suppression state remained unchanged | Selected finding fields are historical snapshots |
| T08 | Display reconstruction | **Fail** | Mechanism, management, evidence URL, source record, and raw payload absent from finding snapshot | A prior displayed summary/evidence record is not fully reconstructible |
| T09 | Acknowledgment record | Pass | Acknowledgment and creation event retained the tested user and note | Selected creation persistence is supported |
| T10 | Suppression snapshot | Pass | Same-severity acknowledgment retained finding with returned/stored suppression true | Suppression-without-deletion is supported |
| T11 | Severity escalation | Pass | Contraindicated current severity resurfaced over major acknowledgment | Implemented resurfacing comparison is supported |
| T12 | Deactivation | Pass | Acknowledgment became inactive; removal event persisted | Selected removal-state persistence is supported |
| T13 | Deactivation identity | **Fail** | Tested user UUID differed from removal-event default-user UUID | Reliable actor attribution is not supported |
| T14 | Override record | Pass | Override and event retained user, action, contraindicated severity, and note | Finding-level override persistence is supported |
| T15 | Override semantics | Pass | Original finding retained one override; later finding had none and was unsuppressed | Overrides are historical records, not future-check controls |

## Snapshot mutation test

The completed run stored a JSON medication snapshot and the finding stored maximum severity, source names, conflict state, and acknowledgment-suppression state. Later edits to drug names, medication dose/activity, assertion severities, mechanism/management, URLs, source IDs, and raw payload did not alter the selected run/finding fields.

However, `InteractionCheckFinding` has no columns for mechanism, management/effect, evidence URL, source record ID, or raw payload. Once the live assertion rows were edited, those prior values were not recoverable from the run/finding snapshot. The original manuscript's unqualified claim that the system preserves “what was displayed” is therefore too broad.

## Workflow semantics

The acknowledgment creation route used the explicitly supplied test user and wrote an event. Same-severity acknowledgment suppressed the finding without deleting it; raising the current assertion from major to contraindicated resurfaced it. Deactivation retained the acknowledgment as inactive and wrote a removal event, but the event was attributed to user `00000000-0000-0000-0000-000000000001`, not the workflow user.

The override route stored the tested user/action/note and the finding's run-time severity, plus an event. A subsequent check did not use or copy that override. This matches the intended “historical record only” behavior but means overrides do not annotate or control later findings.

## Integrity record

- Execution-time repository HEAD: `285167e28dd36a6217b309bd1c8aa2df6d457980`.
- Last commit affecting evaluated sources: `c33c6581f5b577f10af421e4ebfd311add281317`.
- Results JSON SHA-256: `633d35a5ce82f94f473555e3a042204bc7cc6ca65272ca9506ee455aae892cf3`.
- Environment lock SHA-256: `b6169f706047c4b5763d2157110cdcd96a79b347c8151a3f1c0c324b2c70350e`.

The raw JSON records all criterion evidence, fixture/run IDs, table counts, source hashes, runner hash, package versions, and local database metadata.
