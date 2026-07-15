# RxCheck Submission-Readiness Checklist

**Current decision:** **NO-GO FOR SUBMISSION**

**Permitted next state:** Manuscript v2 may undergo author, domain, security, rights, and journal-specific review. The prototype remains no-go for clinical use and real patient data.

## A. Evidence and manuscript integrity

- [x] Original paper preserved without modification.
- [x] Prior v1 revision preserved without modification.
- [x] Evidence 01–07 completed and indexed.
- [x] Final evidence review completed.
- [x] Manuscript v2 created as a new file.
- [x] Positive and negative results reported with exact denominators.
- [x] Failed validator, lineage, traceability, and normalization contracts disclosed.
- [x] Clinical, safety, usefulness, cost, and deployment claims removed.
- [x] Novelty narrowed to an incremental authority-boundary instantiation.
- [x] Claim-to-evidence map created.
- [x] Manuscript change log created.
- [ ] Independent second-researcher check of scripts, raw outputs, and manuscript numbers.

## B. Immediate security and data protection blockers

- [ ] Revoke and rotate the exposed database credential.
- [ ] Inspect provider and access logs for unauthorized use.
- [ ] Determine whether the database ever contained real or identifiable data.
- [ ] Follow institutional incident-response requirements if applicable.
- [ ] Remove the credential from active source and Git history through an approved coordinated rewrite.
- [ ] Run and retain a full secret/history scan after remediation.
- [ ] Create a clean public archival tag that contains no active secret.

**Gate:** Any unchecked item in Section B is a submission and release blocker.

## C. Reproducibility and data lineage

- [x] Fresh local architecture reproduction retained.
- [x] Core latency harness and raw measurements retained.
- [x] Validator, traceability, and normalization fixtures/results retained.
- [x] DDInter source manifest, origin metadata, and hashes retained.
- [ ] Replace the empty migration with a reviewed schema bootstrap/migration.
- [ ] Pin and package backend and frontend dependencies.
- [ ] Provide one-command prerequisite/environment setup or a reviewed container workflow.
- [ ] Obtain a publisher-defined semantic DDInter release identifier or retain manifest-only wording.
- [ ] Complete a fresh manifest-driven import with mapping snapshot, quarantine, deduplication, inserted/conflicted counts, and run ID.
- [ ] Obtain an independent rerun on a second machine by a second researcher.

## D. Clinical and human-factors evidence

- [ ] Pharmacist or clinical-pharmacologist review of design requirements.
- [ ] Independently adjudicated clinical DDI reference cases if any accuracy claim is desired.
- [ ] Remediate validator before generating a positive explanation dataset.
- [ ] Compare no explanation, deterministic source-filled template, and generated explanation.
- [ ] Obtain an appropriate ethics determination before recruiting users.
- [ ] Conduct a pharmacist comprehension/usability study before any workflow-benefit claim.
- [ ] Reserve patient outcomes and alert-fatigue claims for later prospective research.

**Gate:** Section D may remain incomplete only if the target venue accepts a strictly formative, non-clinical paper and the manuscript retains all current limitations. No clinical or user-benefit claim is allowed.

## E. Rights, licensing, ethics, and declarations

- [ ] Copyright holder selects a root software license.
- [ ] Qualified review confirms compatibility with DDInter and other third-party terms.
- [ ] Author names, degrees, affiliations, ORCIDs, and corresponding-author details supplied.
- [ ] CRediT roles supplied and approved by all authors.
- [ ] Funding statement supplied.
- [ ] Competing-interests statement supplied.
- [ ] Acknowledgments supplied.
- [ ] Institutional ethics/non-human-subjects determination supplied.
- [ ] Generative-AI/AI-assisted coding and writing disclosure aligned to journal policy.
- [ ] All authors approve the final manuscript and repository release.

**Gate:** Every applicable item in Section E is required before submission.

## F. Citations and related work

- [x] Existing 15 reference identities verified.
- [x] Official NeurIPS RAG link used.
- [x] Closest DDI alert, contextual algorithm, outcomes, ExDDI, MedRAG, and provenance sources added.
- [x] Mutable organizational pages have access dates.
- [x] Non-peer-reviewed 2026 overlap labeled as a preprint.
- [ ] Librarian or second researcher reruns the targeted search immediately before submission.
- [ ] Decide whether the target journal permits/encourages citing the 2026 preprint.
- [ ] Reformat every reference to the selected journal's style and verify DOI/link resolution.

## G. Figures, tables, accessibility, and numerical QA

- [x] New authority-boundary Mermaid source created.
- [x] New evidence-flow Mermaid source created.
- [x] Core result tables included in v2.
- [ ] Render figures to journal-accepted vector/raster formats.
- [ ] Visually inspect figures at print and screen sizes.
- [ ] Add final captions, legends, abbreviations, and alt text.
- [ ] Check color contrast and grayscale interpretation.
- [ ] Confirm table/figure limits for the selected article type.
- [ ] Independently recalculate every number against raw JSON/CSV.
- [ ] Confirm that 73.3% is described as a purposive-suite proportion, not population accuracy.

## H. Target-journal compliance

- [ ] Corresponding author selects the target journal and article type.
- [ ] Verify current aims/scope and current instructions on the submission date.
- [ ] Verify title, structured abstract headings, word count, reference count, and table/figure limits.
- [ ] Verify data/code availability, repository, archival, and persistent-identifier requirements.
- [ ] Verify reporting guideline requirements for a design-science/formative software study.
- [ ] Verify patient/public involvement statement requirements.
- [ ] Verify APCs, waivers, and funder open-access requirements.
- [ ] Tailor cover letter to the incremental contribution and negative formative evidence.

## I. Final pre-submission verification

- [ ] No credential, token, patient data, or sensitive endpoint appears in the manuscript or remediated release.
- [ ] Repository URL resolves to the exact safe archival tag/DOI.
- [ ] All manuscript placeholders are resolved.
- [ ] All abbreviations are defined at first use.
- [ ] All in-text citations have one matching reference and vice versa.
- [ ] All numerical claims match the claim map and raw evidence.
- [ ] Original paper and historical artifacts remain unchanged.
- [ ] Git worktree is clean on the research branch.
- [ ] Pharmacist-informatics and methods reviewers have read the final draft.
- [ ] All authors provide final approval.

## Final gate

Submission is authorized only when Sections B, E, H, and I are complete, all claims remain within the evidence map, and any incomplete items in C, D, F, or G are explicitly acceptable for the selected formative article type. Until then, the status remains **NO-GO FOR SUBMISSION**.
