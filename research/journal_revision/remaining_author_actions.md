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
3. [x] **Create one independently specified validation component.** Evidence 06 froze 30 official-reference-derived normalization cases and separately verified all mappings before execution. The application failed 8/30 strict cases; no pharmacist/second-researcher adjudication was available.
4. [x] **Measure core-check latency and repeatability.** Evidence 04 completed 720 correct calls across eight workloads; all met the local p95/repeatability rules. The result is not a production SLA or clinical validation.
5. [x] **Audit selected persistence and traceability semantics.** Evidence 05 passed 10/15 criteria but failed the broad contract: attempted insufficient checks are absent, duplicate pair counts overstate distinct pairs, run sources can be wrong, display evidence is not fully snapshotted, and acknowledgment removal uses the default identity.
6. [x] **Review citation and related-work support.** Evidence 07 verified 15/15 current reference identities, classified 9 direct and 6 bounded uses, and compared six required categories. The result requires an incremental authority-boundary framing and rejects broad novelty.

## Final evidence-completion status

- [x] Consolidate all completed, failed, mixed, and inconclusive Evidence 01–07 results.
- [x] Classify fully supported, partially supported, and prohibited manuscript claims.
- [x] Record remaining external-validation and author-authority needs.
- [x] Update publication readiness to 61/100 with category-level rationale.
- [x] Record GO for manuscript v2 drafting and NO-GO for submission/clinical use.
- [x] Specify exact manuscript changes and a twelve-step revision order.

The controlling synthesis is `final_evidence_review.md`.

## Manuscript v2 phase

- [x] Create manuscript v2 as a completely new file.
- [x] Integrate all completed, failed, mixed, and inconclusive Evidence 01–07 results.
- [x] Replace the unresolved related-work marker with a verified comparison.
- [x] Create a 34-claim evidence map.
- [x] Create a section-level manuscript change log.
- [x] Create a submission-readiness checklist with explicit blockers.
- [x] Create updated authority-boundary and evidence-flow figure sources.
- [ ] Render and visually verify figures in the target journal's required formats.
- [ ] Resolve every author/declaration placeholder.
- [ ] Obtain pharmacist-informatics, methods, and literature-search review.
- [ ] Complete security, licensing, ethics, and target-journal actions in `manuscript/submission_readiness_checklist.md`.

## Citation and related-work actions after Evidence 07

- [x] Verify the bibliographic identity of all 15 current references against primary, publisher, or official records.
- [x] Record claim-fit limits for every existing citation.
- [x] Compare rule-based DDI CDS, DDI alert presentation, deterministic template baseline, contextualized DDI algorithms, provenance-aware CDS, medical RAG, and natural-language DDI explanation.
- [ ] Replace the RAG arXiv URL with the official NeurIPS proceedings record in manuscript v2.
- [ ] Add the closest related-work citations from Evidence 07 and remove the unresolved related-work marker in manuscript v2.
- [ ] Describe ExDDI as prior natural-language DDI explanation work and distinguish prediction explanations from RxCheck's post-finding prose.
- [ ] State that a deterministic source-filled template is the missing baseline; do not claim an LLM benefit.
- [ ] Use FHIR/AHRQ provenance work as context while explicitly stating that RxCheck is not standards-conformant and failed the broad traceability contract.
- [ ] Present the 2026 hybrid DDI preprint, if cited, as non-peer-reviewed contemporaneous overlap only.
- [ ] Have a librarian or second researcher update the search for the selected target journal before submission.

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

## Normalization remediation required after Evidence 06

- [ ] Represent and retain all ingredients for multi-ingredient concepts; do not silently select the first related ingredient.
- [ ] Reject or route approximate candidates that lack active concept properties or a resolvable ingredient.
- [ ] Separate exact, normalized-exact, fuzzy, candidate, and user-confirmed status semantics.
- [ ] Convert RxNorm timeouts/network/server errors to explicit visible non-resolution without losing the attempted input.
- [ ] Rerun the frozen 30-case benchmark after remediation and retain paired before/after results.
- [ ] Expand with independently sourced real-world errors only if expert review or an appropriate dataset becomes available.

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

All feasible technical and bounded scholarly evidence tasks in this cycle are complete, and manuscript v2 now applies `final_evidence_review.md` to every major claim. Submission remains gated by security remediation, rights/licensing, author and ethics declarations, target-journal checks, rendered/verified figures, final quality assurance, and appropriate external review. The combined evidence does not permit claims of clinical validation, safety, completeness, full reproducibility, affordability, deployment readiness, explanation grounding, broad traceability, general normalization accuracy, or broad novelty.
