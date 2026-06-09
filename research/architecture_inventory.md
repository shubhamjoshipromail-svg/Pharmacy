# RxCheck Architecture And Design Decision Inventory

## Purpose

This inventory prevents a design science manuscript from reducing RxCheck to a generic "drug interaction checker with an LLM." It records the important decisions that are observable in the current repository, the problems those decisions address, and the limits on claims that can be made from them.

The inventory describes a **research prototype**, not a clinically validated system. Code evidence refers to the current repository. Evaluation evidence refers to the synthetic formative architecture evaluation generated on June 9, 2026, unless otherwise stated.

## How To Use This Inventory

- Use the **Design and implementation** entries to describe the artifact.
- Use the **Evaluation evidence** entries only for the behavior actually exercised by synthetic fixtures.
- Use the **Safe wording and limitations** text to constrain manuscript claims.
- Do not infer clinical accuracy, complete interaction coverage, FDA clearance, HIPAA compliance, or operational readiness from implementation evidence.

---

## A. Medication Normalization And Uncertainty Handling

### A1. Ingredient-Level RxNorm Normalization

1. **Design decision:** Normalize medication input to an ingredient-level RxCUI before interaction checking.
2. **Problem it addresses:** Brand names, synonyms, typographical variants, and product-level identifiers can refer to the same active ingredient. A common identifier is needed for deterministic pair matching.
3. **Implementation details:** `normalize_drug_name()` checks local aliases, calls RxNorm when necessary, and uses the RxNorm related-concept endpoint with `tty=IN` to resolve a returned concept to an ingredient concept. The normalized `Drug` stores an RxCUI, preferred name, and term type.
4. **Code evidence:** `app/services/normalization.py::_resolve_ingredient_concept`; `normalize_drug_name`; `app/models/drug.py::Drug`.
5. **Evaluation evidence:** `rxnorm_not_required_at_check_time` verifies that checks consume already stored RxCUIs. The formative evaluator deliberately does not test live RxNorm accuracy.
6. **Manuscript section:** Artifact design; normalization subsystem; external-service boundary.
7. **Safe wording and limitations:** Safe: "RxCheck maps medication input toward ingredient-level RxNorm concepts before checking stored interactions." Limitation: the repository does not establish normalization accuracy across real medication vocabularies, combination products, local formularies, or ambiguous names.

### A2. Local Exact Alias Lookup First

1. **Design decision:** Search the local `drug_aliases` table before making a network request.
2. **Problem it addresses:** Repeated external calls add latency, network dependence, and recurring operational burden.
3. **Implementation details:** The alias comparison lowercases the stored alias and normalized input. Brand/tradename aliases return `matched_brand`; other local aliases return `matched_exact`.
4. **Code evidence:** `app/services/normalization.py:normalize_drug_name` local alias branch; `BRAND_ALIAS_KINDS`; `app/models/drug.py::DrugAlias`.
5. **Evaluation evidence:** Not directly exercised by the 26-scenario orchestrator evaluation. The cost analysis documents the intended local-resolution behavior.
6. **Manuscript section:** Design rationale; cost-conscious architecture.
7. **Safe wording and limitations:** Safe: "Previously stored aliases can be resolved locally before contacting RxNorm." Limitation: matching is case-insensitive but not a general lexical or multilingual normalization strategy.

### A3. RxNorm Exact/Normalized Search

1. **Design decision:** Use RxNorm's `rxcui.json?name=...&search=2` search before fuzzy matching.
2. **Problem it addresses:** Exact or normalized matches should be preferred over less certain approximate candidates.
3. **Implementation details:** The service selects the first RxNorm ID returned, obtains its properties, resolves it to an ingredient concept, upserts the drug, and stores the typed input as a brand or synonym alias.
4. **Code evidence:** `app/services/normalization.py::_search_exact`; exact-hit branch in `normalize_drug_name`.
5. **Evaluation evidence:** No live external-API evaluation is claimed.
6. **Manuscript section:** Normalization workflow.
7. **Safe wording and limitations:** Safe: "The normalization workflow attempts RxNorm exact/normalized search before approximate search." Limitation: taking the first returned ID is an implementation heuristic, not evidence that the selected concept is always clinically correct.

### A4. RxNorm Fuzzy Lookup With Confidence Bands

1. **Design decision:** Use RxNorm `approximateTerm` results when exact lookup fails, with separate auto-resolution and human-confirmation bands.
2. **Problem it addresses:** Pharmacist-entered names may contain spelling errors, while low-confidence automatic mapping could silently select the wrong drug.
3. **Implementation details:** Up to five candidates are ingredient-resolved and sorted by score, rank, and name. A top score greater than 8 auto-resolves; scores from 4 through 8 return candidates without inserting a medication; lower scores proceed toward NDC or unresolved handling.
4. **Code evidence:** `app/services/normalization.py::_search_fuzzy`; fuzzy branch in `normalize_drug_name`; `app/api/patients.py::create_patient_medication`.
5. **Evaluation evidence:** The architecture evaluation does not assess the empirical calibration of these thresholds.
6. **Manuscript section:** Human-in-the-loop normalization; uncertainty handling.
7. **Safe wording and limitations:** Safe: "RxCheck uses implementation-defined score bands to distinguish automatic fuzzy resolution from candidate confirmation." Limitation: the thresholds are not clinically validated or calibrated against a labeled normalization benchmark.

### A5. NDC Lookup

1. **Design decision:** Recognize 10- or 11-digit input, including dashed forms, and query RxNorm using `idtype=NDC`.
2. **Problem it addresses:** Medication entry may use package identifiers rather than names.
3. **Implementation details:** Non-digits are removed; input is treated as NDC-like when 10 or 11 digits remain. A successful result is resolved to an ingredient, stored, and returned as `matched_ndc`.
4. **Code evidence:** `app/services/normalization.py::_looks_like_ndc`; `_clean_ndc`; `_search_ndc`; NDC branch in `normalize_drug_name`.
5. **Evaluation evidence:** Not evaluated against live NDC fixtures.
6. **Manuscript section:** Normalization input modes.
7. **Safe wording and limitations:** Safe: "The service includes an RxNorm-backed path for 10- or 11-digit NDC-like input." Limitation: it does not demonstrate complete package-code normalization, NDC format validation, or handling of every 10-to-11-digit conversion convention.

### A6. Alias Learning

1. **Design decision:** Persist successful typed inputs as aliases for later local resolution.
2. **Problem it addresses:** Repeated brands, synonyms, and misspellings should not require repeated remote normalization.
3. **Implementation details:** Exact results become `brand` or `synonym` aliases, high-scoring fuzzy inputs become `misspelling` aliases, and NDC-like inputs are currently stored as `synonym`. A uniqueness constraint and application lookup avoid duplicate alias rows for the same alias kind and RxCUI.
4. **Code evidence:** `app/services/normalization.py::add_alias`; exact, fuzzy, and NDC branches; `app/models/drug.py::DrugAlias`.
5. **Evaluation evidence:** The current evaluator establishes check-time independence from RxNorm after concepts are stored, not alias-learning accuracy.
6. **Manuscript section:** Learning/caching design; cost-conscious architecture.
7. **Safe wording and limitations:** Safe: "Successful normalizations populate a reusable local alias table." Limitation: this is database persistence, not machine learning, and an incorrectly accepted mapping could be reused until reviewed or corrected.

### A7. Drug Upsert By RxCUI

1. **Design decision:** Treat RxCUI as the drug primary key and update an existing row rather than creating duplicate concepts.
2. **Problem it addresses:** Multiple names or searches can resolve to the same ingredient.
3. **Implementation details:** `get_or_create_drug()` loads by RxCUI, can convert a matching placeholder row to non-placeholder, refreshes preferred name/TTY, and updates synchronization time.
4. **Code evidence:** `app/services/normalization.py::get_or_create_drug`; `app/models/drug.py::Drug.rxcui`.
5. **Evaluation evidence:** Not separately evaluated.
6. **Manuscript section:** Data model; normalization persistence.
7. **Safe wording and limitations:** Safe: "RxCUI-keyed upsert behavior reduces duplicate normalized drug concepts." Limitation: preferred-name replacement is not versioned, and RxNorm concept retirement/remapping is not comprehensively managed.

### A8. Unresolved Entries And Deterministic Placeholder IDs

1. **Design decision:** Preserve unmatched input in both an unresolved-entry record and a placeholder `Drug`.
2. **Problem it addresses:** Rejecting or discarding unresolved medication text would hide uncertainty and prevent later review.
3. **Implementation details:** A normalized-input record tracks occurrence count and last-seen time. A SHA-1-derived identifier prefixed with `placeholder:` creates a stable placeholder RxCUI for the normalized text. The placeholder has `tty="PLACEHOLDER"` and `is_placeholder=true`.
4. **Code evidence:** `app/services/normalization.py::_placeholder_rxcui`; `_record_unresolved`; `app/models/drug.py::UnresolvedDrugEntry`; `Drug.is_placeholder`.
5. **Evaluation evidence:** `placeholder_visible_but_excluded` and `placeholder_drug_exclusion` passed with synthetic fixtures.
6. **Manuscript section:** Uncertainty representation; safety-oriented design.
7. **Safe wording and limitations:** Safe: "Unresolved input is preserved as an explicitly marked placeholder rather than silently treated as a verified concept." Limitation: SHA-1 is used only for deterministic local identity, not security; the current workflow lacks a complete pharmacist resolution queue.

