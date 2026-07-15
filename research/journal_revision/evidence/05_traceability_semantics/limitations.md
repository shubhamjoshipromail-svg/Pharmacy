# Limitations: Persistence and Traceability Semantics

1. The audit used synthetic fixtures and called production Python functions directly; it did not exercise an authenticated HTTP client, frontend, or real user workflow.
2. Only selected write paths were tested. Patient/medication/condition changes, explanation persistence, import logs, and read events were not comprehensively audited.
3. No authentication or route-level authorization exists, so supplied/default user IDs are not trustworthy identities even where criterion-level equality passed.
4. `AuditEvent` rows are ordinary mutable database records. The audit did not test tamper resistance because no append-only, cryptographic, database-policy, or external-log control is implemented.
5. Concurrency, timestamp collisions, transaction failures, rollback behavior, retention, deletion, backup/restore, and clock integrity were not tested.
6. One local PostgreSQL version and one execution were used.
7. The result does not establish HIPAA, FDA, institutional, legal, evidentiary, or other compliance-grade auditability.
8. Acknowledgment/override behavior was assessed as software semantics, not clinical appropriateness, usability, or effect on alert fatigue.
9. The source-reporting case used a supported manual assertion to expose internal inconsistency; it does not measure the frequency of this mismatch in a configured dataset.
10. The strict contract was chosen to evaluate the manuscript's broad preservation language. Product requirements could intentionally exclude failed items, but the manuscript would then need to disclose those exclusions.
