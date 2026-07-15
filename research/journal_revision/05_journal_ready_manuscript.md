# Separating Drug-Interaction Detection From Generative Explanation: Design and Formative Evaluation of the RxCheck Evidence-Bounded Architecture

**Authors:** [AUTHOR TO SUPPLY: Names, degrees, affiliations, and ORCID identifiers]  
**Corresponding author:** [AUTHOR TO SUPPLY]  
**Manuscript type:** Design-science health-informatics system paper with formative architecture evaluation  
**Repository snapshot evaluated:** `6b763c03a69e33031f196eceb598899ee08a1cba`

> **Prototype status:** RxCheck is not clinically validated, is not intended for clinical use, and must not be used with real patient data in its current form.

## Abstract

### Background

Drug-interaction decision support requires reliable medication identity, structured interaction evidence, patient context, review-state management, and clear communication. Large language models (LLMs) may make structured findings easier to read, but fluent generation is unsafe if it is allowed to determine whether a clinical interaction exists. A defensible architecture should separate finding authority from language generation.

### Objective

This study describes RxCheck and examines whether the prototype enforces a predefined evidence boundary: deterministic database logic creates interaction findings, while an optional LLM is limited to explaining a persisted finding. Secondary objectives were to characterize how the artifact represents unresolved medication input, source assertions, patient-condition context, and longitudinal review state, and to identify the claims that remain untested.

### Methods

RxCheck was examined as a design-science artifact at Git commit `6b763c0`. The system comprises a React/Vite interface, FastAPI service, SQLAlchemy/Postgres data model, RxNorm-oriented medication-normalization workflow, DDInter-derived interaction import, deterministic DDI/DFI/DDSI orchestration, selected review and audit records, optional OpenFDA label retrieval, and an Anthropic explanation endpoint. A committed historical evaluation created synthetic database fixtures and compared expected with observed behavior across 26 architecture scenarios. A separate committed profile described the configured database, and a recorded focused test run covered three software tests. The present revision did not rerun database-writing code because the repository’s default configuration contains an exposed credential. No clinical cases, pharmacists, patient outcomes, or generated explanations were evaluated.

### Results

The recorded June 9, 2026 run reported 26 of 26 synthetic architecture scenarios passing. Tested behaviors included stored-row finding creation, canonical pair ordering, inactive and placeholder exclusion, condition-gated DDSI display, DFI behavior, severity ranking, preservation and conflict flagging of source assertions, run and finding persistence, acknowledgment suppression with severity resurfacing, override persistence without later suppression, an existing-finding requirement for explanation, and independence of the tested core check from Anthropic, OpenFDA, and RxNorm at check time. The timestamped database profile reported 152,416 interaction rows and 172,714 source assertions, including identifiable research fixtures; 152,413 rows were DDI, one was DFI, and two were DDSI. The real-data importer in the repository is DDI-only. The evidence does not establish clinical accuracy, source completeness, normalization performance, explanation factuality, pharmacist usability, alert-fatigue reduction, cost-effectiveness, security, or regulatory readiness.

### Conclusions

RxCheck provides an inspectable instantiation of an evidence-bounded explanation architecture in which the generative component is downstream of deterministic finding creation. The recorded formative run supports selected software boundaries under synthetic conditions, not clinical performance. Independent data packaging, security remediation, source-version documentation, external reference cases, explanation assessment, and pharmacist evaluation are required before submission as a mature system study or consideration for clinical use.

**Keywords:** clinical decision support; drug interactions; pharmacy informatics; large language models; design science; provenance; human oversight; formative evaluation

## 1. Introduction

Drug-interaction decision support (CDS) is a safety-relevant but imperfect component of medication review. Pharmacy CDS products can vary in their ability to identify clinically important drug–drug interactions (DDIs), and excessive or poorly targeted alerts can be ignored or overridden [1,2]. Interaction review is therefore not only a pair-lookup task. It also depends on medication identity, source coverage, patient context, prioritization, review history, and a clear account of what evidence produced a finding.

Generative models create an additional design problem. An LLM can render structured information into concise prose, but it can also omit, contradict, or add claims. Retrieval-augmented generation combines retrieved information with generation [6], but supplying context does not by itself establish factual or clinical correctness. Evaluations of medical LLMs continue to identify limitations even when models display substantial medical knowledge [7]. Responsible AI-CDS guidance consequently emphasizes validation, transparency, governance, and continuous oversight [8,9].