### A9. Non-Resolution And Candidate-Confirmation Behavior

1. **Design decision:** Distinguish low-confidence candidate review from complete non-resolution.
2. **Problem it addresses:** Ambiguous candidates and no-match cases require different user responses.
3. **Implementation details:** Scores from 4 through 8 return HTTP 202 with candidates and do not create a medication. A no-match result creates a placeholder medication and returns a warning. Empty input also becomes an unresolved placeholder at the service layer, although API validation may constrain practical entry.
4. **Code evidence:** `app/services/normalization.py:normalize_drug_name`; `app/api/patients.py::create_patient_medication`; `add_medication`.
5. **Evaluation evidence:** Placeholder persistence/exclusion is evaluated; candidate-selection UX and live rejection behavior are not.
6. **Manuscript section:** Human-in-the-loop workflow; failure handling.
7. **Safe wording and limitations:** Safe: "Ambiguous fuzzy results request confirmation, while unmatched inputs remain visible as placeholders." Limitation: RxNorm network exceptions currently propagate rather than reliably entering the placeholder path.

### A10. Placeholder Visibility In The User Interface

1. **Design decision:** Show unresolved medications in the list with their raw input and an amber warning marker.
2. **Problem it addresses:** Excluded medications must remain visible so users can recognize incomplete checking.
3. **Implementation details:** `MedicationList` renders `raw_input` for placeholders, displays `!`, and provides the tooltip "Drug could not be verified — interactions may be incomplete." Verified medications show a green check and RxNorm tooltip.
4. **Code evidence:** `frontend/src/components/MedicationList.jsx`.
5. **Evaluation evidence:** The backend evaluator verifies stored visibility, not browser rendering. No formal usability evaluation has been performed.
6. **Manuscript section:** Interface design; uncertainty communication.
7. **Safe wording and limitations:** Safe: "The prototype visually distinguishes unresolved medications in the medication list." Limitation: a small badge and tooltip may be overlooked and have not been evaluated for comprehension or accessibility.

### A11. Placeholder Exclusion At The Orchestrator Boundary

1. **Design decision:** Exclude `is_placeholder=true` drugs before pair generation or interaction lookup.
2. **Problem it addresses:** A non-verified concept must not be treated as a real RxCUI and matched against interaction data.
3. **Implementation details:** The active-medication query joins `Drug` and filters `Drug.is_placeholder.is_(False)`. An equivalent helper exists in `app/services/checks.py`.
4. **Code evidence:** `app/services/orchestrator.py:run_interaction_check`; `app/services/checks.py::medications_for_interaction_checks`.
5. **Evaluation evidence:** `placeholder_drug_exclusion` and `placeholder_visible_but_excluded` passed.
6. **Manuscript section:** Deterministic checker; uncertainty boundary.
7. **Safe wording and limitations:** Safe: "Placeholder drugs are retained for review but excluded from interaction checking." Limitation: exclusion can make results incomplete, and the check response does not currently enumerate the excluded placeholders in a dedicated warning.

### A12. RxNorm Rate Limiting

1. **Design decision:** Insert at least 100 ms between RxNorm requests.
2. **Problem it addresses:** External public APIs should not be called without basic request pacing.
3. **Implementation details:** A process-global monotonic timestamp controls individual HTTP calls, and batch normalization also sleeps between names.
4. **Code evidence:** `app/services/normalization.py::_rate_limited_get_json`; `batch_normalize`.
5. **Evaluation evidence:** Not load-tested.
6. **Manuscript section:** External-service integration; operational considerations.
7. **Safe wording and limitations:** Safe: "The prototype applies simple client-side pacing to RxNorm calls." Limitation: the process-local mechanism is not a distributed rate limiter and does not coordinate multiple application workers.

---

## B. Database And Interaction Knowledge Representation

### B1. Postgres As The Current Database

1. **Design decision:** Use Postgres as the active persistence platform.
2. **Problem it addresses:** The imported interaction graph, source assertions, snapshots, arrays, and JSON payloads benefit from relational constraints and Postgres-native types.
3. **Implementation details:** SQLAlchemy reads `DATABASE_URL`, configures connection pooling, and models use Postgres `UUID`, `JSONB`, and `ARRAY`. Railway supplies the hosted deployment target.
4. **Code evidence:** `app/db/session.py`; `app/core/config.py`; Postgres dialect imports in `app/models/*.py`; `railway.toml`.
5. **Evaluation evidence:** The 26-scenario evaluation and data profile ran against the configured Postgres database.
6. **Manuscript section:** Technical architecture; deployment.
7. **Safe wording and limitations:** Safe: "The current prototype is implemented and evaluated with Postgres." Limitation: although the project began with SQLite-compatible substitutions, the current schema is not transparently interchangeable with SQLite because it now depends on Postgres-specific types and SQL behavior.

### B2. Environment-Configured Connection With Pool Health Checks

1. **Design decision:** Centralize database connection construction through application settings and SQLAlchemy sessions.
2. **Problem it addresses:** API requests and scripts require consistent transaction/session behavior and stale-connection detection.
3. **Implementation details:** The engine uses `pool_pre_ping=true`, pool size 5, and overflow 10. `get_db()` yields and closes a request-scoped session.
4. **Code evidence:** `app/db/session.py`.
5. **Evaluation evidence:** Successful evaluation, profiling, and pytest runs demonstrate connectivity in one configured environment.
6. **Manuscript section:** Implementation architecture; operational design.
7. **Safe wording and limitations:** Safe: "Database access is centralized through SQLAlchemy with basic pooled-connection health checks." Limitation: there is no reported concurrency, failover, or connection-pool performance evaluation.

### B3. UUID, JSONB, And ARRAY Storage Choices

1. **Design decision:** Use UUID identifiers for major entities, JSONB for structured snapshots/raw payloads, and Postgres arrays for source lists.
2. **Problem it addresses:** Globally unique identifiers support distributed creation; JSONB retains variable source/context structures; arrays preserve compact source snapshots.
3. **Implementation details:** UUIDs identify patients, users, interactions, check runs, medications, and explanations. JSONB stores source raw payloads, medication snapshots, LLM structured input, validation errors, token usage, and audit payloads. `ARRAY(String)` stores run/finding sources.
4. **Code evidence:** `app/models/interaction.py`; `app/models/check.py`; `app/models/audit.py`; `app/models/patient.py`.
5. **Evaluation evidence:** `source_assertion_preservation`, `check_run_persistence`, and `finding_snapshot_persistence` passed.
6. **Manuscript section:** Data architecture.
7. **Safe wording and limitations:** Safe: "Postgres-native UUID, JSONB, and array fields support flexible provenance and snapshot storage." Limitation: flexible JSON fields reduce schema-level validation, and no storage-growth or query-performance study has been performed.

### B4. Relational Constraints And Indexes

1. **Design decision:** Enforce important invariants through foreign keys, check constraints, unique constraints, and lookup indexes.
2. **Problem it addresses:** Application-only validation is insufficient for preventing malformed interaction structures and duplicate evidence rows.
3. **Implementation details:** Constraints enforce one interaction counterpart, type/counterpart consistency, ordered DDI pairs, unique interaction keys, unique source records, and unique run/interaction findings. Indexes cover drug, interaction, patient/time, audit target, severity, and external-ID lookup paths.
4. **Code evidence:** `app/models/interaction.py::__table_args__`; `app/models/check.py::__table_args__`; `app/models/drug.py::__table_args__`; `app/models/audit.py::__table_args__`.
5. **Evaluation evidence:** Canonical ordering and non-duplicated findings passed; index performance itself was not benchmarked.
6. **Manuscript section:** Data integrity; architecture rationale.
7. **Safe wording and limitations:** Safe: "The schema encodes selected interaction and provenance invariants at the database level." Limitation: these constraints do not establish semantic or clinical correctness of imported rows.

### B5. Canonical DDI Pair Ordering

1. **Design decision:** Store and query drug-drug pairs in lexicographic RxCUI order.
2. **Problem it addresses:** Without canonical order, A+B and B+A could become duplicate interactions or fail to match.
3. **Implementation details:** The database requires `drug_a_rxcui < drug_b_rxcui`; the orchestrator sorts each combination before a single tuple-`IN` query; the importer also sorts RxCUIs.
4. **Code evidence:** `app/models/interaction.py` `interactions_ddi_ordered`; `app/services/orchestrator.py` `canonical_pairs`; `scripts/import_ddinter.py::resolve_rows`.
5. **Evaluation evidence:** `canonical_drug_pair_ordering` passed.
6. **Manuscript section:** Deterministic checking algorithm; data integrity.
7. **Safe wording and limitations:** Safe: "Canonical RxCUI ordering gives each DDI pair one database orientation." Limitation: this assumes the interaction is symmetric for lookup; direction-specific effects are not represented as separate ordered edges.

