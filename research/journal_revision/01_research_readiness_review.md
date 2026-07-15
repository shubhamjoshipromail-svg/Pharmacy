# RxCheck Research-Readiness Review

## Review scope and source snapshot

This review treats `paper/rxcheck_manuscript_0.1v.md` as read-only source material and evaluates the repository at Git commit `6b763c03a69e33031f196eceb598899ee08a1cba` on branch `research/journal-ready-paper`. The review uses the application code, tests, recorded research outputs, diagrams, README, and manuscript. No live database or external-model evaluation was rerun because the current repository contains a live-looking database credential and its research evaluator writes persistent fixtures.

The original manuscript is preserved at `paper/rxcheck_manuscript_0.1v.md`. Its Git object hash at the start of this review was `cd5c4ab332461544a1f083bfcfd65fd60b2b49e4`.

## 1. Project and paper diagnosis

RxCheck is a full-stack, pharmacist-oriented research prototype for reviewing stored drug-interaction records. It is not a trained clinical prediction model and it is not an autonomous clinical reasoning system. Its core check path is deterministic: active, normalized medication identifiers are matched against interaction rows in Postgres; drug-disease findings are filtered by recorded active conditions; and each run and finding can be persisted. An optional Anthropic endpoint generates prose only after a finding exists. OpenFDA label text is optional context for that explanation path, not a source used to create findings.

The strongest scholarly contribution is therefore an architecture and safety-boundary contribution: RxCheck instantiates and formatively evaluates a pattern in which a generative model is placed downstream of deterministic evidence retrieval, while unresolved medication inputs, source assertions, review state, and finding snapshots remain explicit. The most defensible name for this pattern is **evidence-bounded explanation architecture**. “Evidence-bounded” is preferable to “evidence-bound AI” in the article because it describes an implemented system boundary without implying that every generated sentence is demonstrably grounded.

The best article type is a **design-science health-informatics system paper with a formative architecture evaluation**. A secondary fit is a software/application note after reproducibility, licensing, and security defects are corrected. The work is not currently defensible as a clinical-effectiveness study, diagnostic-accuracy study, machine-learning model paper, cost-effectiveness analysis, or production implementation study.

Current publication readiness: **promising artifact, not submission-ready**. The paper has unusually good self-limitation and repository-to-claim documentation, but the evidence remains architecture-focused, the scholarly positioning is incomplete, and several security and reproducibility problems would cause immediate editorial concern.

## 2. Strongest academic framing

### Proposed framing

> RxCheck is a design-science instantiation and formative evaluation of an evidence-bounded explanation architecture for drug-interaction review. Deterministic, database-backed logic creates findings; an optional LLM renders an existing finding into prose; and explicit rejection, provenance, patient-context gating, and review-state persistence define the boundary between evidence and generation.

This framing is stronger than “frugal clinical AI” for the present evidence. The repository demonstrates service separation and use of open-source components, but it contains no measured deployment cost, cost comparison, total-cost model, low-bandwidth experiment, or economic evaluation. Cost-consciousness can remain a design consideration, not the title-level contribution.

### Central research contribution

The contribution is a concrete, inspectable architecture pattern and implementation showing how a generative explanation layer can be prevented from determining interaction existence in one pharmacy-oriented prototype. Supporting contributions are explicit non-resolution of uncertain medication names, preservation of source-specific assertions, condition-gated DDSI logic, and persisted review state.

### Defensible research questions

Primary question:

> To what extent does the RxCheck prototype enforce a predefined evidence boundary in which deterministic database logic creates drug-interaction findings and a generative model is limited to explaining a persisted finding?

Secondary questions:

1. How does the artifact represent uncertain medication identity, source provenance, patient-condition context, and longitudinal review state?
2. Which architecture requirements are supported by the current synthetic evaluation, and which safety, clinical, and operational claims remain untested?