This study addresses a narrow architecture question: **what authority should an LLM have inside a drug-interaction review prototype?** RxCheck places the LLM downstream of a deterministic finding. On the evaluated path, stored interaction rows determine whether a finding exists. The LLM receives a structured representation of an existing finding and optional label excerpts; it cannot create a canonical interaction or a check finding through the explanation endpoint.

We call this arrangement an **evidence-bounded explanation architecture**. The term refers to a software authority boundary, not a guarantee that every generated statement is supported. The architecture combines five design principles: (1) normalize medication identity or retain explicit non-resolution; (2) create findings from structured interaction rows; (3) preserve source assertions and runtime evidence state; (4) incorporate patient context and longitudinal review state; and (5) limit generation to an optional explanation of an existing finding.

The primary research question was:

> To what extent does the inspected RxCheck prototype enforce a predefined evidence boundary in which deterministic database logic creates drug-interaction findings and a generative model is limited to explaining a persisted finding?

Secondary questions were how the artifact represents uncertain medication identity, evidence provenance, patient-condition context, and review state, and which clinical or operational claims remain unsupported. The study is positioned as design science: it describes an artifact and evaluates selected requirements under controlled synthetic conditions [10,11]. It is not a clinical-effectiveness, diagnostic-accuracy, economic, or implementation study.

## 2. Related work and design context

### 2.1 Drug-interaction CDS and alert burden

DDI software can assist medication review, but an alert does not automatically constitute a useful or correct clinical recommendation. In a standardized evaluation across 64 pharmacies, commercial pharmacy CDS systems showed variable performance for selected clinically important interactions [1]. A systematic review of medication safety alerts found that interaction design and clinical-role tailoring may affect alert acceptance, while also noting heterogeneity in measures and a need for further research [2]. RxCheck does not claim to improve detection or alert burden. Its acknowledgment, ranking, and condition-gating features are design mechanisms whose real-world effects have not been studied.

### 2.2 Medication identity and interaction knowledge

RxNorm provides normalized names and identifiers for clinical drugs and links medication concepts across vocabularies [3]. RxCheck uses RxNorm-oriented endpoints and local aliases to attempt medication resolution before checking. This workflow is relevant because inconsistent names can prevent deterministic matching, but the present repository contains no benchmark of its normalization accuracy.

DDInter is an openly accessible DDI resource containing structured interaction associations and risk annotations [4]. DDInter 2.0 expanded the published resource to include additional DDI records, drug–food interactions (DFIs), drug–disease interactions (DDSIs), and therapeutic duplication [5]. RxCheck’s data model can represent DDI, DFI, and DDSI records. However, the importer committed in the repository is tailored to eight DDI-formatted CSV partitions and does not demonstrate import of the broader DDInter 2.0 interaction types. The source’s terms also state that the data are licensed under CC BY-NC-SA 4.0 and caution that the database is incomplete [15].

### 2.3 Generative explanation and responsible AI-CDS

Retrieval-augmented generation was introduced as a way to combine parametric generation with retrieved nonparametric information [6]. In health applications, grounding techniques can constrain available context, but they do not remove the need to evaluate unsupported statements, omission, robustness, and human interpretation. Medical LLM research has shown both strong knowledge performance and important limitations [7]. Recommendations for AI-enabled CDS emphasize staged development, validation, monitoring, privacy, and human-centered governance [8]. World Health Organization guidance similarly emphasizes autonomy, transparency, accountability, inclusiveness, and safety in AI for health [9].

RxCheck does not evaluate whether an LLM improves comprehension or decisions. Its contribution is more limited: the endpoint requires an existing finding, the prompt instructs the model to use supplied context, and the response undergoes custom structural checks before selected fields are returned. This reduces the model’s authority within the system but does not establish faithful explanation.

### 2.4 Design-science positioning

Design-science research evaluates purpose-built artifacts against defined objectives [10]. The Peffers et al. process includes problem identification, objective definition, design and development, demonstration, evaluation, and communication [11]. RxCheck is treated here as an instantiation of an architecture principle rather than as evidence of clinical benefit. The evaluation asks whether selected software boundaries behaved as specified in synthetic fixtures.