### B6. Duplicate Prevention At Multiple Layers

1. **Design decision:** Prevent duplicate normalized drugs, interaction keys, source assertions, and per-run findings.
2. **Problem it addresses:** Re-imports and repeated checks should not multiply the same logical evidence.
3. **Implementation details:** RxCUI is the drug primary key. Unique indexes identify DDI/DFI/DDSI interactions. Assertions are unique by interaction, source, and source record ID. Findings are unique by run and interaction. The bulk DDInter importer uses `ON CONFLICT DO NOTHING`.
4. **Code evidence:** `app/models/drug.py`; `app/models/interaction.py`; `app/models/check.py`; `scripts/import_ddinter.py`.
5. **Evaluation evidence:** `duplicate_medication_does_not_duplicate_finding` observed one finding for the stored DDI.
6. **Manuscript section:** Data integrity; import architecture.
7. **Safe wording and limitations:** Safe: "The schema and importer reduce duplicate interaction and assertion records." Limitation: active duplicate medication rows are allowed; the evaluation observed that the pair-count metric can include a same-RxCUI self-pair even though the DDI finding is not duplicated.

### B7. Unified DDI, DFI, And DDSI Representation

1. **Design decision:** Represent drug-drug, drug-food, and drug-disease interactions in one `interactions` table with typed counterpart columns.
2. **Problem it addresses:** Common orchestration, source assertion, severity, and finding logic should work across interaction categories.
3. **Implementation details:** `interaction_type` selects DDI, DFI, DDSI, or therapeutic duplication. Exactly one of `drug_b_rxcui`, `food_id`, or `condition_id` must be present, and a check constraint aligns the counterpart with interaction type.
4. **Code evidence:** `app/models/enums.py::InteractionType`; `app/models/interaction.py::Interaction`.
5. **Evaluation evidence:** Synthetic DDI, DFI, and DDSI fixtures passed `severity_ranking_with_three_interaction_types`.
6. **Manuscript section:** Domain/data model.
7. **Safe wording and limitations:** Safe: "The schema can represent DDI, DFI, and DDSI records through a common interaction abstraction." Limitation: schema support does not imply comparable real-data coverage for all three types.

### B8. Condition-Gated DDSI

1. **Design decision:** Return a drug-disease interaction only when the patient has the matching active condition.
2. **Problem it addresses:** Showing every disease interaction associated with a medication would create clinically irrelevant false-positive alerts.
3. **Implementation details:** The DDSI query restricts `condition_id` to patient-condition rows with matching patient ID and `resolved_date IS NULL`. Resolving a condition sets the date rather than deleting history.
4. **Code evidence:** `app/services/orchestrator.py` DDSI query; `app/api/patients.py::resolve_patient_condition`; `app/models/patient.py::PatientCondition`.
5. **Evaluation evidence:** `ddsi_absent_without_active_condition`, `ddsi_present_with_matching_active_condition`, and `ddsi_absent_after_condition_resolution` passed.
6. **Manuscript section:** Clinical-context filtering; architecture evaluation.
7. **Safe wording and limitations:** Safe: "In the tested fixtures, DDSI findings were gated by matching active patient-condition records." Limitation: correctness depends on complete, accurately mapped condition data; condition terminology normalization is minimal.

### B9. DFI Is Drug-Based Rather Than Condition-Gated

1. **Design decision:** Query DFI records for active drugs independently of patient conditions.
2. **Problem it addresses:** Food interactions generally do not require a disease-profile match in the current model.
3. **Implementation details:** The DFI query filters by active drug RxCUIs and interaction type only.
4. **Code evidence:** `app/services/orchestrator.py` DFI query.
5. **Evaluation evidence:** `dfi_independent_of_condition_profile` passed.
6. **Manuscript section:** Interaction-type behavior.
7. **Safe wording and limitations:** Safe: "The current orchestrator treats stored DFI records as drug-based alerts." Limitation: the design does not model actual patient diet, food exposure, dose, timing, or quantity.

### B10. Source Assertions Separate From Canonical Interactions

1. **Design decision:** Separate the canonical interaction edge from source-specific assertions.
2. **Problem it addresses:** Multiple sources may report the same pair with different severity, mechanism, management, quality, or provenance.
3. **Implementation details:** `InteractionSourceAssertion` links to an interaction and stores source, raw severity, normalized severity, mechanism, management, onset, documentation quality, evidence URL, source record ID, import time, and raw payload.
4. **Code evidence:** `app/models/interaction.py::InteractionSourceAssertion`.
5. **Evaluation evidence:** `source_assertion_preservation` passed. The data profile observed 172,714 assertions over 152,416 interactions at generation time.
6. **Manuscript section:** Evidence/provenance architecture.
7. **Safe wording and limitations:** Safe: "RxCheck separates canonical interaction records from source-specific assertions." Limitation: the current real import is dominated by DDInter, so multi-source capability is more developed in schema than in observed source diversity.

### B11. Raw Source Payload Preservation

1. **Design decision:** Retain imported source rows in JSONB alongside normalized fields.
2. **Problem it addresses:** Normalization can lose source detail needed for traceability, debugging, or reprocessing.
3. **Implementation details:** `raw_payload` stores the original row structure; the bulk importer inserts the DDInter row as JSON.
4. **Code evidence:** `app/models/interaction.py::InteractionSourceAssertion.raw_payload`; `scripts/import_ddinter.py::bulk_upsert_assertions`.
5. **Evaluation evidence:** `source_assertion_preservation` verified raw payload retention for synthetic assertions.
6. **Manuscript section:** Provenance; reproducibility.
7. **Safe wording and limitations:** Safe: "The assertion model retains source payloads for traceability." Limitation: retaining a payload does not verify its correctness, licensing status, or long-term schema compatibility.

### B12. Explicit Source Provenance

1. **Design decision:** Store normalized source identity, source record ID, evidence URL, and import time.
2. **Problem it addresses:** Findings should be traceable to the stored evidence used to construct them.
3. **Implementation details:** The source enum includes DDInter, OpenFDA, RxNorm, and manual. Assertion source-record uniqueness supports idempotent import. Check findings also snapshot source names.
4. **Code evidence:** `app/models/enums.py::InteractionSource`; `app/models/interaction.py`; `app/models/check.py::InteractionCheckFinding.sources_at_run`.
5. **Evaluation evidence:** `source_assertion_preservation` and `finding_snapshot_persistence` passed.
6. **Manuscript section:** Explainability/provenance; auditability.
7. **Safe wording and limitations:** Safe: "The prototype records source identity and source-record provenance for stored assertions." Limitation: source naming is not equivalent to formal evidence-quality assessment or citation verification.

### B13. Source Coverage Checks

1. **Design decision:** Record whether a source was checked for a pair and whether it reported an interaction.
2. **Problem it addresses:** Absence of a finding can mean either "checked and not found" or "not checked."
3. **Implementation details:** `SourceCoverageCheck` stores the pair/counterpart, source, check time, found flag, and notes. The DDInter bulk importer writes positive coverage rows.
4. **Code evidence:** `app/models/interaction.py::SourceCoverageCheck`; `scripts/import_ddinter.py::bulk_insert_coverage_checks`.
5. **Evaluation evidence:** The current expanded evaluator does not test coverage-check semantics.
6. **Manuscript section:** Data provenance; limitations.
7. **Safe wording and limitations:** Safe: "The schema can retain source-coverage observations." Limitation: the current importer appends coverage rows, primarily positive DDInter observations, and the UI does not expose a complete coverage interpretation.

---

## C. Deterministic Interaction Checking And Result Prioritization

### C1. Deterministic Database-Backed Checking

1. **Design decision:** Determine interaction existence only from stored interaction rows.
2. **Problem it addresses:** An LLM or label-text search should not invent or infer the existence of an interaction during the core check.
3. **Implementation details:** The orchestrator queries DDI tuples, DFI rows, and condition-gated DDSI rows from Postgres. It builds summaries from stored assertions. No LLM, OpenFDA, or RxNorm function is called on this path.
4. **Code evidence:** `app/services/orchestrator.py::run_interaction_check`.
5. **Evaluation evidence:** `deterministic_ddi_from_stored_row`, `missing_database_interaction_creates_no_finding`, `anthropic_not_required_for_core_checking`, `openfda_not_required_for_core_checking`, and `rxnorm_not_required_at_check_time` passed.
6. **Manuscript section:** Core artifact architecture; evaluation results.
7. **Safe wording and limitations:** Safe: "Interaction existence in the evaluated path is determined by stored database records rather than LLM generation." Limitation: a missing or incorrect database row directly produces a missing or incorrect finding.

### C2. Batched DDI Pair Query

