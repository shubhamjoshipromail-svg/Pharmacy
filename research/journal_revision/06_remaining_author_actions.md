# Remaining Author Actions Before Submission

This checklist is prioritized by submission risk. Items marked **blocking** should be completed before the manuscript is sent to any journal or reviewers are directed to the repository.

## Priority 0 — Immediate security and data protection

- [ ] **BLOCKING: Revoke and rotate the exposed Postgres credential** found in `app/core/config.py`, `scripts/import_ddinter.py`, and `alembic.ini`.
- [ ] **BLOCKING: Determine whether the exposed database is still reachable and inspect provider/access logs** for unauthorized access. Do not publish the credential in an issue, manuscript, or remediation note.
- [ ] **BLOCKING: Confirm whether the database contains any real or identifiable patient data.** If it does or may have, follow institutional incident-response and legal/privacy procedures.
- [ ] **BLOCKING: Remove secrets from active source and Git history** using an approved history-rewrite process, then invalidate old clones/deployments as appropriate.
- [ ] Run a complete secret scan across the repository and history; record the tool/version/date and remediation result.
- [ ] Replace live defaults with a non-secret local/test configuration and fail closed when required environment variables are absent.
- [ ] Restrict CORS, remove wildcard production access, and document that the current prototype must not receive real patient data.

## Priority 1 — Reproducible research package

- [ ] **BLOCKING: Record the exact DDInter release/version and access date.** The current named partitions are not enough.
- [ ] Record SHA-256 checksums for every source file and state the DDInter license/attribution obligations.
- [ ] Report import accounting: raw rows, duplicate rows, mapped rows, quarantined rows, inserted canonical interactions, inserted assertions, and reasons for exclusion.
- [ ] Separate source-derived rows from all synthetic/manual fixtures and publish fixture-adjusted profile counts.
- [ ] Create a clean database migration. The current Alembic `upgrade()` is empty and does not reconstruct the schema.
- [ ] Pin Python and frontend dependencies; preserve lockfiles and document runtime versions.
- [ ] Create an isolated local test database or container workflow with no live credential.
- [ ] Make the formative evaluator transactional or add deterministic cleanup/teardown.
- [ ] Rerun the 26 scenarios from a fresh database and record:
  - [ ] Git commit SHA and tag.
  - [ ] Operating system and hardware.
  - [ ] Python, Postgres, and dependency versions.
  - [ ] Migration revision.
  - [ ] Source/fixture hashes.
  - [ ] Start/end timestamps.
  - [ ] Scenario-level outputs and logs.
- [ ] Add the commit SHA and environment metadata directly to generated JSON/Markdown results.
- [ ] Archive the safe code and synthetic research package with a DOI, if possible.

## Priority 2 — Minimum empirical strengthening

- [ ] **BLOCKING: Add at least one independently specified validation component.** A clinical trial is not required for this article type. Choose one or preferably two of the following:
  - [ ] A transparent reference set of 20–50 drug-interaction cases with expected stored-result behavior and documented source/adjudication.
  - [ ] A medication-normalization benchmark covering exact names, brands, ingredients, combination products, NDCs, misspellings, ambiguous names, unmatched names, and service failures.
  - [ ] An independent code/evaluation review by a second researcher.
- [ ] If the LLM remains central to the title and contribution, complete the explanation-boundary evaluation:
  - [ ] Freeze exact structured context, label excerpts, prompt version, model ID, and raw response.
  - [ ] Include valid, malformed, wrong-drug, wrong-severity, invented-source, unsupported-management, and prompt-injection cases.
  - [ ] Score each criterion in the committed rubric; report criterion-level results, not only totals.
  - [ ] Use a second reviewer for a subset and report agreement descriptively.
  - [ ] Do not label the result clinical accuracy or safety.
- [ ] Measure core-check latency over a specified number of runs in a documented environment.
- [ ] If making any cost claim, measure actual hosting, database, network, and LLM costs in a defined workload. Otherwise keep cost as future work.

## Priority 3 — Engineering evidence and architecture corrections

- [ ] Convert the architecture scenarios into isolated automated unit/integration tests.
- [ ] Add tests for:
  - [ ] RxNorm timeout and network failure.
  - [ ] Placeholder warnings in check results.
  - [ ] Import idempotency and quarantine persistence.
  - [ ] DFI/DDSI/duplication ingestion if claimed.
  - [ ] Duplicate active medication rows and self-pair counts.
  - [ ] Checks with fewer than two verified medications and attempted-run auditing.
  - [ ] Acknowledgment expiry/deactivation.
  - [ ] Override semantics.
  - [ ] Malformed/non-object LLM JSON and incorrect field types.
  - [ ] Source-name and severity preservation.
  - [ ] OpenFDA ambiguity, timeout, and non-404 failure.
  - [ ] Authentication/authorization after implementation.