[RELATED-WORK REVIEW REQUIRED: Before submission, add a structured comparison with published DDI CDS systems, templated explanation approaches, provenance-aware CDS, and LLM-grounded health systems. The current repository is insufficient to establish novelty relative to all prior work.]

## 3. Design-science method

### 3.1 Artifact and scope

The artifact was the public RxCheck repository at commit `6b763c03a69e33031f196eceb598899ee08a1cba`. The revision examined application code, database models, frontend components, tests, the evaluator, recorded outputs, a database profile, architecture documentation, diagrams, and the prior manuscript.

The evaluated unit was observable software architecture behavior. The study did not evaluate clinical correctness, sensitivity or specificity, interaction-source completeness, pharmacist decisions, patient outcomes, cost-effectiveness, regulatory status, or production operations.

### 3.2 Design requirements

The repository’s committed documentation describes nine detailed requirements. For this paper, they were consolidated into five architecture requirements:

| Requirement | Intended behavior | Principal implementation evidence |
|---|---|---|
| R1. Identity or explicit non-resolution | Resolve medication input toward a stored RxCUI; retain unresolved input as a visible placeholder excluded from checking | `app/services/normalization.py`; `Drug.is_placeholder`; orchestrator filter |
| R2. Structured finding authority and provenance | Create findings from stored interaction rows; retain source-specific assertions and runtime snapshots | Interaction models; `run_interaction_check`; check-run/finding models |
| R3. Context-specific orchestration | Treat DDI, DFI, and DDSI separately; require a matching active condition for DDSI | Orchestrator DDI/DFI/DDSI queries |
| R4. Longitudinal review state | Store findings, acknowledgments, overrides, and selected audit events without mutating canonical evidence | Check and audit models; interaction API |
| R5. Bounded optional generation | Require a persisted finding before explanation; keep Anthropic/OpenFDA outside the core check | Explanation endpoint and LLM service; service-boundary scenarios |

These requirements were reconstructed from the committed implementation and research artifacts. [AUTHOR TO VERIFY: Identify which requirements were specified before implementation and which were documented retrospectively.]

### 3.3 Evaluation design

The committed evaluator, `research/evaluate_rxcheck.py`, creates uniquely named synthetic users, patients, drugs, medication rows, interactions, assertions, conditions, acknowledgments, and overrides in the configured Postgres database. It calls the production `run_interaction_check()` service and records each scenario’s expected behavior, observed behavior, code evidence, pass status, and a conservative interpretation. External-service boundary scenarios replace Anthropic, OpenFDA, or normalization functions with failing sentinels to detect unexpected calls from the core check path.

The script requires `--allow-live-db` because it writes persistent fixtures. It does not automatically remove those fixtures. The recorded results were generated on June 9, 2026. The results file identifies the configured SQLAlchemy database but does not include a database snapshot, exact DDInter release, dependency lock, schema migration revision, operating system, or Git commit SHA. Consequently, the committed run is treated as historical architecture evidence rather than an independently reproduced experiment.

The 26 scenarios were grouped after inspection into four families:

1. Medication identity and pair construction (6 scenarios).
2. Detection, context, ranking, and provenance (9 scenarios).
3. Persistence and review state (7 scenarios).
4. Explanation and external-service boundaries (4 scenarios).

A separate script generated a read-only database profile after the evaluation. A committed test report records one health-endpoint test and two interaction-summary tests. The present review did not rerun these components because the repository contains a credential-bearing default database URL. No live LLM output was generated or scored.

## 4. Artifact architecture

### 4.1 System boundary

RxCheck is a full-stack web prototype. The frontend is implemented with React and Vite. A FastAPI backend provides patient, medication, condition, checking, review, and explanation endpoints. SQLAlchemy models target Postgres-specific UUID, JSONB, and array fields. The production configuration can serve a built frontend from the backend process.

The interface is pharmacist-oriented, but identity is not authenticated. The backend creates a default database user labeled “Default Pharmacist.” This row is a prototype convenience and does not verify professional role.