1. **Design decision:** Generate all unique medication pairs and query them in one tuple-`IN` statement.
2. **Problem it addresses:** One database query per pair would scale poorly with polypharmacy.
3. **Implementation details:** `itertools.combinations` generates pairs; sorted tuples are deduplicated in a set; SQLAlchemy constructs one composite `IN` filter.
4. **Code evidence:** `app/services/orchestrator.py` `canonical_pairs` and DDI query.
5. **Evaluation evidence:** Canonical pair behavior passed; no performance benchmark was conducted.
6. **Manuscript section:** Algorithm/implementation.
7. **Safe wording and limitations:** Safe: "The DDI lookup batches canonical pairs into a single relational query." Limitation: this is an implementation-efficiency choice, not measured evidence of scalability or response-time guarantees.

### C3. Inactive Medication Exclusion

1. **Design decision:** Check only active patient medications.
2. **Problem it addresses:** Discontinued medication rows should remain in history without continuing to trigger findings.
3. **Implementation details:** The orchestrator filters `PatientMedication.is_active=true`. Deletion endpoints soft-deactivate medications and set an end date.
4. **Code evidence:** `app/services/orchestrator.py`; `app/api/patients.py::deactivate_medication`.
5. **Evaluation evidence:** `inactive_medication_exclusion` passed.
6. **Manuscript section:** Patient-state modeling; evaluation.
7. **Safe wording and limitations:** Safe: "Inactive medication records are retained but excluded from checks." Limitation: medication adherence, planned starts, intermittent use, and actual administration are not modeled by the checker.

### C4. Insufficient-Medication Early Return

1. **Design decision:** Return an empty warning result when fewer than two active non-placeholder medications exist.
2. **Problem it addresses:** Pairwise DDI checking is not meaningful with fewer than two verified medications.
3. **Implementation details:** The orchestrator returns no persisted run ID and a warning before pair/query logic.
4. **Code evidence:** `app/services/orchestrator.py` early-return branch.
5. **Evaluation evidence:** Not one of the current 26 scenarios.
6. **Manuscript section:** Checker control flow; limitations.
7. **Safe wording and limitations:** Safe: "The orchestrator reports insufficient verified medications rather than constructing DDI pairs." Limitation: DFI or DDSI could conceptually be relevant with one medication, but the current early return prevents all interaction types when fewer than two verified medications exist.

### C5. Maximum Severity Aggregation

1. **Design decision:** Represent an interaction's displayed severity as the highest severity among its assertions.
2. **Problem it addresses:** Multiple sources may assign different severity levels, and the UI needs one prioritization value.
3. **Implementation details:** `build_summary()` computes a maximum using the ordered enum unknown, minor, moderate, major, contraindicated.
4. **Code evidence:** `app/schemas/interaction.py::build_summary`; `SEVERITY_ORDER`.
5. **Evaluation evidence:** Summary tests and `severity_ranking` passed.
6. **Manuscript section:** Result aggregation; alert prioritization.
7. **Safe wording and limitations:** Safe: "The prototype uses the maximum stored source severity as a conservative display aggregate." Limitation: maximum aggregation is a design rule, not validated evidence that it is the best clinical reconciliation strategy.

### C6. Severity Ranking With Conflict And Hub Tie-Breakers

1. **Design decision:** Rank findings by severity, then source conflict, then drug-A hub count, followed by names.
2. **Problem it addresses:** A long result list needs deterministic ordering that foregrounds higher-severity and potentially contested findings.
3. **Implementation details:** Contraindicated ranks above major, moderate, minor, and unknown. Conflicted assertions sort before non-conflicted assertions at the same severity. Higher `hub_score_a` sorts earlier.
4. **Code evidence:** `app/services/orchestrator.py::SEVERITY_ORDER`; `ranked_items.sort`.
5. **Evaluation evidence:** `severity_ranking` and `severity_ranking_with_three_interaction_types` passed.
6. **Manuscript section:** Alert prioritization; user-interface rationale.
7. **Safe wording and limitations:** Safe: "The returned findings use deterministic severity-first ordering with conflict and hub-count tie-breakers." Limitation: no human-factors study establishes that this ranking improves decisions or reduces harm.

### C7. Source Severity Conflict Detection

1. **Design decision:** Flag an interaction when its stored assertions contain more than one severity.
2. **Problem it addresses:** Collapsing multiple sources to one maximum can conceal disagreement.
3. **Implementation details:** `sources_conflict` is true when the set of assertion severity values has more than one member. The finding snapshot stores the flag; the UI displays "Sources disagree."
4. **Code evidence:** `app/schemas/interaction.py::build_summary`; `app/models/check.py::InteractionCheckFinding`; `frontend/src/components/InteractionCard.jsx`.
5. **Evaluation evidence:** `source_severity_conflict_flag` passed; the data profile observed 174 interactions with multiple asserted severities at generation time.
6. **Manuscript section:** Evidence reconciliation; interface design.
7. **Safe wording and limitations:** Safe: "RxCheck flags stored severity disagreement without adjudicating it." Limitation: the flag does not assess source quality, independence, recency, or which severity is clinically appropriate.

### C8. Hub Score As Interaction-Degree Count

1. **Design decision:** Compute how many stored interactions involve each patient drug.
2. **Problem it addresses:** Interaction burden can be used as a secondary display signal in polypharmacy.
3. **Implementation details:** A union of drug-A and drug-B RxCUIs is grouped and counted for the patient's non-placeholder drugs. The score is included in summaries and used as a tie-breaker.
4. **Code evidence:** `app/services/checks.py::get_hub_scores`; `app/schemas/interaction.py::build_summary`; `app/services/orchestrator.py`.
5. **Evaluation evidence:** The data profile reports top hub drugs; the evaluator exercises ranking but does not validate clinical meaning.
6. **Manuscript section:** Graph-derived prioritization; data profile.
7. **Safe wording and limitations:** Safe: "Hub score is the stored interaction-degree count for a drug." Limitation: it is not a clinical risk score, danger score, patient-specific probability, or evidence-strength measure.

### C9. Concise Five-Second Summary Shape

1. **Design decision:** Return a compact summary with severity, parties, short mechanism/effect/action text, conflict state, hub counts, and explanation availability.
2. **Problem it addresses:** Pharmacists need a scannable first view before optional detail.
3. **Implementation details:** Text is compacted and truncated to 80 characters. Effect is derived from selected raw-payload keys or assertion text. Names adapt to drug, food, or condition counterparts.
4. **Code evidence:** `app/schemas/interaction.py::InteractionSummary`; `build_summary`.
5. **Evaluation evidence:** Unit tests cover severity/conflict and DDSI naming; the architecture evaluator uses summaries in all finding scenarios.
6. **Manuscript section:** Information presentation; artifact design.
7. **Safe wording and limitations:** Safe: "The API provides a compact, structured interaction summary for rapid review." Limitation: the summary uses the first assertion for mechanism/action text and may omit nuance; no timed usability study supports the phrase "five-second" as a measured outcome.

### C10. Severity Grouping In The Frontend

1. **Design decision:** Group unsuppressed findings into contraindicated, major, moderate, and minor sections.
2. **Problem it addresses:** Flat alert lists can be difficult to scan.
3. **Implementation details:** The frontend creates severity buckets, displays only non-empty groups, uses count badges and colored section labels, and renders unknown severity only if separately accommodated by card behavior rather than a named result section.
4. **Code evidence:** `frontend/src/components/InteractionResults.jsx`; `SeverityBadge.jsx`.
5. **Evaluation evidence:** Backend ordering is evaluated; frontend grouping has not undergone formal usability testing.
6. **Manuscript section:** Interface design; alert-fatigue mitigation.
7. **Safe wording and limitations:** Safe: "The interface groups findings by stored severity to support visual scanning." Limitation: color/grouping effectiveness and accessibility have not been empirically evaluated.

### C11. Alert-Fatigue Mitigation As Layered Presentation

1. **Design decision:** Combine severity ordering, compact collapsed cards, conflict indicators, and a collapsed reviewed section.
2. **Problem it addresses:** Repeated and numerous alerts can overwhelm users.
3. **Implementation details:** Cards are collapsed by default; details and AI explanation are requested on demand. Suppressed findings remain available under "previously reviewed."
4. **Code evidence:** `frontend/src/components/InteractionCard.jsx`; `InteractionResults.jsx`; orchestrator ranking/suppression.
5. **Evaluation evidence:** Suppression semantics and severity ranking passed. Alert fatigue itself was not measured.
6. **Manuscript section:** Design rationale; human-computer interaction.
7. **Safe wording and limitations:** Safe: "The prototype includes design mechanisms intended to reduce visual alert burden." Limitation: it must not be claimed that RxCheck reduces alert fatigue without a user study.

---

## D. Longitudinal State, Suppression, Overrides, And Auditability

### D1. Acknowledgment Suppression Rather Than Deletion