These questions match the evidence. They do not assume that the system is clinically accurate, useful, safe, low-cost, or complete.

## 3. Strongest parts of the existing work

1. **A clear deterministic/generative boundary.** `app/services/orchestrator.py` creates findings from stored rows; `app/api/interactions.py` exposes explanation only by finding ID. This is the most coherent and publishable idea in the project.
2. **Explicit non-resolution.** `app/services/normalization.py` creates deterministic placeholder identifiers for unmatched input, and the orchestrator excludes placeholder drugs. This is a useful fail-visible design pattern, provided the UI makes incomplete coverage salient.
3. **Provenance-oriented data model.** `InteractionSourceAssertion` separates canonical interactions from source-specific severity, identifiers, import time, and raw payload. This is more defensible than claiming a single authoritative label.
4. **Context-gated drug-disease logic.** DDSI rows are queried only for active patient conditions. The synthetic evaluation exercises absent, present, and resolved-condition behavior.
5. **Longitudinal review-state modeling.** Check runs, finding snapshots, acknowledgments, overrides, selected audit events, and explanation records create an inspectable prototype history.
6. **Conservative existing manuscript language.** The draft repeatedly distinguishes architecture behavior from clinical validation and explicitly rejects claims about patient outcomes, HIPAA compliance, FDA clearance, complete coverage, alert-fatigue reduction, and cost-effectiveness.
7. **Traceable research artifacts.** The architecture inventory, claim/evidence matrix, data profile, evaluation plan, results, failure-mode analysis, and explanation rubric create a useful audit trail.

## 4. Methodological and evidentiary weaknesses

### Submission-critical weaknesses

- **Exposed database secret.** A credential-bearing Postgres URL is committed in `app/core/config.py`, `scripts/import_ddinter.py`, and `alembic.ini`. This requires immediate credential revocation/rotation and repository-history remediation by the author. It also prevents safe independent reruns from the current default configuration.
- **No reproducible data package.** The imported DDInter files are absent, their exact release/version and checksums are not recorded, the database snapshot is unavailable, and the profile includes synthetic fixtures. The reported database totals cannot be independently reconstructed from the repository.
- **Database setup is not reproducible.** The only Alembic migration has an empty `upgrade()`. Runtime import calls `Base.metadata.create_all`, while Postgres extensions and expected tables are handled separately. This is not a controlled schema-versioning record.
- **Dependency versions are not pinned.** `requirements.txt` lists package names without versions or hashes. The recorded pytest environment is described but not lockfile-reproducible.
- **Evaluation is coupled to a persistent configured database.** `research/evaluate_rxcheck.py` writes multiple fixtures and does not provide an automatic transactional teardown. The results are a recorded historical run, not a clean rerun from archived inputs.
- **No independent clinical benchmark.** There is no labeled interaction reference set, sensitivity/specificity estimate, normalization benchmark, expert adjudication, usability evaluation, or explanation-quality scoring. That is acceptable for a narrow architecture paper only if claims remain correspondingly narrow.
- **No software license.** The public repository has no root license, limiting reuse and weakening software-publication positioning. DDInter data have separate noncommercial share-alike terms that also need an explicit compatibility and attribution statement.

### Important technical caveats that the paper must state