**Figure 1. Overall RxCheck architecture.** [AUTHOR ACTION REQUIRED: Render and verify `research/diagrams/overall_architecture.mmd`; remove deployment-specific details that are not relevant to the target journal.]

### 4.2 Medication identity and explicit non-resolution

Medication entry first checks local aliases. If no alias exists, the service attempts RxNorm exact search, related ingredient resolution, approximate search with implementation-defined score bands, and NDC lookup. Successful matches create or update a drug row and may store the typed term as an alias.

When no match is obtained, the service creates an `UnresolvedDrugEntry` and a deterministic placeholder RxCUI derived from the normalized text. The medication remains in the patient profile, but `run_interaction_check()` joins patient medications to drugs and filters `is_placeholder = false`. This design keeps unresolved input visible without treating it as verified.

The safety tradeoff is explicit. Exclusion avoids inventing a concept, but it can also omit a clinically important interaction. RxNorm network exceptions are not consistently converted into the placeholder path, fuzzy thresholds have not been calibrated, and the user interface has not been evaluated for whether incomplete-result warnings are noticed.

### 4.3 Interaction and provenance model

The `interactions` table represents a canonical record with one of three counterpart forms: a second drug, a food, or a condition. Database constraints require exactly one counterpart and align counterpart type with interaction type. DDI pairs are stored in lexicographic RxCUI order. Unique indexes constrain DDI, DFI, and DDSI canonical records.

`interaction_source_assertions` stores source, raw and normalized severity, mechanism, management, source record identifier, evidence URL, import time, and raw JSON payload. This separates a normalized interaction entity from source-level claims. The design can retain multiple assertions, but current observed data do not demonstrate mature multi-source integration: the committed profile reported 172,713 DDInter assertions and one manual assertion.

The bulk importer reads eight locally named DDInter CSV partitions, resolves drug names through stored aliases/preferred names, canonicalizes pairs, maps major/moderate/minor severity, upserts DDI rows, and retains a compact raw payload. Rows with unresolved drug names are collected in memory as quarantine rows and are not imported. The repository does not persist a formal quarantine report, include the source files, identify their exact release, or record checksums and complete transformation counts.

### 4.4 Deterministic orchestration and context

For a patient with at least two active non-placeholder medications, the orchestrator creates a set of canonical medication pairs and queries stored DDI rows. It separately queries DFI rows for active medications and DDSI rows for active medications whose condition matches an unresolved patient-condition record. It loads source assertions, summarizes each interaction, and orders results by maximum stored severity, presence of a stored severity conflict, a graph-degree “hub” count, and drug names.

Maximum severity and graph degree are implementation rules, not validated clinical prioritization methods. The “hub” value counts stored interactions involving a drug among the active medications and must not be interpreted as patient risk, danger, evidence strength, or probability.

When at least two verified active medications are present, the service creates an `InteractionCheckRun` and one `InteractionCheckFinding` per interaction. Run snapshots include selected medication fields; finding snapshots include maximum severity, source names, a conflict flag, and acknowledgment-suppression state. When fewer than two verified active medications remain, the service returns a warning without persisting a run.

### 4.5 Acknowledgment, override, and audit-oriented persistence

An acknowledgment associates a patient and interaction with the severity at review, optional expiry, note, and active state. On later checks, a current acknowledgment suppresses presentation when its stored severity is at least the current maximum severity. A higher current severity resurfaces the finding. Suppressed findings remain returned rather than being deleted.

Overrides attach an action and note to a specific finding. They are stored with selected audit events, but the orchestrator does not use them to change later results. The system also stores selected explanation metadata. These features constitute audit-oriented persistence, not a complete or immutable clinical audit trail. Identity is not authenticated, read access is not audited, and compliance controls were not assessed.

### 4.6 Evidence-bounded explanation

The explanation API accepts a finding identifier. It loads the persisted finding and its interaction before calling the LLM service. If an explanation is already linked, the stored response is returned. Otherwise, the service constructs context containing the interaction parties, type, maximum stored severity, source names, the first assertion’s mechanism and management, and up to 500 characters of optional OpenFDA drug-interaction label text per drug.