1. **Design decision:** Keep acknowledged interactions in results with a suppression flag.
2. **Problem it addresses:** Removing reviewed alerts would erase visibility and weaken traceability.
3. **Implementation details:** Active, unexpired acknowledgments are loaded by patient and interaction. Matching findings are marked `suppressed=true`, persisted with `suppressed_by_ack`, excluded from severity counts, and shown in a collapsible UI section.
4. **Code evidence:** `app/services/orchestrator.py`; `app/models/audit.py::InteractionAcknowledgment`; `frontend/src/components/InteractionResults.jsx`.
5. **Evaluation evidence:** `acknowledgment_suppression` passed.
6. **Manuscript section:** Alert-fatigue mitigation; auditability.
7. **Safe wording and limitations:** Safe: "Acknowledgment changes presentation state while preserving the finding." Limitation: suppression design has not been clinically validated, and users lack a comprehensive acknowledgment-management interface.

### D2. Severity Escalation Invalidates Lower-Severity Acknowledgment

1. **Design decision:** Suppress only if acknowledgment severity is at least the current maximum severity.
2. **Problem it addresses:** A previously reviewed interaction should reappear if later evidence raises its severity.
3. **Implementation details:** Severity ranks are compared; a moderate acknowledgment cannot suppress a current major finding.
4. **Code evidence:** `app/services/orchestrator.py` acknowledgment comparison.
5. **Evaluation evidence:** `acknowledgment_severity_escalation_behavior` passed.
6. **Manuscript section:** Safety-oriented alert state; evaluation.
7. **Safe wording and limitations:** Safe: "In the synthetic evaluation, a higher current severity prevented suppression by a lower-severity acknowledgment." Limitation: this evaluates implementation logic, not whether the escalation policy is clinically sufficient.

### D3. Expiring And Deactivatable Acknowledgments

1. **Design decision:** Allow acknowledgments to expire or be deactivated without deleting their row.
2. **Problem it addresses:** Review decisions may be temporary, and historical state should remain inspectable.
3. **Implementation details:** Optional `expires_days` sets `expires_at`; the orchestrator ignores expired rows. DELETE sets the newest active acknowledgment to `is_active=false` and writes an audit event.
4. **Code evidence:** `app/api/interactions.py::acknowledge_interaction`; `deactivate_acknowledgment`; `app/models/audit.py`.
5. **Evaluation evidence:** Active acknowledgment suppression is tested; expiration timing and deactivation endpoint behavior are not in the 26 scenarios.
6. **Manuscript section:** Longitudinal alert management.
7. **Safe wording and limitations:** Safe: "The acknowledgment model supports expiry and soft deactivation." Limitation: no scheduled cleanup, reminder, or expiry-management UI is implemented.

### D4. Override Persistence

1. **Design decision:** Store an override as a record linked to a specific finding, including user, action, severity, note, and time.
2. **Problem it addresses:** A pharmacist action should be documented without mutating the original interaction assertion.
3. **Implementation details:** The endpoint resolves the finding and user, copies the finding severity, inserts `InteractionOverride`, and writes an audit event. The frontend requires a non-empty note before submitting, although the API schema itself permits `note=None`.
4. **Code evidence:** `app/api/interactions.py::override_finding`; `app/models/audit.py::InteractionOverride`; `frontend/src/components/InteractionCard.jsx`.
5. **Evaluation evidence:** `override_persistence` passed.
6. **Manuscript section:** Human oversight; audit trail.
7. **Safe wording and limitations:** Safe: "The prototype persists finding-level override records and related audit events." Limitation: API-level note enforcement is absent, identity is not authenticated, and persistence does not establish regulatory-grade auditability.

### D5. Overrides Do Not Automatically Suppress Future Findings

1. **Design decision:** Keep override records separate from orchestration/suppression logic.
2. **Problem it addresses:** An override can document a decision without silently changing future detection behavior.
3. **Implementation details:** The orchestrator reads acknowledgments but does not query `InteractionOverride`.
4. **Code evidence:** `app/services/orchestrator.py`; `app/models/audit.py::InteractionOverride`.
5. **Evaluation evidence:** `override_does_not_suppress_future_finding` passed.
6. **Manuscript section:** Override semantics; evaluation.
7. **Safe wording and limitations:** Safe: "Current overrides are audit records and do not alter later deterministic checks." Limitation: users could reasonably expect different semantics; the UI should make this distinction clearer.

### D6. Check Run Snapshots

1. **Design decision:** Persist each completed check as a run with a medication snapshot, source list, actor, timestamp, and duration.
2. **Problem it addresses:** Patient medication state can change, so later review requires a record of what was checked.
3. **Implementation details:** The snapshot contains medication ID, RxCUI, preferred name, dose, and active state for active non-placeholder medications. Sources currently default to `["DDInter"]`.
4. **Code evidence:** `app/models/check.py::InteractionCheckRun`; `app/services/orchestrator.py` run creation.
5. **Evaluation evidence:** `check_run_persistence` passed.
6. **Manuscript section:** Reproducibility; longitudinal audit.
7. **Safe wording and limitations:** Safe: "Completed checks persist a run-level snapshot of the verified active medication set." Limitation: the snapshot excludes placeholders and conditions, and `sources_used` is currently hardcoded rather than derived from all finding assertions.

### D7. Finding Snapshots

1. **Design decision:** Persist run-specific severity, source, conflict, suppression, and explanation linkage for each interaction.
2. **Problem it addresses:** Source assertions or aggregate severity may change after a check.
3. **Implementation details:** A unique run/interaction finding stores `max_severity_at_run`, `sources_at_run`, `sources_conflicted`, `suppressed_by_ack`, and optional `llm_explanation_id`.
4. **Code evidence:** `app/models/check.py::InteractionCheckFinding`; finding creation in `app/services/orchestrator.py`.
5. **Evaluation evidence:** `finding_snapshot_persistence` and `findings_exist_before_llm_request` passed.
6. **Manuscript section:** Provenance; temporal reproducibility.
7. **Safe wording and limitations:** Safe: "The prototype preserves selected finding state at check time." Limitation: it does not snapshot full assertion text or source payloads into the finding itself.

### D8. Audit Events

1. **Design decision:** Write generic audit-event rows for overrides and acknowledgment changes.
2. **Problem it addresses:** Domain records alone may not provide a unified event trail.
3. **Implementation details:** Events record time, user ID, event type, target type/ID, JSON payload, and optional IP/user agent fields. Current endpoints populate the core fields but not request IP or user agent.
4. **Code evidence:** `app/models/audit.py::AuditEvent`; acknowledgment and override endpoints in `app/api/interactions.py`.
5. **Evaluation evidence:** Override persistence evaluation creates an override through application logic; comprehensive audit-event coverage is not separately scored in the expanded results.
6. **Manuscript section:** Auditability; governance limitations.
7. **Safe wording and limitations:** Safe: "Selected user actions produce structured audit-event records." Limitation: this is not evidence of an immutable, complete, authenticated, or regulatory-compliant audit trail.

---

## E. LLM Explanation Boundary And FDA Label Context

### E1. Finding-Bound LLM Explanation Endpoint

1. **Design decision:** Generate an explanation only for an existing persisted finding.
2. **Problem it addresses:** Allowing arbitrary prompts or drug pairs would weaken the boundary between deterministic detection and generative explanation.
3. **Implementation details:** `POST /api/v1/findings/{finding_id}/explain` first loads the finding. Existing explanation IDs are reused rather than regenerated. New generation receives the finding's interaction ID.
4. **Code evidence:** `app/api/interactions.py::explain_finding`; `get_finding_or_404`; `app/services/llm.py::generate_explanation`.
5. **Evaluation evidence:** `llm_explanation_requires_existing_finding` and `findings_exist_before_llm_request` passed.
6. **Manuscript section:** Human-AI architecture; safety boundary.
7. **Safe wording and limitations:** Safe: "The explanation endpoint is structurally downstream of a persisted deterministic finding." Limitation: this prevents arbitrary explanation requests but does not guarantee factual or clinically appropriate generated text.

### E2. Structured RAG Context

1. **Design decision:** Supply the LLM with database interaction fields and optional FDA label excerpts rather than ask it to identify interactions from model memory.
2. **Problem it addresses:** Generative models can invent interaction facts when prompted without bounded evidence.
3. **Implementation details:** Context includes parties, type, maximum severity and sources, first assertion mechanism/management, truncated label excerpts, and citation metadata.
4. **Code evidence:** `app/services/llm.py` `rag_context` and `rag_text`.
5. **Evaluation evidence:** The evaluator confirms the LLM is not required for finding creation. It does not assess generated clinical correctness.
6. **Manuscript section:** RAG/explanation design.
7. **Safe wording and limitations:** Safe: "The explanation request is grounded in a structured context assembled from stored records and optional label text." Limitation: only the first assertion supplies mechanism/management, and prompt grounding cannot guarantee model adherence.

### E3. Restrictive System Prompt

