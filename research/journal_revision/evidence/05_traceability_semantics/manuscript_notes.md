# Manuscript Notes From Evidence 05

## Required replacement claim

Replace broad language such as:

> This allows the system to preserve what was checked, what was found, what was displayed, what was acknowledged, what was overridden, and what explanation was generated.

with:

> For completed checks with at least two verified medications, the prototype persists a medication snapshot and selected finding fields (run-time maximum severity, source names, source-label conflict state, and acknowledgment-suppression state). It also stores acknowledgment and finding-level override records plus selected write events. This is audit-oriented prototype persistence, not a complete, immutable, or identity-authenticated audit trail.

## Required explicit exceptions

- Checks with fewer than two non-placeholder medications return a warning but do not create a run/attempt record.
- Duplicate medication rows do not duplicate a finding, but `total_pairs_checked` can include a same-RxCUI pair and is not a count of distinct-drug pairs.
- Run-level `sources_used` is hard-coded to DDInter and can disagree with finding-level source snapshots.
- Historical mechanism, management/effect, evidence URL, source-record ID, and raw payload are not copied into finding snapshots; prior display content can change or become unreconstructible if live assertions change.
- Acknowledgment removal is currently attributed to the default user; no authenticated actor binding exists.
- Overrides remain linked to the original finding and neither suppress nor annotate later findings.

## Permitted results wording

> In a 15-criterion synthetic traceability audit, 10 criteria passed and five failed. The implementation preserved selected medication/finding fields across live-row mutation and persisted tested acknowledgment, suppression, escalation, deactivation, and override states. It did not preserve below-threshold attempts, produce distinct-pair counts in the presence of duplicate medications, maintain consistent run/finding source attribution, reconstruct prior displayed evidence from snapshots, or reliably attribute acknowledgment removal to the tested actor.

## Claim-status changes

| Claim | Status after Evidence 05 |
|---|---|
| Completed runs retain selected medication fields | Supported |
| Findings retain run-time severity/source/conflict/suppression fields | Supported |
| Duplicate rows do not duplicate stored findings | Supported |
| Pair-count reporting is accurate for duplicate medication rows | Not supported |
| Every attempted check is recorded | Not supported |
| Run-level source reporting is faithful | Not supported |
| The exact prior displayed evidence is reconstructible | Not supported |
| Acknowledgments suppress and higher severity resurfaces | Supported as tested software behavior |
| Overrides persist and do not affect later checks | Supported as tested software behavior |
| Review actor identity is reliable | Not supported |
| The system has a complete/immutable/compliance audit trail | Not supported |

## Placement

- Report the criterion table in Results or a repository supplement.
- Describe the snapshot field list precisely in Methods.
- Put failed semantics and unauthenticated identity in Limitations, not only Future Work.
- Do not claim reduced alert fatigue, workflow benefit, or regulatory auditability from these software tests.