The system prompt instructs the model to use only supplied context, avoid new interactions or dosing decisions, identify insufficient data, cite sources, and return JSON. The parser checks JSON readability, seven required keys, and whether `sources_used` is a list. A separate check scans the response for names of other non-placeholder drugs stored in the database. The raw response, structured input, prompt version, model metadata, token counts, latency, and validation errors are persisted.

This design restricts access and authority but is not strict factual validation. It does not verify every claim against a source passage, ensure that named sources were supplied, enforce an enumerated confidence value, reconcile multiple assertions, sanitize label text against prompt injection, or evaluate clinical appropriateness. Generic-name OpenFDA fallback can select an unintended label, and label content is not persisted as a versioned document. “Confidence” is model-reported text, not a calibrated probability.

**Figure 2. Finding authority and explanation boundary.** [AUTHOR ACTION REQUIRED: Render and verify `research/diagrams/llm_explanation_boundary.mmd`; amend the figure to show validation failure and external-service failure paths.]

### 4.7 Cost-conscious service separation

The core checker uses already stored medication identifiers and interaction rows. The recorded boundary scenarios indicate that it did not call Anthropic, OpenFDA, or RxNorm at check time. This is a cost-conscious and failure-isolating design property. It does not establish affordability, cost-effectiveness, full offline operation, or suitability for resource-constrained pharmacies. New medication normalization can still require RxNorm, and explanations require network services in the current implementation.

## 5. Results

### 5.1 Recorded formative architecture evaluation

The committed June 9, 2026 result reports all 26 scenarios passing. Table 2 groups the executed assertions. A pass means that observed software behavior matched the scenario’s expected behavior in that run; it does not mean that the behavior is clinically correct.

| Scenario family | Scenarios | Recorded result | Supported interpretation |
|---|---:|---:|---|
| Medication identity and pair construction | 6 | 6 passed | Active/inactive and placeholder filtering, canonical ordering, duplicate-finding behavior, and absence of invented missing interactions matched predefined expectations. |
| Detection, context, ranking, and provenance | 9 | 9 passed | Stored DDI lookup, DFI/DDSI branch behavior, condition gating, ranking, assertion preservation, and conflict flagging matched synthetic fixtures. |
| Persistence and review state | 7 | 7 passed | Run/finding snapshots, findings before explanation, override persistence/non-suppression, acknowledgment suppression, and severity resurfacing matched expectations. |
| Explanation and service boundaries | 4 | 4 passed | Missing finding returned 404, and mocked Anthropic/OpenFDA/RxNorm failures did not affect the tested core check path. |
| **Total** | **26** | **26 passed** | **Selected architecture boundaries were exercised under one synthetic configured-database run.** |

One duplicate-medication scenario requires qualification. Duplicate active medication rows did not duplicate the DDI finding, but the recorded pair-count metric could include a same-RxCUI pair. The evaluation also wrote persistent fixtures and did not test concurrency, security, frontend behavior, performance, source completeness, clinical accuracy, or external-service recovery.

### 5.2 Timestamped database profile

The committed profile was generated at `2026-06-09T19:59:39.927169+00:00`. It reported:

- 152,416 interaction rows.
- 172,714 source assertions.
- 1,967 drugs and 1,934 aliases.
- 71 unresolved drug entries.
- 152,413 DDI rows, one DFI row, and two DDSI rows.
- 172,713 DDInter assertions and one manual assertion.
- 174 interactions with more than one distinct stored severity.
- Five interactions and six assertions identifiable through `evaluation_fixture=true` in assertion payloads.

These are observations from a configured database, not source-release totals. The database is not archived, the exact DDInter release is not recorded, and additional synthetic or manually entered rows cannot be excluded from the repository alone. The counts therefore do not establish completeness, accuracy, or equivalence to DDInter or DDInter 2.0. The almost entirely DDI distribution means that DFI/DDSI architecture capability should not be read as meaningful source coverage.

### 5.3 Focused tests

The committed test report records `3 passed, 3 warnings` in a Python 3.13.5 environment. The tests covered the health response, maximum-severity selection with a conflict flag, DDI summary fields and degree counts, and DDSI condition naming. They did not cover the full orchestrator, most APIs, import behavior, normalization accuracy, LLM outputs, security, concurrency, or migrations.

### 5.4 Unexecuted evaluation components

