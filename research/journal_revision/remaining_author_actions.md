# Remaining Author Actions After Evidence 01

This file is the active post-evidence action register. The original numbered checklist, `06_remaining_author_actions.md`, remains unchanged as a review baseline.

## Completed in this branch

- [x] Create a disposable local PostgreSQL workflow that never uses the committed remote database URL.
- [x] Start each evaluation repetition from a fresh empty database.
- [x] Rerun all 26 architecture scenarios three times.
- [x] Retain scenario-level JSON, console logs, PostgreSQL lifecycle logs, exact package versions, source hashes, script hashes, timestamps, OS/architecture, and PostgreSQL version.
- [x] Confirm no external API calls were reported on exercised paths.
- [x] Stop and delete the temporary database cluster.
- [x] Confirm the original manuscript and historical evaluation files were not modified.

## Blocking security actions requiring author/provider authority

- [ ] Revoke and rotate the exposed database credential.
- [ ] Inspect provider/access logs for unauthorized access.
- [ ] Determine whether the database contains or contained identifiable or real patient data and follow applicable incident-response procedures.
- [ ] Remove the credential from active source and Git history through an approved coordinated history rewrite.
- [ ] Run and document a full secret/history scan after remediation.

These actions cannot be completed safely by adding evidence files alone. Until they are completed, the repository must be described as unsafe for clinical or public release use, and no real patient data should be entered.

## Highest-priority feasible research actions

1. [x] **Audit structured-output and hallucination-resistance checks.** Evidence 02 executed 30 cases. The implementation failed: 15 invalid cases were accepted and 7 raised unhandled exceptions.
2. [x] **Recover source-data provenance from repository and history.** Evidence 03 recovered the exact eight-file manifest, acquisition timestamps, official origins, hashes, and raw profile. Exact semantic release and transformation lineage remain unavailable.
3. [ ] **Create one independently specified validation component.** Prefer a transparent 20–50 case reference set or normalization benchmark derived from clearly cited authoritative material and, where possible, reviewed by a pharmacist or second researcher.
4. [x] **Measure core-check latency and repeatability.** Evidence 04 completed 720 correct calls across eight workloads; all met the local p95/repeatability rules. The result is not a production SLA or clinical validation.
5. [x] **Audit selected persistence and traceability semantics.** Evidence 05 passed 10/15 criteria but failed the broad contract: attempted insufficient checks are absent, duplicate pair counts overstate distinct pairs, run sources can be wrong, display evidence is not fully snapshotted, and acknowledgment removal uses the default identity.
6. [ ] **Review citation and related-work support.** Verify current references and add a structured comparison with rule-based DDI CDS, templated explanations, provenance-aware CDS, and grounded LLM systems.

## Explanation-boundary remediation required after Evidence 02

- [ ] Treat the current validator as failed, not partially validated, in manuscript Results and Limitations.
- [ ] Do not run or present live-model explanation quality as a positive result until structural enforcement is remediated.
- [ ] Enforce complete JSON consumption and top-level object type.
- [ ] Use a strict typed schema before persistence/return, including non-empty text, string-list elements, confidence enumeration, and an additional-field policy.
- [ ] Validate source names and stored severity against the exact structured context.
- [ ] Add explicit checks/review for unsupported dosing, mechanisms, effects, foods/conditions, and unknown entities.
- [ ] Add prompt-injection regression cases and controlled failure behavior.
- [ ] Rerun the frozen 30-case suite after remediation and retain both pre- and post-remediation results.

Under the current file-preservation rules, the application source was not modified. These items remain engineering actions for an explicitly authorized future implementation change.

## Traceability remediation required after Evidence 05

- [ ] Persist below-threshold check attempts or narrow all history claims to completed checks with at least two verified medications.
- [ ] Deduplicate active RxCUIs before candidate-pair generation and report distinct-row and distinct-pair metrics separately.
- [ ] Derive run-level sources from actual finding assertions rather than hard-coding DDInter.
- [ ] Define and persist the exact historical display/evidence snapshot required for later reconstruction.
- [ ] Bind acknowledgment removal and all review actions to authenticated identities.
- [ ] Add append-only/tamper-evident controls and read auditing only if a stronger audit claim is intended.
- [ ] Keep override semantics explicit: current overrides are finding-level records and do not affect later checks.

## Reproducibility work still required

- [ ] Replace the empty migration with a complete, reviewed migration or schema bootstrap artifact without changing the preserved application baseline.
- [ ] Pin Python and frontend dependencies in a new reproducibility package.
- [ ] Automate PostgreSQL and Python prerequisite setup or provide a container workflow.
- [x] Record DDInter source filenames, acquisition date, official origin, source checksums, and current byte identity.
- [x] Record the official DDInter license/terms URL and CC BY-NC-SA 4.0 status.
- [ ] Obtain a publisher-defined semantic release identifier; do not infer one from the 2021 server timestamp.
- [ ] Reconstruct import accounting and separate source-derived records from fixtures. Evidence 03 shows this cannot be recovered from current artifacts.
- [ ] Freeze or hash the alias/preferred-name mapping used by each import.
- [ ] Persist deduplicated input counts, cross-file membership, quarantine rows/reasons, inserted-vs-conflicted counts, and a run ID.
- [ ] Obtain an independent rerun on a second machine or by a second researcher.

## External or author-supplied items

- [ ] Software-license selection by the copyright holder and third-party data-license review.
- [ ] Author names, affiliations, ORCIDs, CRediT roles, corresponding-author details, funding, conflicts, and acknowledgments.
- [ ] Institutional ethics/human-subjects determination.
- [ ] Pharmacist or methods-reviewer feedback.
- [ ] Target-journal selection and current formatting/APC/policy check.

## Manuscript gate

Do not create manuscript v2 until the feasible technical evidence tasks are complete and `final_evidence_review.md` has classified every major claim. Evidence 01 permits updating the reproducibility result, but it does not permit claims of clinical validation, safety, completeness, full reproducibility, affordability, or deployment readiness.