1. **Design decision:** Instruct the model to use only context, avoid invented facts and doses, identify insufficient data, cite sources, and include a verification disclaimer.
2. **Problem it addresses:** Unconstrained clinical language generation could add unsupported recommendations.
3. **Implementation details:** A fixed system prompt defines these rules; the user prompt requests JSON only.
4. **Code evidence:** `app/services/llm.py::PROMPT_SYSTEM`.
5. **Evaluation evidence:** No paid API was called in the architecture evaluation. `research/explanation_quality_rubric.md` defines a future boundary-adherence assessment.
6. **Manuscript section:** Prompt design; risk controls.
7. **Safe wording and limitations:** Safe: "The prompt explicitly constrains generation to supplied context." Limitation: prompt instructions are not a security boundary and do not eliminate hallucination or prompt-injection risk.

### E4. Expected JSON Output Shape And Custom Validation

1. **Design decision:** Request seven named JSON fields and validate basic structure before returning parsed content.
2. **Problem it addresses:** Free-form prose is harder to render, inspect, and validate consistently.
3. **Implementation details:** The parser strips an optional code fence, uses `JSONDecoder.raw_decode`, checks required keys, and verifies that `sources_used` is a list. The API response is then shaped by `LlmExplanationResult`.
4. **Code evidence:** `app/services/llm.py::_parse_explanation_payload`; `app/schemas/interaction.py::LlmExplanationResult`.
5. **Evaluation evidence:** The current architecture evaluator does not call Anthropic. The rubric includes schema validity for future explanation samples.
6. **Manuscript section:** LLM output control; evaluation instrument.
7. **Safe wording and limitations:** Safe: "RxCheck applies custom JSON parsing and required-field checks to model output." Limitation: validation does not fully enforce field types, allowed confidence values, severity preservation, citation correctness, or semantic grounding.

### E5. Model-Reported Confidence

1. **Design decision:** Ask the LLM to label confidence as high, medium, or low based on context evidence quality.
2. **Problem it addresses:** Users may benefit from an explicit indication that explanation quality varies with evidence.
3. **Implementation details:** `confidence` is requested in the prompt, returned in `LlmExplanationResult`, and shown as a colored badge.
4. **Code evidence:** `app/services/llm.py` user message; `app/schemas/interaction.py`; `frontend/src/components/InteractionCard.jsx`.
5. **Evaluation evidence:** No calibration or reliability evaluation exists.
6. **Manuscript section:** Explanation interface; limitations.
7. **Safe wording and limitations:** Safe: "The interface displays a model-reported confidence label." Limitation: this is not a calibrated probability, uncertainty estimate, or validated indicator of clinical correctness, and current custom validation does not restrict it to the three requested values.

### E6. Failed Validation Storage

1. **Design decision:** Persist raw model output and validation errors even when validation fails.
2. **Problem it addresses:** Discarding failed outputs would prevent failure analysis and audit.
3. **Implementation details:** Every generated row stores raw text, structured input, pass/fail flag, validation errors, model identifiers, latency, and token usage. If validation fails, parsed explanation fields are returned as `None`.
4. **Code evidence:** `app/services/llm.py` validation and `LlmExplanation` creation; `app/models/check.py::LlmExplanation`.
5. **Evaluation evidence:** Not exercised with live or mocked malformed model output in the 26 scenarios.
6. **Manuscript section:** LLM observability; failure analysis.
7. **Safe wording and limitations:** Safe: "The schema preserves failed model outputs and validation diagnostics for later review." Limitation: persistence does not prevent a harmful output from being generated, and the frontend does not provide a dedicated validation-failure review workflow.

### E7. Drug-Reference Cross-Check

1. **Design decision:** Reject schema validation when the raw explanation mentions another known non-placeholder drug.
2. **Problem it addresses:** An explanation may introduce a drug not present in the underlying interaction.
3. **Implementation details:** The validator loads all non-placeholder preferred names and searches the response text for word-boundary matches, excluding the two allowed drug names.
4. **Code evidence:** `app/services/llm.py::_validate_drug_mentions`.
5. **Evaluation evidence:** Not directly evaluated in the current 26 scenarios.
6. **Manuscript section:** LLM validation; safety constraints.
7. **Safe wording and limitations:** Safe: "A lexical cross-check flags references to other known drug preferred names." Limitation: this heuristic can miss brands, abbreviations, classes, morphology, or unknown drugs and can create false positives for short/common names.

### E8. Prompt And Model Versioning

1. **Design decision:** Store prompt-template version, logical model name, and API model version with every explanation.
2. **Problem it addresses:** Generated behavior can change when prompts or provider models change.
3. **Implementation details:** Constants identify prompt version `v1` and stored model name; the configured API model is persisted separately.
4. **Code evidence:** `app/services/llm.py::PROMPT_TEMPLATE_VERSION`; `STORED_MODEL_NAME`; `API_MODEL_NAME`; `app/models/check.py::LlmExplanation`.
5. **Evaluation evidence:** Not evaluated across versions.
6. **Manuscript section:** Reproducibility; LLM implementation.
7. **Safe wording and limitations:** Safe: "Explanation records retain prompt and model version metadata." Limitation: reproducibility is still limited by provider-side model changes, nondeterminism, and absent generation-parameter snapshots beyond the coded `max_tokens`.

### E9. OpenFDA Label Retrieval With Fallback Queries

1. **Design decision:** Retrieve label evidence using stored SPL set ID first, then RxCUI, then generic name.
2. **Problem it addresses:** OpenFDA label indexing may not support one identifier consistently for every drug.
3. **Implementation details:** The fetcher extracts drug interactions, warnings, boxed warnings, and contraindications; creates a DailyMed URL; caches by RxCUI; and persists newly discovered SPL set IDs.
4. **Code evidence:** `app/services/openfda.py::fetch_label_for_drug`; `_build_label_payload`; `_persist_spl_set_id`.
5. **Evaluation evidence:** The architecture evaluation mocks OpenFDA to prove it is outside core checking; live retrieval quality is not evaluated.
6. **Manuscript section:** External evidence enrichment.
7. **Safe wording and limitations:** Safe: "The optional explanation path can retrieve selected OpenFDA label sections through identifier fallbacks." Limitation: a returned label may not be the intended product label, generic-name search can be ambiguous, and non-404 errors currently propagate.

### E10. OpenFDA Interaction Mention Heuristic

1. **Design decision:** Record whether the counterpart's preferred name appears in the other drug's label interaction text.
2. **Problem it addresses:** A simple signal can indicate direct lexical mention in label evidence.
3. **Implementation details:** The fetcher performs a lowercase substring search in each direction.
4. **Code evidence:** `app/services/openfda.py::fetch_citations_for_interaction`.
5. **Evaluation evidence:** Not evaluated against a label corpus.
6. **Manuscript section:** Citation/context design; limitations.
7. **Safe wording and limitations:** Safe: "The citation payload includes a lexical mention flag." Limitation: substring matching is not semantic evidence extraction and can produce false negatives or false positives.

### E11. OpenFDA Is Explanation-Only Evidence

1. **Design decision:** Do not use label retrieval to create interaction findings.
2. **Problem it addresses:** Availability or wording of a label should not make the deterministic checker nondeterministic.
3. **Implementation details:** OpenFDA is imported only by the LLM service. The orchestrator contains no OpenFDA dependency.
4. **Code evidence:** `app/services/llm.py`; `app/services/openfda.py`; absence from `app/services/orchestrator.py`.
5. **Evaluation evidence:** `openfda_not_required_for_core_checking` passed.
6. **Manuscript section:** Architectural separation; evaluation.
7. **Safe wording and limitations:** Safe: "OpenFDA contributes optional explanation context but not interaction existence." Limitation: this separation means label-only interactions absent from the imported database will not become findings.

### E12. Anthropic Is Optional To Core Checking

1. **Design decision:** Keep the paid LLM call out of the interaction-check transaction.
2. **Problem it addresses:** Core checking should remain available without a paid key, provider availability, or token expenditure.
3. **Implementation details:** The LLM is invoked only through the explain endpoint. A missing API key returns HTTP 400; findings and summaries are created beforehand.
4. **Code evidence:** `app/api/interactions.py::explain_finding`; `app/services/llm.py`; `app/services/orchestrator.py`.
5. **Evaluation evidence:** `anthropic_not_required_for_core_checking` and `findings_exist_before_llm_request` passed.
6. **Manuscript section:** Cost-conscious architecture; human-AI boundary.
7. **Safe wording and limitations:** Safe: "Anthropic is optional for explanation generation and is not required for the evaluated core check." Limitation: the UI still exposes the explanation control, and provider/network errors beyond a missing key are not comprehensively handled.

### E13. RxNorm Is Not Required At Check Time After Normalization