The repository contains a ten-criterion explanation-boundary rubric and a scoring template. No completed sample is reported. The rubric is therefore an evaluation instrument, not a result. No latency, cost, pharmacist, or clinical reference-case results are available.

## 6. Safety, privacy, governance, and human oversight

RxCheck’s architecture keeps deterministic finding authority outside the LLM, but the prototype is not suitable for care. It has no authentication, session management, route-level authorization, reliable identity binding, row-level controls, immutable audit store, or production privacy program. Its schema can store names, medical-record identifiers, dates of birth, conditions, medications, and notes. Real patient data must not be entered.

The inspected public repository also contains a credential-bearing database URL in runtime configuration, the DDInter importer, and Alembic configuration. The present review did not use that credential. [AUTHOR ACTION REQUIRED BEFORE SUBMISSION: Revoke and rotate the credential, inspect access logs and database contents, remove the secret from active files and Git history, complete a repository-wide secret scan, and document remediation without reproducing the credential.]

The LLM output is intended for pharmacist review and the prompt ends with a reminder to verify institutional references. However, pharmacist oversight has not been studied, and a warning does not substitute for validation. Regulatory status was not analyzed. Current FDA guidance distinguishes categories of CDS software using criteria that require case-specific legal and regulatory assessment [14]; this manuscript makes no claim that RxCheck meets a non-device category.

## 7. Discussion

### 7.1 Principal finding

The recorded evaluation supports a narrow conclusion: in one synthetic configured-database run, the RxCheck artifact behaved consistently with selected architecture requirements. In particular, stored rows rather than the LLM created findings, and the explanation endpoint required a persisted finding. The artifact also made unresolved medication identity explicit, preserved source assertions, condition-gated synthetic DDSI behavior, and retained selected review state.

This result is useful because it makes system authority inspectable. A model that cannot create a finding through the evaluated explanation path presents a different risk profile from a model asked to infer interactions from its training data. Nevertheless, the architecture only removes one source of authority. It does not prevent unsupported mechanism, effect, or management language within an explanation.

### 7.2 Design implications

Four implications follow from the artifact.

First, **finding authority and language rendering should be separately testable**. The core result should remain available when generation or enrichment services fail. This supports operational clarity as well as cost control.

Second, **uncertain identity should be represented as state, not silently resolved**. Placeholder exclusion prevents false certainty, but the excluded medication and resulting coverage gap must be prominent to the reviewer.

Third, **provenance and review state should not be collapsed into display text**. Source assertions, runtime snapshots, acknowledgments, and overrides have different meanings and should remain independently inspectable.

Fourth, **a bounded LLM still requires direct evaluation**. Context construction, source selection, model version, raw output, parsing, and validation failures should be frozen and reviewed. A templated non-LLM explanation is also an important comparator because architecture complexity is justified only if generation provides measured benefit.

### 7.3 Relation to frugal digital health

Frugal health innovation emphasizes workable solutions under constrained resources [12], and WHO digital-health guidance calls for evaluation of benefits, harms, feasibility, resource use, and equity [13]. RxCheck’s separation of local checking from optional paid generation is compatible with cost-conscious design. However, no constrained setting, deployment cost, staffing need, bandwidth condition, or comparator was evaluated. The present study therefore does not label RxCheck a frugal innovation or claim suitability for low-resource care.

### 7.4 Publication and implementation implications

The most appropriate next evidence is not a large clinical trial. Before user research, the artifact needs a secret-free reproducible release, versioned source provenance, clean migrations, pinned dependencies, independent reference cases, and completed explanation-boundary testing. A small pharmacist formative study could then assess whether the boundary and warnings are understood. Clinical performance and workflow outcomes should be investigated only after source quality and security are adequate.

## 8. Threats to validity and limitations

### 8.1 Construct validity

The scenarios operationalize architecture conformance, not safety or clinical correctness. A “source conflict” is a difference among stored severity labels and does not measure independent clinical disagreement. The hub count is graph degree and not clinical risk. Model-reported confidence is not calibrated uncertainty.

### 8.2 Internal validity

The evaluator and expected outcomes were created within the same project. Fixtures were inserted into the configured database, and no clean transactional isolation or automatic teardown is documented. The committed results do not record a Git SHA. The profile was generated after fixture insertion and includes identified synthetic rows.