- The real importer handles DDI-formatted files only. The profiled DFI and DDSI counts are one and two, respectively, and include evaluation/manual fixtures; architecture support must not be presented as meaningful real-source coverage.
- The real importer records severity and raw rows but does not import rich mechanism or management text from the named CSV files.
- `InteractionCheckRun.sources_used` is currently hard-coded to `DDInter`, even when a synthetic/manual assertion participates in a finding.
- The “hub score” is a database degree count, not a patient-specific or validated risk score.
- The LLM context uses the first source assertion’s mechanism and management, even when several assertions exist; source disagreement is not synthesized at the explanation boundary.
- LLM output checking is custom and shallow: required-key presence, `sources_used` list type, and a database-wide name scan. It does not enforce a formal schema, confidence vocabulary, citation entailment, clinical factuality, or injection resistance.
- OpenFDA generic-name fallback can return an unintended label; label content is cached only in memory and is not versioned with the explanation evidence.
- Core checking is independent of RxNorm only after medication concepts have been stored. New or unfamiliar medication entry can still fail when RxNorm is unavailable, and network exceptions do not reliably become placeholders.
- A check with fewer than two verified active medications returns without a persisted run, so not every attempted check is auditable.
- Authentication and authorization are absent. A default “pharmacist” database row is an application convenience, not verified professional identity.
- CORS includes `*` with credentials allowed, sensitive patient fields exist, and audit events are neither immutable nor comprehensive.

## 5. Claims supported by the repository

The following claims are defensible when scoped to the inspected commit and tested paths:

- RxCheck is a pharmacist-oriented prototype interface, although actual users are not authenticated as pharmacists.
- The current implementation targets Postgres and uses FastAPI/SQLAlchemy with a React/Vite frontend.
- The core orchestrator determines interaction existence from stored interaction rows rather than from the LLM.
- Active placeholder drugs are excluded from checking, and placeholder medication entries remain stored for review.
- Stored DDI pairs are canonicalized; DFI is drug-gated; DDSI is gated by an active matching condition.
- Canonical interactions can retain multiple source assertions and raw source payloads.
- Check runs and findings persist selected runtime snapshots when a check has at least two verified active medications.
- Acknowledgment can suppress presentation of a later finding; severity escalation can invalidate lower-severity suppression.
- Overrides are persisted but do not alter later check behavior.
- The explanation endpoint is downstream of an existing finding.
- The recorded June 9, 2026 evaluation artifact reports 26 of 26 synthetic scenarios passing and no external API calls on the exercised core paths.
- The recorded database profile reports 152,416 interaction rows and 172,714 source assertions at one timestamp, including identified research fixtures.

## 6. Claims that are overstated, unclear, or unsupported

- **“Strict RAG”** is too strong. The system constructs a bounded context from stored fields and optional label excerpts, but it lacks passage-level retrieval evaluation, citation entailment, comprehensive schema enforcement, and completed explanation scoring.
- **“Evidence-bound AI”** can be misunderstood as a guarantee that generation is evidentially faithful. Use “evidence-bounded explanation architecture” and explicitly state that the boundary reduces authority but does not prove factuality.
- **“Frugal” or “for budget-constrained pharmacies”** is only a design rationale. There is no user/context study, measured deployment cost, comparative cost analysis, or evidence from resource-constrained pharmacies.
- **“Source disagreement”** is structurally supported, but the profiled database is almost entirely DDInter. A single manual assertion and synthetic conflict do not demonstrate operational multi-source reconciliation.
- **“Drug-food and drug-disease support”** is true at the schema/orchestrator level, not as meaningful imported coverage.
- **“Reproducible evaluation”** is not yet justified. The code is visible, but data, schema migration, dependency lock, clean database fixture, teardown, commit metadata in outputs, and a safe configuration are missing.
- **“Schema-validated LLM output”** should be narrowed to “custom parsed and checked for required keys and unexpected stored drug names.”
- **“Audit trail”** should be narrowed to “audit-oriented persistence of selected events and snapshots.”
- **“Working architecture prototype”** is supportable only as a repository artifact with a recorded synthetic run; it is not independently verified in this review because safe rerun prerequisites are absent.
- Claims of clinical accuracy, safety, usefulness, alert-fatigue reduction, complete coverage, cost-effectiveness, regulatory status, or deployment readiness are unsupported.

## 7. Missing work

### Missing evaluation