1. **Design decision:** Store normalized medication identifiers and check them later without re-contacting RxNorm.
2. **Problem it addresses:** Core checking should not fail because a normalization API is temporarily unavailable after medication entry.
3. **Implementation details:** `PatientMedication` stores RxCUI and normalization status; the orchestrator consumes RxCUIs directly.
4. **Code evidence:** `app/models/patient.py::PatientMedication`; `app/services/orchestrator.py`.
5. **Evaluation evidence:** `rxnorm_not_required_at_check_time` passed with a failing normalization sentinel.
6. **Manuscript section:** Service-boundary evaluation; cost-conscious design.
7. **Safe wording and limitations:** Safe: "Previously normalized medication lists can be checked without a live RxNorm call." Limitation: adding unseen names, fuzzy variants, or NDCs may still require RxNorm.

---

## F. Import, Deployment, And Cost-Conscious Architecture

### F1. Bulk, Idempotent DDInter Import

1. **Design decision:** Load all aliases in memory, resolve CSV names locally, and use batched Postgres upserts.
2. **Problem it addresses:** Row-by-row ORM/network operations were too slow for hundreds of thousands of source rows.
3. **Implementation details:** Eight CSV partitions are concatenated; names are resolved through aliases/preferred names; pairs are canonicalized; `execute_values` inserts interactions and assertions in batches; conflict handling preserves existing rows.
4. **Code evidence:** `scripts/import_ddinter.py`.
5. **Evaluation evidence:** `research/data_profile.md` observed 152,413 DDI rows and 172,713 DDInter assertions at generation time.
6. **Manuscript section:** Data ingestion; implementation optimization.
7. **Safe wording and limitations:** Safe: "The repository includes a bulk, conflict-tolerant importer for eight named DDInter CSV partitions." Limitation: current paths are local-machine-specific, import benchmarking is not part of the formative evaluation, and source licensing/terms require independent review.

### F2. Quarantine Rather Than Placeholder Import For Unresolved DDInter Names

1. **Design decision:** Skip imported source rows when either DDInter drug name lacks a local mapping.
2. **Problem it addresses:** Creating interaction edges to unresolved placeholders would imply unsupported identity certainty.
3. **Implementation details:** `resolve_rows()` places unresolved rows in a quarantine list and only sends fully resolved rows to database insertion.
4. **Code evidence:** `scripts/import_ddinter.py::resolve_rows`.
5. **Evaluation evidence:** The data profile documents this importer limitation; quarantine totals are not included in the current profile output.
6. **Manuscript section:** Data quality; limitations.
7. **Safe wording and limitations:** Safe: "The bulk importer excludes rows whose drug names cannot be mapped locally." Limitation: excluded rows reduce coverage, and the quarantine is not persisted as a formal review dataset.

### F3. Real Import Is DDI-Only

1. **Design decision:** Map the available five-column DDInter files to DDI interactions only.
2. **Problem it addresses:** The supplied files contain two drug columns and severity but no food/disease counterpart structure.
3. **Implementation details:** Imported interaction type is fixed to `DDI`; severity maps major, moderate, minor, and unknown; the files do not populate mechanism or management.
4. **Code evidence:** `scripts/import_ddinter.py`; `research/data_profile.md`.
5. **Evaluation evidence:** The profile observed 152,413 DDI, one DFI, and two DDSI rows; the small DFI/DDSI counts include research/synthetic fixtures rather than equivalent real import coverage.
6. **Manuscript section:** Dataset description; limitations.
7. **Safe wording and limitations:** Safe: "The current bulk DDInter import populates DDI pairs and severity labels." Limitation: do not claim broad DFI or DDSI source coverage from the real import.

### F4. Single-Service Frontend And API Deployment

1. **Design decision:** Build the React frontend and serve its static output from FastAPI under the same origin.
2. **Problem it addresses:** A single deployment URL reduces infrastructure and CORS/API-base complexity for a prototype.
3. **Implementation details:** Railway builds Python and frontend dependencies; FastAPI mounts `/assets`, serves `index.html`, and preserves API/docs/health routes.
4. **Code evidence:** `railway.toml`; `app/main.py`; `frontend/src/api.js`.
5. **Evaluation evidence:** Not part of the architecture evaluator; prior project acceptance testing exercised local frontend/backend behavior.
6. **Manuscript section:** Deployment architecture; cost rationale.
7. **Safe wording and limitations:** Safe: "The prototype can serve its API and compiled frontend from one FastAPI deployment." Limitation: this is not a high-availability, independently scalable, or security-hardened production topology.

### F5. Cost-Conscious Separation Of Core And Optional Services

1. **Design decision:** Keep Postgres-backed checking local to the application while treating RxNorm, OpenFDA, and Anthropic as boundary services with different timing requirements.
2. **Problem it addresses:** Budget-constrained deployments may not support a paid LLM call or continuous dependence on multiple remote services.
3. **Implementation details:** Anthropic and OpenFDA are explanation-time dependencies; RxNorm is medication-entry-time unless aliases already exist; deterministic checking uses stored rows.
4. **Code evidence:** Service boundaries in `app/services/orchestrator.py`, `normalization.py`, `openfda.py`, and `llm.py`; `research/cost_constrained_design.md`.
5. **Evaluation evidence:** The three service-independence scenarios passed without external calls.
6. **Manuscript section:** Design rationale; cost-conscious architecture.
7. **Safe wording and limitations:** Safe: "RxCheck demonstrates a cost-conscious separation between deterministic checking and optional network-dependent enrichment." Limitation: no formal cost model, cost-effectiveness analysis, total-cost-of-ownership study, or low-resource field deployment has been conducted.

### F6. Open-Source Application Stack With Proprietary Optional LLM

1. **Design decision:** Build the application with FastAPI, SQLAlchemy, Postgres, React, Vite, Tailwind, pandas, and related open-source tools, while using Anthropic only for optional explanations.
2. **Problem it addresses:** A transparent, modifiable prototype stack supports research inspection and self-hosting.
3. **Implementation details:** Dependencies are listed in Python and frontend package manifests; Railway is the current managed host.
4. **Code evidence:** `requirements.txt`; `frontend/package.json`; `research/cost_constrained_design.md`.
5. **Evaluation evidence:** Successful script and test execution demonstrate one environment, not portability across all environments.
6. **Manuscript section:** Artifact implementation; cost context.
7. **Safe wording and limitations:** Safe: "Most application components are open-source, while explanation generation currently uses an optional proprietary API." Limitation: DDInter terms, hosting, operations, and external API usage may still create licensing or recurring costs.

### F7. Basic Health Check And Route Introspection

1. **Design decision:** Expose `/health` and print registered routes at startup.
2. **Problem it addresses:** Deployment platforms need a basic liveness endpoint, and prototype developers need route visibility.
3. **Implementation details:** Railway uses `/health`; FastAPI startup prints sorted routes.
4. **Code evidence:** `app/main.py`; `railway.toml`.
5. **Evaluation evidence:** `tests/test_health.py` passed.
6. **Manuscript section:** Operational implementation.
7. **Safe wording and limitations:** Safe: "The deployment exposes a basic application health endpoint." Limitation: it does not verify database availability, source freshness, external dependencies, or clinical readiness.

### F8. Schema Creation At Application Import

1. **Design decision:** Call `Base.metadata.create_all()` when the application module loads.
2. **Problem it addresses:** Prototype deployment can initialize missing tables without a separate migration step.
3. **Implementation details:** All imported model metadata is passed to the configured engine before the FastAPI app is created.
4. **Code evidence:** `app/main.py`.
5. **Evaluation evidence:** The application imported successfully during pytest and evaluation.
6. **Manuscript section:** Prototype deployment; limitations.
7. **Safe wording and limitations:** Safe: "The prototype can create missing tables from SQLAlchemy metadata at startup." Limitation: this is not a robust migration strategy; Alembic is installed but migration-managed schema evolution is not demonstrated.

---

## G. Security, Governance, Coverage, And Validation Boundaries

### G1. Prototype User Roles Without Authentication Or RBAC Enforcement

1. **Design decision:** Model users and role labels, but use a fixed default user for prototype actions.
2. **Problem it addresses:** Audit-linked records require an actor even before authentication is implemented.
3. **Implementation details:** `User.role` is constrained to pharmacist/admin/readonly, but no login, token validation, route guard, or role authorization exists. API actions create or use a default pharmacist identity.
4. **Code evidence:** `app/models/patient.py::User`; `app/api/patients.py::ensure_default_user`; absence of auth middleware/dependencies in `app/main.py`.
5. **Evaluation evidence:** No authentication/security evaluation exists.
6. **Manuscript section:** Limitations; future work; governance.
7. **Safe wording and limitations:** Safe: "The data model anticipates user roles, but the current prototype does not authenticate users or enforce RBAC." It must not be described as suitable for real patient data or controlled clinical deployment.

### G2. Broad Development CORS

1. **Design decision:** Allow broad origins, methods, headers, and credentials for frontend development/deployment convenience.
2. **Problem it addresses:** The prototype frontend may run on local or Railway origins.
3. **Implementation details:** The allowlist includes production/local URLs and `"*"`.
4. **Code evidence:** `app/main.py` CORS middleware.
5. **Evaluation evidence:** No security evaluation exists.
6. **Manuscript section:** Deployment limitations; security.
7. **Safe wording and limitations:** Safe: "CORS is configured permissively for prototype development." Limitation: the combination requires security review and tightening before any sensitive deployment.