### 8.3 External validity

No real clinical cases, pharmacists, pharmacies, patient records, EHR integrations, or external deployment sites were studied. Medication normalization was not tested with a representative set of names or codes. The real importer covers only DDI-formatted source files, while DFI and DDSI behavior was tested with synthetic rows.

### 8.4 Reproducibility

The repository does not include the DDInter source files, exact source release, file checksums, database snapshot, populated Alembic schema migration, pinned Python environment, or an isolated one-command test database. Hard-coded local paths and a credential-bearing default URL further impede safe reproduction. The present work therefore reports a committed historical run rather than claiming independent reproducibility.

### 8.5 Explanation and external-service limitations

No generated explanation was scored. Context uses the first assertion’s mechanism and management, label lookup is heuristic and unversioned, structural validation is shallow, prompt injection is not systematically addressed, and provider failures are incompletely handled. The architecture cannot identify a clinically real interaction absent from imported rows.

### 8.6 Security and governance limitations

Authentication, authorization, privacy controls, production secret management, strict CORS, immutable audit, monitoring, backup controls, and regulatory analysis are absent. The exposed database credential is a submission-critical defect. The public repository also lacks a root software license, and compatibility with DDInter’s data terms has not been documented.

## 9. Future work

Future work should proceed in stages.

1. **Security and reproducibility:** rotate and remove exposed secrets; create a safe test configuration; add complete migrations, dependency locks, a clean seeded database, fixture teardown, and a tagged archival release.
2. **Data provenance:** record the exact DDInter release, access date, license, checksums, raw/mapped/quarantined row counts, and transformation logic; distinguish source data from evaluation fixtures.
3. **Reference-case verification:** evaluate a transparent set of DDI and medication-normalization cases with independently specified expected results.
4. **Explanation-boundary evaluation:** freeze contexts and model outputs; score structural validity, drug/severity consistency, unsupported claims, source use, uncertainty, and injection probes; report failures at criterion level.
5. **Human-factors evaluation:** conduct a small pharmacist walk-through or usability study to test warning comprehension, acknowledgment semantics, explanation value, and risk of overreliance.
6. **Coverage and implementation:** add genuine DFI/DDSI/therapeutic-duplication ingestion, stronger terminology mapping, and production security only after earlier validation.
7. **Comparative and outcomes research:** compare templated and generative explanations, measure costs in a defined setting, and consider prospective workflow or clinical outcomes only after technical maturity.

## 10. Conclusion

RxCheck instantiates an evidence-bounded explanation architecture for drug-interaction review. Its deterministic core creates findings from stored interaction rows, while the optional LLM endpoint explains an existing finding. A recorded 26-scenario synthetic run supports selected implementation boundaries, including explicit placeholder exclusion, condition-gated DDSI behavior, provenance storage, review-state persistence, and separation of core checking from external explanation services. These results establish neither clinical performance nor safe deployment. Security remediation, reproducible packaging, source documentation, independent reference cases, explanation assessment, and pharmacist evaluation are necessary before clinical or operational claims can be considered.

## Declarations

### Ethics statement

The committed evaluation describes synthetic software fixtures and does not report human participants or real patient data. [AUTHOR TO VERIFY: Obtain and report the relevant institutional determination regarding human-subjects/ethics review. Any later pharmacist review or usability study may require separate approval or exemption.]

### Funding

[AUTHOR TO SUPPLY: Funding sources and grant numbers, or state that no specific funding was received.]

### Author contributions

[AUTHOR TO SUPPLY: CRediT roles for conceptualization, software, methodology, validation, analysis, writing, supervision, and project administration.]

### Conflicts of interest

[AUTHOR TO SUPPLY: Include any employment, financial, model-provider, hosting-provider, or data-source relationships.]

### Acknowledgments

[AUTHOR TO SUPPLY.]

### Data availability

The repository contains machine-readable recorded evaluation and profile outputs but does not contain the configured database, exact DDInter source files, or a complete reconstruction package. DDInter data are subject to third-party terms [15]. [AUTHOR ACTION REQUIRED BEFORE SUBMISSION: Archive a license-compliant synthetic evaluation package and, if permitted, derived data/provenance metadata with a persistent identifier.]