- A clean, isolated, transactional rerun of all architecture scenarios from a fresh database.
- A medication-normalization benchmark with realistic exact, brand, combination-product, NDC, misspelled, ambiguous, and failure inputs.
- A small, openly specified interaction reference set to estimate retrieval behavior without claiming comprehensive clinical validity.
- Completed LLM explanation evaluation using frozen prompts, contexts, model version, raw outputs, two reviewers for a subset, and criterion-level results.
- Latency measurements for core checks and optional explanations, with environment and sample size.
- Unit/integration tests for the orchestrator, API authorization boundary once implemented, import idempotency, external failures, and malformed LLM outputs.

### Missing documentation and artifacts

- Exact DDInter release/version, download/access date, license, file checksums, row counts before/after quarantine, and transformation log.
- Reproducible schema migration and dependency lock.
- Root software license and third-party data attribution/compatibility statement.
- Rendered publication-quality architecture, evidence-boundary, and evaluation-flow figures.
- Author names, affiliations, contributions, funding, acknowledgments, conflicts, and corresponding-author details.
- Ethics determination explaining why the reported synthetic/software study did or did not require human-subjects review.
- A security disclosure describing credential remediation without publishing the secret.

## 8. Prioritized improvements

### Required before submission

1. Revoke and rotate the exposed database credential; remove it from active files and repository history; verify that no other secrets or real patient data were exposed.
2. Create a safe local/test configuration and rerun the evaluation in a fresh, isolated database with automatic teardown. Archive commit SHA, environment, schema revision, and outputs.
3. Replace the empty migration with a reproducible schema history and pin dependencies.
4. Record the exact DDInter source release, access date, terms, checksums, preprocessing, mapped/quarantined counts, and fixture-adjusted profile totals.
5. Add a software license and a data-license/attribution notice compatible with intended scholarly distribution.
6. Complete at least one modest empirical validation beyond self-authored architecture assertions: preferably an independent reference-case check plus completed explanation-boundary scoring. A clinical trial is not required for the proposed article type.
7. Replace all citation placeholders with verified sources and conduct a focused related-work comparison demonstrating what is and is not novel.
8. Remove or narrow every clinical, “strict RAG,” frugality, reproducibility, and multi-source claim that exceeds the evidence.
9. Add author, funding, conflict, ethics, data-availability, and code-availability statements.

### Strongly recommended

1. Convert the 26 scenarios into isolated automated tests and report scenario families, not only a perfect aggregate count.
2. Add negative and malformed-output tests for the LLM boundary, including source injection, wrong drug names, wrong severity, invalid JSON type, invented sources, and unsupported management text.
3. Persist and version every explanation input, including exact assertion selection and OpenFDA label identifiers/text hashes.
4. Clarify or revise `sources_used`, first-assertion selection, duplicate-medication pair counts, and incomplete-check warnings.
5. Render and number the existing Mermaid diagrams; add a table that maps design requirements to code and evaluation evidence.
6. Obtain pharmacist review of design requirements and a small formative usability walk-through if feasible.
7. Add authentication/authorization and strict production CORS before any deployment or real-user study.

### Optional future work

1. Import and evaluate genuine DDInter 2.0 DFI, DDSI, and therapeutic-duplication data.
2. Add FHIR/SMART integration only after terminology, security, and governance are mature.
3. Compare explanation approaches, including no-LLM templating, local models, and proprietary APIs.
4. Measure deployment cost and operational requirements in a defined setting before reintroducing “frugal” as a primary claim.
5. Conduct a pharmacist usability study, then a prospective workflow study; patient outcomes are a later-stage question.

## 9. Bottom line

The project contains a publishable design idea and an unusually candid prototype record. Its strongest paper is about **where generative AI is not allowed to act**, not about superior clinical performance. A journal submission should present the artifact as a formative design-science case, report the 26-scenario run as architecture verification, and treat clinical accuracy, explanation quality, user benefit, security, and deployment as open questions. With credential remediation, reproducible packaging, a completed modest validation, and sharper related-work comparison, the work could become a credible formative informatics submission.