### G3. No HIPAA Compliance Claim

1. **Design decision:** Treat all current patient creation as synthetic and label the product as a prototype.
2. **Problem it addresses:** Research prototyping should avoid implying readiness for protected health information.
3. **Implementation details:** Created patients set `is_synthetic=true`; the frontend warns "Prototype — not for clinical use." However, the schema can store identifiable and health-related fields.
4. **Code evidence:** `app/api/patients.py::create_patient`; `app/models/patient.py`; `frontend/src/components/Layout.jsx`.
5. **Evaluation evidence:** No privacy, security, HIPAA, threat-model, or penetration assessment exists.
6. **Manuscript section:** Ethics, privacy, limitations.
7. **Safe wording and limitations:** Safe: "The evaluated artifact uses synthetic prototype patients." Do not claim HIPAA compliance, PHI suitability, encryption governance, retention compliance, or institutional deployment readiness.

### G4. No FDA Clearance Or Regulated-Device Claim

1. **Design decision:** Position RxCheck as a research prototype and require institutional-reference verification in LLM output.
2. **Problem it addresses:** The artifact has not undergone regulatory review.
3. **Implementation details:** Prototype warnings and conservative research artifacts explicitly reject FDA claims.
4. **Code evidence:** LLM disclaimer in `app/services/llm.py`; research claim matrix and README; frontend prototype warning.
5. **Evaluation evidence:** No regulatory evaluation exists.
6. **Manuscript section:** Limitations; regulatory context.
7. **Safe wording and limitations:** Safe: "RxCheck is a design research prototype." Do not claim FDA clearance, approval, authorization, device classification, or regulatory compliance.

### G5. Incomplete DFI And DDSI Data Coverage

1. **Design decision:** Support DFI/DDSI in the schema and orchestrator despite the present bulk source import being DDI-only.
2. **Problem it addresses:** The architecture should express contextual interaction types even when current data ingestion is uneven.
3. **Implementation details:** DFI/DDSI tables, APIs, filters, summaries, and synthetic fixtures exist; real DDInter import files populate DDI only.
4. **Code evidence:** `app/models/interaction.py`; `app/services/orchestrator.py`; `scripts/import_ddinter.py`; `research/data_profile.md`.
5. **Evaluation evidence:** Synthetic DFI and DDSI scenarios passed. The data profile observed only one DFI and two DDSI rows versus 152,413 DDI rows at generation time.
6. **Manuscript section:** Artifact scope; dataset limitations.
7. **Safe wording and limitations:** Safe: "The architecture supports DFI and condition-gated DDSI behavior in synthetic evaluation." Do not claim substantive real-world DFI/DDSI coverage from the current database.

### G6. Incomplete DDI Coverage

1. **Design decision:** Check only imported and successfully normalized interactions.
2. **Problem it addresses:** Deterministic behavior requires a defined database rather than unbounded inference.
3. **Implementation details:** Missing pairs return no finding; unresolved import names are quarantined.
4. **Code evidence:** `app/services/orchestrator.py`; `scripts/import_ddinter.py`.
5. **Evaluation evidence:** `missing_database_interaction_creates_no_finding` passed; the data profile describes stored counts but not completeness.
6. **Manuscript section:** Data limitations; validity threats.
7. **Safe wording and limitations:** Safe: "RxCheck checks interactions present in its configured imported database." Do not claim complete DDI coverage, comprehensive drug knowledge, or that no finding means no clinically relevant interaction.

### G7. No Clinical Validation

1. **Design decision:** Evaluate architecture behavior with synthetic controlled fixtures rather than claim clinical effectiveness.
2. **Problem it addresses:** The prototype needs reproducible evidence without overstating what software tests can prove.
3. **Implementation details:** The research evaluator covers 26 deterministic scenarios and explicitly disables/mocks external APIs. The explanation rubric assesses evidence-boundary adherence rather than clinical correctness.
4. **Code evidence:** `research/evaluate_rxcheck.py`; `research/evaluation_plan.md`; `research/explanation_quality_rubric.md`.
5. **Evaluation evidence:** 26/26 synthetic architecture scenarios passed; pytest reported 3 passing tests. Neither result is a clinical study.
6. **Manuscript section:** Evaluation methodology; discussion; limitations.
7. **Safe wording and limitations:** Safe: "Formative synthetic evaluation demonstrated the specified architecture behaviors under controlled fixtures." Do not claim clinical accuracy, improved outcomes, reduced medication harm, pharmacist acceptance, or clinical validation.

### G8. Prompt-Injection Risk Remains

1. **Design decision:** Use restrictive instructions and post-generation lexical checks while documenting prompt injection as unresolved.
2. **Problem it addresses:** External label text and stored source content are placed into the model context.
3. **Implementation details:** The prompt tells the model to use only context, but context is not sanitized or structurally isolated as untrusted data. The research rubric includes an optional injection probe.
4. **Code evidence:** `app/services/llm.py`; `research/failure_mode_analysis.md`; `research/explanation_quality_rubric.md`.
5. **Evaluation evidence:** No adversarial LLM execution was performed.
6. **Manuscript section:** Security and LLM limitations.
7. **Safe wording and limitations:** Safe: "The design includes prompt constraints but retains prompt-injection risk." Do not claim robust prompt-injection resistance.

### G9. External-Service Failure Handling Is Partial

1. **Design decision:** Keep external services out of core checks, while implementing basic missing-key, 404, and no-match behavior.
2. **Problem it addresses:** Remote APIs can be unavailable or incomplete.
3. **Implementation details:** Missing Anthropic key maps to HTTP 400; OpenFDA 404 returns no label; RxNorm no-match creates a placeholder. Other provider/network errors can propagate.
4. **Code evidence:** `app/services/llm.py`; `app/api/interactions.py`; `app/services/openfda.py`; `app/services/normalization.py`.
5. **Evaluation evidence:** Core checks passed with failing service sentinels, but endpoint degradation under actual network errors was not evaluated.
6. **Manuscript section:** Failure-mode analysis; resilience limitations.
7. **Safe wording and limitations:** Safe: "The core checker is isolated from optional service calls, while external-service endpoint failure handling remains partial." Do not claim full offline capability or graceful degradation for every API failure.

### G10. Research Results Are Timestamped And Fixture-Contaminated

1. **Design decision:** Preserve generated evaluation and profiling outputs and explicitly count identifiable research fixtures.
2. **Problem it addresses:** Reproducible reporting requires fixed outputs, but evaluation writes synthetic rows into the configured database.
3. **Implementation details:** Evaluation assertions include `evaluation_fixture=true`; the profiler reports fixture interaction/assertion counts and states that aggregate totals include them.
4. **Code evidence:** `research/evaluate_rxcheck.py`; `research/profile_data.py`; `research/data_profile.md`.
5. **Evaluation evidence:** The profile reported five identifiable fixture interactions and six fixture assertions at its generation time.
6. **Manuscript section:** Reproducibility; data profile; limitations.
7. **Safe wording and limitations:** Safe: "Reported database counts are timestamped observations that include explicitly identified research fixtures." Limitation: counts can change after imports or evaluations and should not be presented as immutable dataset characteristics.

---

## Cross-Cutting Manuscript Map

| Manuscript Section | Decisions To Draw From |
|---|---|
| Problem framing | A1, A8-A11, C1, C11, G5-G7 |
| Design objectives | A1-A12, B5-B13, C1-C11, D1-D8, E1-E13 |
| Artifact architecture | B1-B13, C1-C9, E1-E13, F1-F8 |
| Human-in-the-loop design | A4, A9-A11, C9-C11, D1-D5, E1-E7 |
| Data and provenance | B3-B13, D6-D8, F1-F3 |
| Cost-conscious rationale | A2, A6, A12, E11-E13, F4-F6 |
| Formative evaluation | B5, B8-B11, C1-C8, D1-D7, E1, E11-E13, G7 |
| Discussion and limitations | Every item's limitation, especially G1-G10 |
| Future work | Authentication/RBAC, migration governance, source diversification, normalization benchmarking, LLM adversarial evaluation, usability studies, and clinical validation |

## Claims The Manuscript Should Not Make

- RxCheck is clinically validated or clinically effective.
- RxCheck has complete DDI, DFI, or DDSI coverage.
- A "no interactions found" result establishes clinical safety.
- Hub score measures drug danger or patient risk.
- Model-reported confidence is calibrated.
- The LLM explanation is clinically correct because it passed structural validation.
- RxCheck is FDA cleared, approved, or compliant.
- RxCheck is HIPAA compliant or ready for protected health information.
- User roles constitute implemented authentication or RBAC.
- The audit tables constitute a complete or immutable regulatory audit trail.
- Postgres and SQLite are currently interchangeable without schema changes.
- The architecture is formally cost-effective.
- The prototype has been shown to reduce alert fatigue or improve pharmacist decisions.