### Code availability

The inspected code is publicly visible at <https://github.com/shubhamjoshipromail-svg/Pharmacy> at commit `6b763c03a69e33031f196eceb598899ee08a1cba`. At the time of review, the repository had no root software license and contained an exposed database credential. [AUTHOR ACTION REQUIRED BEFORE SUBMISSION: Publish a remediated, licensed, tagged, and DOI-archived release; cite that release instead of the unsafe snapshot.]

## References

1. Saverno KR, Hines LE, Warholak TL, Grizzle AJ, Babits L, Clark C, et al. Ability of pharmacy clinical decision-support software to alert users about clinically important drug-drug interactions. *J Am Med Inform Assoc.* 2011;18(1):32-37. doi:10.1136/jamia.2010.007609.
2. Hussain MI, Reynolds TL, Zheng K. Medication safety alert fatigue may be reduced via interaction design and clinical role tailoring: a systematic review. *J Am Med Inform Assoc.* 2019;26(10):1141-1149. doi:10.1093/jamia/ocz095.
3. Nelson SJ, Zeng K, Kilbourne J, Powell T, Moore R. Normalized names for clinical drugs: RxNorm at 6 years. *J Am Med Inform Assoc.* 2011;18(4):441-448. doi:10.1136/amiajnl-2011-000116.
4. Xiong G, Yang Z, Yi J, Wang N, Wang L, Zhu H, et al. DDInter: an online drug-drug interaction database towards improving clinical decision-making and patient safety. *Nucleic Acids Res.* 2022;50(D1):D1200-D1207. doi:10.1093/nar/gkab880.
5. Tian Y, Yi J, Wang N, Wu C, Peng J, Liu S, et al. DDInter 2.0: an enhanced drug interaction resource with expanded data coverage, new interaction types, and improved user interface. *Nucleic Acids Res.* 2025;53(D1):D1356-D1362. doi:10.1093/nar/gkae726.
6. Lewis P, Perez E, Piktus A, Petroni F, Karpukhin V, Goyal N, et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: *Advances in Neural Information Processing Systems 33.* 2020:9459-9474. <https://arxiv.org/abs/2005.11401>.
7. Singhal K, Azizi S, Tu T, Mahdavi SS, Wei J, Chung HW, et al. Large language models encode clinical knowledge. *Nature.* 2023;620(7972):172-180. doi:10.1038/s41586-023-06291-2.
8. Labkoff S, Oladimeji B, Kannry J, Solomonides A, Leftwich R, Koski E, et al. Toward a responsible future: recommendations for AI-enabled clinical decision support. *J Am Med Inform Assoc.* 2024;31(11):2730-2739. doi:10.1093/jamia/ocae209.
9. World Health Organization. *Ethics and Governance of Artificial Intelligence for Health: WHO Guidance.* Geneva: World Health Organization; 2021. <https://www.who.int/publications/i/item/9789240029200>.
10. Hevner AR, March ST, Park J, Ram S. Design science in information systems research. *MIS Quarterly.* 2004;28(1):75-105. doi:10.2307/25148625.
11. Peffers K, Tuunanen T, Rothenberger MA, Chatterjee S. A design science research methodology for information systems research. *J Manag Inf Syst.* 2007;24(3):45-77. doi:10.2753/MIS0742-1222240302.
12. Tran VT, Ravaud P. Frugal innovation in medicine for low resource settings. *BMC Med.* 2016;14:102. doi:10.1186/s12916-016-0651-1.
13. World Health Organization. *WHO Guideline: Recommendations on Digital Interventions for Health System Strengthening.* Geneva: World Health Organization; 2019. <https://www.who.int/publications/i/item/9789241550505>.
14. US Food and Drug Administration. *Clinical Decision Support Software: Guidance for Industry and Food and Drug Administration Staff.* January 2026. <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software>.
15. DDInter. Terms: disclaimer and data licensing. [accessed 2026 Jul 14]. <https://ddinter.scbdd.com/terms/>.

---

## Author-facing manuscript status note

This revision is the strongest complete manuscript supported by the inspected repository, but it is intentionally **not labeled ready for submission** while bracketed author actions remain. It does not invent missing experiments, data provenance, ethics determinations, or disclosures.