- [ ] Correct or explicitly document run-level `sources_used`, which is currently fixed to DDInter.
- [ ] Define how multiple assertions should be selected or reconciled for explanation context; avoid silently using the first row.
- [ ] Persist exact OpenFDA label identifiers, retrieved text or hash, retrieval time, and query path with each explanation.
- [ ] Replace custom output checking with a strict typed schema and source/severity consistency checks.
- [ ] Add authentication, route authorization, reliable user identity, and a production audit strategy before any real-user study.

## Priority 4 — Scholarly framing and manuscript completion

- [ ] Conduct a focused literature search for comparable DDI CDS, provenance-aware CDS, templated explanations, and LLM-grounded clinical systems.
- [ ] Add a related-work comparison table and make the novelty claim proportional to that search.
- [ ] Verify all 15 references in `05_journal_ready_manuscript.md` against the target journal’s style and current source pages.
- [ ] Replace every remaining bracketed placeholder in the manuscript.
- [ ] State which design requirements were specified prospectively and which were reconstructed post hoc.
- [ ] Keep the primary claim limited to architecture behavior under synthetic conditions.
- [ ] Do not claim:
  - [ ] Clinical validation, accuracy, sensitivity, specificity, safety, or benefit.
  - [ ] Complete DDI/DFI/DDSI coverage.
  - [ ] Alert-fatigue reduction or improved pharmacist decisions.
  - [ ] Strict RAG or verified factual grounding.
  - [ ] HIPAA compliance, FDA status, or deployment readiness.
  - [ ] Cost-effectiveness, frugality, or suitability for low-resource pharmacies without data.
- [ ] Use “pharmacist-oriented prototype,” not “pharmacist-facing system,” unless actual pharmacist users are evaluated.
- [ ] Use “audit-oriented persistence,” not “audit trail” or “compliance-grade audit.”
- [ ] Use “stored severity-label difference,” not “clinical source disagreement,” unless source quality and independence are analyzed.
- [ ] Report database counts as timestamped observations and clearly identify fixtures.

## Priority 5 — Figures, tables, and supplementary material

- [ ] Render `research/diagrams/overall_architecture.mmd` as a publication-quality vector figure.
- [ ] Render and revise `research/diagrams/llm_explanation_boundary.mmd` to show validation and provider-failure paths.
- [ ] Render `research/diagrams/evaluation_workflow.mmd` after updating it to match all 26 scenarios, not only a subset.
- [ ] Add accessible captions, abbreviations, and alt text.
- [ ] Include the full scenario matrix and machine-readable results as supplementary material.
- [ ] Include data/import provenance and the claim–evidence table as supplementary material if the journal permits.
- [ ] Ensure journal table/figure limits are met.

## Priority 6 — Authorship, ethics, licensing, and disclosures

- [ ] **BLOCKING: Add a root software license** selected by the copyright holder(s).
- [ ] Add a third-party data notice describing DDInter’s CC BY-NC-SA 4.0 terms and any restrictions on derived data redistribution or commercial use.
- [ ] Confirm software-license and data-license compatibility for the intended release; obtain legal/institutional review if needed.
- [ ] Supply author names, degrees, affiliations, ORCID identifiers, and corresponding-author details.
- [ ] Complete CRediT author contributions.
- [ ] Supply funding and grant information.
- [ ] Supply conflicts of interest, including any model-provider, hosting-provider, or data-source relationships.
- [ ] Obtain and report the institutional ethics/human-subjects determination for the software/synthetic study.
- [ ] Obtain separate approval or exemption before pharmacist interviews, usability testing, or use of real records.
- [ ] Add acknowledgments and verify permission to name contributors.
- [ ] Confirm that no protected health information, credentials, private endpoints, or confidential logs are in supplementary files.

## Priority 7 — Journal selection and submission checks

- [ ] Select the target journal before final formatting.
- [ ] Most realistic first target after remediation: JMIR Formative Research.
- [ ] Alternative: JAMIA Open Application Note for a shorter software paper, or Research and Applications after stronger evaluation.
- [ ] Alternative: Frontiers in Digital Health Technology and Code/Methods only after validation requirements are met.
- [ ] Check current article type, word count, abstract headings, table/figure limits, data policy, repository requirements, APCs, and patient/community abstract requirements.
- [ ] Create a target-journal compliance checklist and line-by-line response.
- [ ] Ask a pharmacist-informatics expert and a methods reviewer to read the final manuscript before submission.
- [ ] Confirm that the repository URL resolves to the remediated tag/DOI, not the unsafe historical snapshot.

## Final go/no-go gate

Do not submit until all of the following are true:

- [ ] The exposed credential is revoked and repository history is remediated.
- [ ] The code release is safely licensed and archived.
- [ ] The evaluation can be rerun from a clean environment without external secrets.
- [ ] Source version, checksums, import accounting, and fixture-adjusted results are documented.
- [ ] At least one independent/reference validation component is complete.
- [ ] LLM results are either evaluated or removed from the central empirical claims.
- [ ] All author, ethics, funding, conflict, data, and code statements are complete.
- [ ] No unsupported clinical, economic, regulatory, or deployment claims remain.
