# Expanded Formative Architecture Evaluation Plan

## Scope

This evaluation examines observable behavior of the current RxCheck software architecture. It does not evaluate clinical effectiveness, interaction-database completeness, patient outcomes, FDA status, HIPAA compliance, or formal cost-effectiveness.

## Method

`research/evaluate_rxcheck.py` writes uniquely named synthetic fixtures to the configured Postgres database and calls the production `run_interaction_check()` service. It records expected behavior, observed behavior, pass/fail status, code evidence, and a manuscript-safe interpretation for each scenario.

The harness does not call Anthropic, OpenFDA, or RxNorm. External-service boundary scenarios use mocks that fail if invoked, demonstrating whether the core checker attempts those calls under controlled conditions.

Run:

```bash
python research/evaluate_rxcheck.py --allow-live-db
```

The explicit flag acknowledges that the script persists synthetic patients, drugs, interactions, check runs, findings, acknowledgments, and overrides. Fixture assertions contain `evaluation_fixture: true` in `raw_payload` so the data profiler can identify them.

## Scenario Matrix

| # | Scenario | Expected Architecture Behavior | What It Supports |
|---:|---|---|---|
| 1 | Deterministic DDI from stored row | A stored DDI and assertion produce a finding | Interaction existence is database-backed |
| 2 | Canonical drug-pair ordering | Reversed medication insertion still matches one sorted pair | Pair canonicalization is applied |
| 3 | Inactive medication exclusion | Inactive medication is absent from counts and findings | Only active medication rows are checked |
| 4 | Placeholder exclusion | Active placeholder is absent from checked medication and pair counts | Unverified concepts are excluded |
| 5 | Placeholder visibility | Placeholder medication remains stored and queryable | Exclusion does not erase unresolved input |
| 6 | DDSI absent without condition | DDSI is absent when no active matching condition exists | Condition-gated DDSI behavior |
| 7 | DFI independent of conditions | DFI appears without a patient-condition record | DFI and DDSI filters are distinct |
| 8 | Baseline severity ranking | Major DDI precedes minor DFI | Severity ordering is applied |
| 9 | Source severity conflict flag | Distinct stored severities set `sources_conflict` | Assertion disagreement is surfaced |
| 10 | Source assertion preservation | Assertion rows retain source, severity, and raw payload | Evidence rows remain inspectable |
| 11 | Check-run persistence | Run metadata and medication snapshot are stored | Checks are auditable artifacts |
| 12 | Finding snapshot persistence | Finding retains severity and source snapshots | Run-time evidence state is preserved |
| 13 | Findings before LLM request | Findings exist with no explanation ID | Detection precedes explanation |
| 14 | Duplicate medication handling | Duplicate medication does not duplicate a DDI finding | Finding deduplication by stored interaction |
| 15 | Missing interaction | An unrepresented drug pair creates no finding | Checker does not invent interactions |
| 16 | DDSI with active condition | Matching active condition causes DDSI to appear | Condition matching changes query result |
| 17 | Ranking across DDI/DDSI/DFI | Major, moderate, minor order is preserved | Cross-type ranking behavior |
| 18 | DDSI after condition resolution | Resolved condition removes DDSI from later checks | Only active conditions qualify |
| 19 | Override persistence | Override row remains linked to a finding | Override is an auditable record |
| 20 | Override is not suppression | A later run still returns an overridden interaction unsuppressed | Override and acknowledgment semantics differ |
| 21 | Acknowledgment severity escalation | Lower-severity acknowledgment does not suppress higher current severity | Escalation guard is applied |
| 22 | Acknowledgment suppression | Current-severity acknowledgment marks a later finding suppressed | Suppression flags rather than deletes |
| 23 | LLM requires existing finding | Missing finding lookup returns 404 before generation | Explanation endpoint is finding-bound |
| 24 | Anthropic not required | Core check succeeds while explainer call is mocked to fail | Paid LLM is outside deterministic checking |
| 25 | OpenFDA not required | Core check succeeds while citation fetch is mocked to fail | Label retrieval is outside deterministic checking |
| 26 | RxNorm not required at check time | Stored-RxCUI check succeeds while normalization is mocked to fail | Normalization is not a run-time checker dependency |

## Pass Criteria

- The script completes and writes both result files.
- Each scenario records expected and observed behavior rather than only a Boolean.
- External paid/free APIs are not called.
- Failures remain visible in JSON and Markdown; the harness does not convert them into claims of success.

No minimum number of passing scenarios establishes clinical validity. Results only characterize the tested implementation and fixture conditions.

## Known Limitations

- Fixtures are synthetic and intentionally narrow.
- Runs write to the configured database and are not automatically deleted.
- Duplicate medication evaluation verifies non-duplication of findings; the current pair count may include a same-RxCUI pair when duplicate active medication rows exist.
- Mocked service boundaries show that calls are not made on the tested path, not that every outage mode is handled gracefully across the product.
- The harness does not assess frontend behavior, concurrency, performance, security penetration, or clinical correctness.
- Database state and code revisions must be recorded with manuscript results because behavior can change.

## Reproducibility Record

For a reported run retain:

- Git commit SHA.
- Python version and dependency lock/snapshot.
- Database platform and schema revision.
- Generated `evaluation_results.json`.
- Generated `data_profile.json`.
- Pytest output.
- A statement that external APIs were mocked or disabled.
