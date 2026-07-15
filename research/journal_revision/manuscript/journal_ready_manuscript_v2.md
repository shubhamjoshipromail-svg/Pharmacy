# A Deterministic Finding-Authority Boundary for Optional Generative Explanation in Drug-Interaction Review: Design and Formative Evaluation of the RxCheck Prototype

**Authors:** [AUTHOR TO SUPPLY: names, degrees, affiliations, and ORCID identifiers]

**Corresponding author:** [AUTHOR TO SUPPLY]

**Manuscript type:** Design-science health-informatics system paper with formative software evaluation

**Artifact snapshot initially reviewed:** `6b763c03a69e33031f196eceb598899ee08a1cba`

**Evidence synthesis snapshot:** `2861fc7cf845246ea6656bbf993ee4093e3d30d6`

> **Prototype warning:** RxCheck is not clinically validated, is not intended for clinical use, and must not be used with real patient data in its current form. A missing stored finding is not evidence that no clinical interaction exists.

## Abstract

### Background

Large language models (LLMs) may make structured drug-interaction findings easier to read, but fluent prose should not determine whether a safety-relevant finding exists. Separating finding authority from language generation may reduce that risk without guaranteeing explanation correctness.

### Objective

To describe and formatively evaluate RxCheck, a prototype in which deterministic stored-data logic creates findings and optional generated prose is downstream of a persisted finding. Secondary aims examined normalization, provenance, operational behavior, traceability, and output validation.

### Methods

We inspected the FastAPI/React/PostgreSQL artifact without modifying application source. The 26-scenario evaluator was repeated in three fresh databases. We tested 30 frozen outputs against the unchanged explanation validator; audited eight recovered DDInter files; measured 720 core calls over eight synthetic workloads with 150,000 unrelated background interactions; tested 15 traceability criteria; and ran 30 normalization cases separately verified against RxNorm release 06-Jul-2026/API 3.1.353. We also conducted a targeted citation review. No clinician, patient, clinical outcome, or live generated explanation was evaluated.

### Results

All architecture repetitions passed 26/26 scenarios (78/78 executions), with no external-service calls reported on exercised core paths. The validator accepted 3/3 valid controls but cleanly rejected only 5/27 invalid cases; 15 were accepted and 7 raised exceptions. The source bundle contained 222,383 rows, 160,235 unique canonical identifier pairs, and 62,148 cross-file duplicates; semantic release and transformation lineage were unavailable. All 720 core calls returned expected counts; workload p95 latency ranged from 2.586 to 245.124 ms. Traceability passed 10/15 criteria. Normalization passed 22/30 strict cases but failed all four multi-ingredient cases and selected misspelling, unknown-input, and outage behaviors. Related work precluded broad novelty claims.

### Conclusions

The finding-authority boundary survived repeated synthetic testing, but adjacent controls did not: output validation, complete lineage, broad traceability, and general normalization claims were unsupported. This is an incremental architecture case study and negative formative evaluation, not evidence of clinical accuracy, safe explanation, workflow benefit, or deployment readiness.

**Keywords:** clinical decision support; drug interactions; pharmacy informatics; large language models; design science; provenance; medication normalization; formative evaluation

## 1. Introduction

Drug-drug interaction (DDI) decision support is established but imperfect. Standardized testing has shown variation among pharmacy clinical decision-support products, and alert design, clinical relevance, and role tailoring affect how alerts are received [1-3]. A recent systematic review found little high-quality evidence that electronic DDI alerts improve patient-important outcomes, reinforcing the need to distinguish software behavior from clinical benefit [5]. Patient-context algorithms can make selected alerts more specific, but such methods require explicit clinical rules and evaluation in representative workflows [4].

Generative models create a separate safety problem. An LLM may convert structured information into concise prose, but it may also omit, contradict, or add information. Retrieval-augmented generation combines parametric generation with retrieved information [9], and medical RAG benchmarks show that retrieval configuration can affect medical question-answering performance [10]. Neither retrieval nor a prompt instruction establishes factual entailment, clinical appropriateness, or safe use. Medical LLM evaluations continue to identify gaps despite strong benchmark performance [11]. Responsible AI-enabled clinical decision support therefore requires staged validation, human oversight, governance, and monitoring [14,15].

This study examines authority rather than model capability. RxCheck is a pharmacist-oriented research prototype that uses stored medication identifiers and interaction rows for its core check. An optional explanation endpoint accepts an existing finding identifier. We use **finding authority** to mean the ability to create a canonical check finding in the evaluated workflow. We use **evidence-bounded explanation** to describe an access and authority boundary: structured records create the finding, and generated prose is downstream. The term does not mean that every generated sentence is supported.

The primary research question was:

> To what extent does the inspected RxCheck prototype enforce a boundary in which deterministic stored-data logic creates drug-interaction findings and an optional LLM is limited to explaining a persisted finding?

Secondary questions were:

1. How reproducible is the recorded architecture behavior from a fresh local database?
2. What do targeted tests show about explanation-output validation, medication normalization, source provenance, core operational behavior, and review-state traceability?
3. Which claims remain supportable after the closest related-work comparison?

The study is a design-science evaluation of an artifact [18,19]. It is not a clinical-effectiveness, diagnostic-accuracy, human-factors, economic, security-certification, or regulatory study.

## 2. Related Work and Design Context

### 2.1 DDI decision support and alert presentation

DDI checking predates RxCheck by decades. Saverno et al. reported variable ability among pharmacy systems to identify selected clinically important interactions [1]. Hussain et al. found that alert interaction design and role tailoring may influence alert acceptance, while emphasizing heterogeneous methods and the need to report both acceptance and patient outcomes [2]. Expert recommendations for DDI alert usability already specify concise presentation of the interacting drugs, seriousness, clinical consequences, mechanism, contextual factors, actions, and evidence [3]. These elements can be rendered deterministically; generated prose is not required to display them.

Contextualized DDI algorithms also precede RxCheck. Chou et al. developed eight expert-authored algorithms incorporating patient and drug characteristics, validated computable artifacts with synthetic records, and tested them retrospectively at one hospital [4]. Their work addresses alert specificity using EHR context. RxCheck's patient-context behavior is narrower: it contains distinct DDI, drug-food interaction (DFI), and drug-disease interaction (DDSI) branches, with synthetic condition gating for DDSI, but it does not implement or validate comparable patient-specific DDI algorithms.

Clinical outcome evidence remains limited. Holbrook et al. identified eight controlled DDI-alert studies and found no significant improvement in patient-important outcomes, although selected prescribing behavior changed [5]. Consequently, architecture conformance, alert presentation, and patient outcomes must be reported as separate constructs.

### 2.2 Medication identity and interaction knowledge

RxNorm provides normalized names and identifiers for clinical drugs and relationships among drug concepts [6]. Mapping user input to an ingredient identifier can support deterministic comparison, but performance depends on the application logic used for exact, normalized, approximate, related-concept, and National Drug Code (NDC) resolution. Terminology infrastructure does not by itself validate an application's mapping behavior.

DDInter is a curated drug-interaction resource with structured DDI associations and risk annotations [7]. DDInter 2.0 expanded the published resource to additional interaction types and coverage [8]. RxCheck's recovered source bundle, however, consists of eight five-column DDI files. Their exact semantic release was not present in the filenames, headers, URLs, or retained import artifacts. The published DDInter 2.0 resource and the recovered RxCheck input bundle therefore must not be treated as identical. DDInter's terms identify CC BY-NC-SA 4.0 and caution that the resource may be incomplete or contain errors [23].

### 2.3 Generated and retrieval-grounded explanation

RAG is an established model architecture rather than an RxCheck contribution [9]. MedRAG/MIRAGE evaluated medical RAG across 7,663 questions and 41 corpus, retriever, and model combinations, demonstrating the importance of configuration and evaluation [10]. RxCheck does not implement or evaluate a comparable retrieval system. It supplies a selected finding, limited source fields, and optional label excerpts to a proprietary model.

Natural-language DDI explanation is also prior work. ExDDI generates pharmacokinetic and pharmacodynamic explanations for learned DDI predictions [12]. Its task differs from RxCheck: ExDDI explains predicted interactions, including unknown interactions between known drugs, whereas RxCheck makes prose available only after a stored-data finding exists. This distinction supports a narrower authority-boundary comparison, not a claim that generated DDI explanation is new. A 2026 non-peer-reviewed preprint also describes a high-level combination of rule-based DDI reasoning and LLM-assisted explanation [13], further limiting any first-of-kind claim.

### 2.4 Provenance and reusable CDS artifacts

Provenance concepts and standards predate RxCheck. FHIR Provenance distinguishes targets, activities, agents, and source entities and relates provenance to AuditEvent [16]. AHRQ's CDS Connect program supported reusable, standards-based CDS knowledge artifacts and authoring tools [17]. RxCheck uses custom interaction-source assertions, check-run snapshots, finding snapshots, and selected event records. It does not claim FHIR conformance, interoperable knowledge artifacts, or a complete audit trail.

### 2.5 Positioning of RxCheck

Table 1 summarizes the closest method classes. RxCheck's defensible contribution is an incremental, inspectable instantiation of a conservative authority allocation, evaluated with both positive and negative software evidence.

**Table 1. Targeted related-work comparison.**

| Approach | Finding authority | Explanation or presentation | Evaluation maturity | Relationship to RxCheck |
|---|---|---|---|---|
| Conventional pharmacy DDI CDS [1-3] | Stored rules/knowledge bases | Structured alerts and recommended content | Standardized product testing, consensus, and systematic review | DDI detection and alert content are established; RxCheck does not claim improved detection or alert burden |
| Contextualized DDI algorithms [4] | Expert rules using patient/drug context | Context-specific computable alerts | Synthetic validation and retrospective single-hospital testing | More clinically contextualized than RxCheck's limited synthetic condition gating |
| Deterministic source-filled template | Same stored finding as RxCheck | Fixed rendering of drug, severity, mechanism, management, and evidence fields | Not evaluated in this project | Required baseline before any benefit can be attributed to generation |
| ExDDI [12] | Learned DDI prediction | Natural-language explanation of predicted interactions | Peer-reviewed conference experiments | Shows generated DDI explanation is not novel; authority and workflow differ |
| Medical RAG [9,10] | Model answer generation using retrieval | Retrieved-context generation | Large benchmark literature | Establishes RAG context; RxCheck did not benchmark retrieval or explanation quality |
| Provenance standards and CDS artifacts [16,17] | Standards-based CDS/resource processes | Not primarily a generation method | Published standard and federal program | RxCheck's custom partial traceability model is neither novel nor standards-conformant |
| RxCheck | Stored interaction rows on the evaluated core path | Optional prose after a persisted finding | Formative synthetic/local tests; no clinical or human evaluation | Incremental authority-boundary instantiation with documented failures |

## 3. Methods

### 3.1 Study design and artifact scope

We treated RxCheck as a design-science artifact and evaluated selected requirements through seven evidence units. The initially reviewed application snapshot was Git commit `6b763c03a69e33031f196eceb598899ee08a1cba`. Subsequent commits in the research branch added review and evidence materials without modifying the original manuscript or application source. Each executable evidence package records its execution-time Git revision, last commit affecting evaluated paths, script and fixture hashes, environment, raw outputs, and limitations. The consolidated evidence review was recorded at `2861fc7cf845246ea6656bbf993ee4093e3d30d6`.

The artifact comprises a React/Vite frontend, FastAPI backend, SQLAlchemy data model, and PostgreSQL database. Medication entry uses RxNorm-oriented web-service calls and local aliases. The core checker queries stored interactions, creates a check run and findings when at least two verified active medications are present, and applies selected acknowledgment state. An explanation route loads a finding before constructing model context. OpenFDA label excerpts and Anthropic are used only on the optional explanation path.

### 3.2 Architecture requirements

The evaluated requirements were reconstructed from the implementation and prior documentation. The authors must distinguish requirements specified before implementation from those documented retrospectively.

| Requirement | Evaluated behavior | Authority boundary |
|---|---|---|
| R1. Medication identity | Attempt resolution to stored RxNorm-oriented concepts; exclude explicit placeholders | Normalization determines which medications can enter candidate pairs |
| R2. Structured finding authority | Create findings from stored interaction rows | LLM has no finding-creation role on the evaluated endpoint |
| R3. Context branches | Query DDI, DFI, and condition-gated DDSI records separately | Stored records and selected patient context control finding creation |
| R4. Review-state persistence | Store selected runs, findings, acknowledgments, overrides, and events | Review state can affect presentation but not canonical interaction existence |
| R5. Optional explanation | Require an existing finding before model invocation | Generated prose is downstream and non-authoritative |

Figure 1 should be rendered from `figures/authority_boundary_v2.mmd`. The diagram explicitly shows both the intended authority boundary and the normalization/output-validation failures observed in this study.

### 3.3 Evaluation protocols

Table 2 lists the evidence units. Full protocols, fixtures, scripts, raw outputs, logs, and environment records are retained in `research/journal_revision/evidence/`.

**Table 2. Formative evaluation protocols.**

| Unit | Objective | Inputs and comparison | Prespecified decision |
|---|---|---|---|
| E01 Architecture reproduction | Reproduce the historical 26-scenario result from empty databases | Unchanged evaluator and core service; three fresh databases | Every repetition must pass 26/26 with identical outcomes and no reported external APIs |
| E02 Validator conformance | Test whether output validation enforces the documented contract | 3 valid and 27 invalid frozen outputs; no model/database/API | Valid controls accepted and every invalid case controlled-rejected |
| E03 Source provenance | Recover source identity and raw-to-database lineage | Git/history, local files, official live downloads, importer/profile artifacts | Full pass requires exact release and reconstructable transformation accounting |
| E04 Core latency/repeatability | Measure bounded local core behavior | Eight workloads, 90 measured calls each, 150,000 unrelated background rows | Correct counts, no exceptions/external calls, p95 <1,000 ms, repeatability rule met |
| E05 Traceability semantics | Test selected history/source/snapshot/review semantics | 15 criteria over fresh synthetic patients and live-row mutation | All 15 criteria must pass |
| E06 Normalization | Test frozen terminology mappings and failure behaviors | 30 cases; separate official verification before application execution | All 30 reference and application criteria must pass |
| E07 Citation/related work | Verify bibliography and novelty framing | 15 existing references and six prespecified comparison categories | Every reference classified; all categories covered; conservative novelty statement produced |

### 3.4 Isolated architecture reproduction

Evidence 01 built PostgreSQL 16.14 from the recorded source archive and ran on macOS 15.7.7 arm64 with Python 3.12.13. Each repetition started from an empty loopback-only database with a guarded name, created the 20-table schema using `Base.metadata.create_all()`, executed the unchanged historical evaluator, retained full JSON and console output, and removed the cluster. Alembic was not used because the committed migration was empty.

The 26 scenarios covered medication/pair construction (6), detection/context/ranking/provenance (9), persistence/review state (7), and explanation/service boundaries (4). The evaluator used synthetic fixtures authored for the project. A pass meant observed software behavior matched the predefined expectation, not that the behavior was clinically correct.

### 3.5 Explanation-validator conformance

Evidence 02 tested deterministic functions in the unchanged explanation parser and response builder. The suite contained valid controls and invalid cases spanning malformed/trailing/multiple JSON, wrong top-level types, missing/extra/duplicate keys, field-type errors, empty values, confidence vocabulary, severity/source inconsistency, unexpected drugs/food, unsupported dose/mechanism content, and prompt-injection-shaped instructions. No live model, database connection, or external API was used. Outcomes were accepted, controlled-rejected, falsely accepted, or unhandled exception.

### 3.6 DDInter source-provenance audit

Evidence 03 inventoried all Git objects and history, importer expectations, recovered file metadata, macOS quarantine origin metadata, file sizes and SHA-256 values, headers, and row-level structural properties. It downloaded fresh copies from the eight recorded official DDInter URLs on July 15, 2026 and compared hashes and bytes. It then searched for a semantic version, alias snapshot, quarantine output, import log, database export, and other transformation artifacts and compared raw source counts with the committed database profile. Source rows were not copied into Git.

### 3.7 Core latency and repeatability

Evidence 04 used a fresh loopback PostgreSQL 16.14 database and the unchanged `run_interaction_check()` service. Eight workloads crossed medication-list sizes of 2, 10, 25, and 50 with zero or approximately 10% matched candidate pairs. The database contained 150,000 unrelated interactions/assertions and 159 workload-matched rows. Each workload received 5 warmups followed by three passes of 30 measured calls (90 per workload; 720 total). Failing sentinels replaced Anthropic, OpenFDA, and normalization entry points. Every call was checked for patient, medication, pair, finding, summary, run, and persisted-finding counts, then deleted and cascade cleanup verified.

### 3.8 Persistence and traceability audit

Evidence 05 used four synthetic patients and 15 prespecified criteria in a fresh local database. The criteria covered a below-threshold check, attempt history, duplicate findings, distinct-pair accounting, run/finding source agreement, medication and finding snapshots, historical display reconstruction, acknowledgment creation/suppression/escalation/deactivation, removal identity, override creation, and future-check semantics. After a completed run, live medication, drug, and assertion rows were mutated to test which historical fields remained recoverable.

### 3.9 Medication-normalization benchmark

Evidence 06 froze 30 cases before application execution. Expected concepts and behaviors were separately rechecked against RxNorm release `06-Jul-2026`, API version `3.1.353`; three NDC cases also had official DailyMed label support. Cases included exact ingredients, brands, misspellings, a candidate-return case, four multi-ingredient products, NDCs, a constructed non-drug token, empty input, and an injected network failure. Every application case began with empty terminology tables. The strict criterion included expected concept set, resolution state, status semantics, placeholder behavior, and controlled failure where applicable.

### 3.10 Citation and related-work review

Evidence 07 checked the 15 references in the prior draft against publisher, proceedings, PubMed, DOI-registration, agency, standards-body, or data-provider records. It classified claim fit as direct or bounded/context-only and performed a targeted comparison with rule-based DDI CDS, deterministic alert content, contextualized algorithms, provenance-aware CDS, medical RAG, and natural-language DDI explanation. This was not a registered systematic review and did not use duplicate screening.

### 3.11 Safety, preservation, and analysis

All database-writing protocols rejected non-loopback hosts and used disposable databases. No committed remote database credential was used. Application source, the original manuscript, the historical evaluation, and prior review materials were treated as read-only. The original manuscript's Git object remained `cd5c4ab332461544a1f083bfcfd65fd60b2b49e4` throughout the evidence cycle.

Results are descriptive. No inferential clinical statistics were calculated because cases were purposive and the evaluated unit was software behavior. Percentiles in Evidence 04 used linear interpolation over ordered observations. Proportions in the validator, traceability, and normalization suites describe conformance to the frozen cases; they are not population error rates.

### 3.12 Ethics and human participation

No patients, clinicians, identifiable health records, or clinical decisions were studied. All evaluation patients and medications were synthetic. [AUTHOR TO SUPPLY: institutional determination regarding whether the software-only synthetic study required ethics review or qualified for exemption/non-human-subjects status.]

## 4. Results

### 4.1 Architecture reproduction

All three fresh-database repetitions passed 26/26 scenarios, for 78/78 total scenario executions. Outcomes were identical across repetitions. No paid or free external API call was reported. The expected 20 tables were created from an initially empty database in every repetition. The disposable clusters were stopped and removed.

**Table 3. Repeated architecture results.**

| Scenario family | Scenarios per repetition | Repetitions | Passing executions | Interpretation |
|---|---:|---:|---:|---|
| Medication identity and pair construction | 6 | 3 | 18/18 | Selected placeholder, activity, ordering, and duplicate-finding behaviors matched expectations |
| Detection, context, ranking, and provenance | 9 | 3 | 27/27 | Stored-row lookup, synthetic DFI/DDSI branches, ranking, assertions, and severity-difference flags matched expectations |
| Persistence and review state | 7 | 3 | 21/21 | Selected run/finding, acknowledgment, escalation, and override behaviors matched expectations |
| Explanation and service boundaries | 4 | 3 | 12/12 | Existing-finding requirement and core independence from three external services matched expectations |
| **Total** | **26** | **3** | **78/78** | **Repeated synthetic architecture conformance in one recorded environment** |

This result supports the finding-authority boundary on the tested paths. It does not validate interaction content. Scenario 15 specifically demonstrated that an unstored pair yields no finding; this behavior must not be interpreted clinically.

### 4.2 Explanation-validator conformance

The validator contract failed. All three valid controls were accepted. Of 27 expected-invalid cases, only 5 (18.5%) were controlled-rejected, 15 (55.6%) were falsely accepted, and 7 (25.9%) produced unhandled exceptions. Overall, 8/30 expectations were met.

Controlled rejections covered malformed JSON, leading prose, a missing required key, a string in place of `sources_used`, and one unexpected drug already present in the stubbed database. False accepts included trailing prose, a second JSON object, duplicate and extra keys, empty required strings, invalid confidence, wrong severity, invented or empty sources, an unknown fabricated drug, an unexpected food, unsupported dose/mechanism content, and injection-shaped text. Wrong top-level and field types reached `AttributeError` or Pydantic `ValidationError` exceptions.

Code-path inspection explained the results. `JSONDecoder.raw_decode()` was used without checking full input consumption. The parser assumed a top-level object, verified only required-key presence and the outer list type of `sources_used`, and scanned only names of stored non-party drugs. The result supports a description of limited custom checks, not strict schema or semantic validation.

### 4.3 DDInter source provenance

All eight expected files were recovered with official origin URLs and acquisition timestamps from April 16, 2026. Fresh official downloads on July 15, 2026 were byte-identical and had the same SHA-256 values. The files contained five fields: two DDInter identifiers, two names, and severity level.

The concatenated files contained 222,383 rows. There were 160,235 unique canonical identifier pairs and 62,148 cross-file duplicates (27.9% of concatenated rows); no within-file duplicate was found. Required fields were complete, no self-pair occurred, 1,939 identifiers had consistent names, and no canonical identifier pair had conflicting severity labels.

The full-provenance criterion failed. No semantic release identifier, frozen alias state, durable quarantine rows, complete import log, inserted-versus-conflicted counts, or clean database export was available. The configured database profile reported more DDInter assertions than the recovered unique source records could explain. Therefore, database totals are unreconciled observations and the bundle cannot be labeled DDInter 2.0.

### 4.4 Core latency, correctness, and repeatability

All 720 measured calls returned the expected counts, created nonempty run identifiers, persisted expected finding counts, and completed without exceptions or sentinel-detected external calls. All eight workloads met the local p95 and repeatability criteria. Cleanup left no check runs or findings.

**Table 4. Local warm-cache core-check latency.**

| Medications | Candidate pairs | Findings | Median, ms | p95, ms | Maximum, ms |
|---:|---:|---:|---:|---:|---:|
| 2 | 1 | 0 | 2.237 | 2.586 | 4.088 |
| 2 | 1 | 1 | 3.007 | 3.174 | 3.208 |
| 10 | 45 | 0 | 3.076 | 3.510 | 4.986 |
| 10 | 45 | 5 | 5.448 | 6.035 | 21.418 |
| 25 | 300 | 0 | 17.720 | 18.787 | 20.080 |
| 25 | 300 | 30 | 25.136 | 26.493 | 28.200 |
| 50 | 1,225 | 0 | 204.722 | 209.953 | 211.843 |
| 50 | 1,225 | 123 | 231.768 | 245.124 | 251.869 |

These values describe one sequential, synthetic, warm-cache, core-service benchmark. End-to-end latency, concurrency, throughput, production behavior, external-service latency, and clinical usefulness were not measured.

### 4.5 Persistence and traceability semantics

Ten of 15 criteria passed and the broad traceability contract failed. Passing behaviors included a controlled below-threshold return, duplicate-finding prevention, selected medication and finding snapshots, acknowledgment creation, same-severity suppression, higher-severity resurfacing, deactivation state, override persistence, and the finding-level historical semantics of overrides.

Five failures materially narrow the audit claim:

1. a below-threshold attempt persisted no run;
2. duplicate medication rows produced an overstated pair count despite one distinct pair;
3. a run reported DDInter while the finding's source union was manual;
4. mechanism, management, evidence URL, source record, and raw payload were not recoverable from the historical finding after live assertion mutation; and
5. acknowledgment removal was attributed to a default user rather than the tested workflow user.

The system therefore provides audit-oriented persistence of selected events, not a complete, immutable, identity-authenticated, or compliance-grade audit trail.

### 4.6 Medication-normalization benchmark

All 30 expected outcomes were independently reverified against official terminology sources, and all 30 application cases executed. The strict application result was 22/30 (73.3%); 8 cases failed and one injected failure escaped as an exception. Because the cases were purposively selected, 73.3% is not an estimate of real-world accuracy.

**Table 5. Normalization results by case category.**

| Category | Passed | Failed | Main interpretation |
|---|---:|---:|---|
| Exact ingredient | 8 | 0 | Bounded exact-name conformance supported |
| Brand | 7 | 0 | Bounded brand-to-ingredient conformance supported |
| Misspelling, automatic | 2 | 2 | Candidate validity and status semantics were inconsistent |
| Misspelling candidate | 1 | 0 | One candidate-return behavior passed |
| Multi-ingredient | 0 | 4 | Only the first related ingredient was retained |
| NDC | 3 | 0 | Three frozen NDC-to-ingredient cases passed |
| Constructed non-drug token | 0 | 1 | An unresolvable numeric candidate was accepted as non-placeholder |
| Empty input | 1 | 0 | Controlled visible non-resolution passed |
| Injected service failure | 0 | 1 | `ConnectError` escaped with no stored unresolved record |

The combination failures arise from a scalar return contract that selects the first related ingredient. Approximate matching can accept a high-scoring candidate without requiring active concept properties or a resolvable ingredient. One correct misspelling mapping was labeled `matched_exact`, showing that stored status labels do not reliably identify the match method.

### 4.7 Citation support and novelty

All 15 references in the prior draft had verified bibliographic identities. Nine directly supported the bounded manuscript use; six were context-only and could not support system-specific conclusions. The original RAG reference should use the official NeurIPS record rather than the arXiv landing page. The published DDInter 2.0 article supports the resource's capabilities but not the semantic identity of the recovered source bundle.

The related-work comparison found precedent for conventional DDI checking, contextualized DDI algorithms, recommended deterministic alert content, medical RAG, natural-language DDI explanation, provenance standards, and high-level rule-plus-LLM combinations. The broad novelty claim therefore failed. The remaining contribution is the transparent implementation and formative evaluation of the finding-authority boundary together with the negative evidence reported above.

## 5. Discussion

### 5.1 Principal findings

The central architecture result was narrow but consistent: the unchanged evaluator passed 26/26 scenarios in each of three fresh databases, and the explanation endpoint required an existing finding. Across the exercised core paths, Anthropic, OpenFDA, and RxNorm were not invoked. This supports an inspectable separation between finding creation and optional generated prose.

The adjacent controls were substantially weaker. The output validator met only 8/30 frozen expectations and allowed unsupported or inconsistent content to pass. Complete DDInter lineage could not be reconstructed. Five traceability criteria failed, including source and actor attribution. Medication normalization failed cases that can remove ingredients from the candidate set or falsely accept an invalid candidate. These results demonstrate why an architecture boundary should not be treated as a safety guarantee.

### 5.2 Authority boundaries are necessary but insufficient

Preventing an LLM from creating a finding reduces one class of authority. It does not ensure that the underlying finding is correct, that medication identity is complete, or that explanatory prose is faithful. RxCheck can miss an interaction when the interaction row is absent, an ingredient is omitted, a candidate is falsely resolved, or an external terminology call fails. The LLM can then misstate severity, source, mechanism, management, or other content because the current validator does not enforce those dimensions.

The relevant design implication is layered. A safety-oriented system needs reliable terminology handling, versioned and traceable interaction knowledge, deterministic finding logic, faithful historical evidence, strict output controls, and human review. Strength in one layer cannot compensate silently for failure in another.

### 5.3 Deterministic templates are the essential comparator

DDI alert guidance already identifies the content clinicians may need [3]. The same structured fields supplied to the model could populate a deterministic template with exact field-to-text correspondence. RxCheck did not compare that baseline with generated prose. It therefore cannot claim better readability, comprehension, usefulness, time, safety, or trust calibration. Future explanation evaluation should begin only after the validator is remediated and should compare no explanation, a deterministic template, and generated prose over identical findings.

### 5.4 Input identity is part of finding authority

The authority boundary begins before the core query. A medication omitted from the resolved ingredient set never participates in a candidate pair. The four combination-product failures show that a scalar normalization result is structurally inadequate for multi-ingredient products. The invalid approximate candidates and uncontrolled outage show that fail-visible behavior is incomplete. Accordingly, the design principle should be revised from universal “normalize or explicitly reject” language to a tested, conditional statement with a visible incomplete-result requirement.

### 5.5 Provenance and traceability must be versioned at the displayed-evidence grain

The source audit recovered strong file identity but not transformation lineage. The traceability audit separately showed that selected run/finding fields remain stable while detailed displayed evidence does not. These are different provenance layers: source acquisition, transformation, canonical interaction construction, run-time finding selection, displayed evidence, and review action. A future design should assign stable identifiers and versioned snapshots at each layer and use authenticated actors. Existing standards such as FHIR Provenance and AuditEvent provide relevant concepts [16]; RxCheck's current custom schema should not be presented as equivalent.

### 5.6 Operational result and its limits

The local latency benchmark showed correct and repeatable behavior through 50 medications and 1,225 candidate pairs under the specified sequential conditions. This is useful engineering evidence for a formative paper. It is not a production service-level objective. The synthetic database, warm cache, one machine, absence of concurrency, and exclusion of frontend/network/external services all limit generalization.

### 5.7 Safety, privacy, governance, and regulation

The public repository contains an exposed database credential in historical source. It was not used during this evidence cycle. Revocation/rotation, provider-log inspection, determination of whether identifiable data were ever present, active-tree and history remediation, and a full secret scan require repository-owner and provider authority. Until those actions are complete, the repository is unsafe for real patient data and should not be linked from a submission as a remediated release.

The prototype also lacks authenticated user identity and production-grade authorization, audit, and governance controls. Actor-attribution failure was observed directly in Evidence 05. No claim of HIPAA compliance, FDA classification, cybersecurity readiness, or clinical deployment is made. FDA CDS guidance requires function-specific legal and regulatory analysis [22]; this study did not perform one.

WHO guidance emphasizes ethics, autonomy, transparency, accountability, inclusiveness, and safety in health AI [15], and responsible AI-CDS recommendations emphasize staged evaluation and monitoring [14]. The present work belongs at a preclinical formative stage. Its appropriate next steps are remediation, independent technical reproduction, and pharmacist evaluation—not deployment.

### 5.8 Cost-consciousness without a frugality claim

Separating local stored-data checking from optional paid generation can isolate external failures and optional cost. Frugal innovation, however, concerns effective solutions under constrained resources [20], and WHO digital-health guidance calls for evaluation of benefits, harms, feasibility, resource use, and equity [21]. RxCheck was not evaluated in a constrained setting, and no deployment cost, staffing model, bandwidth requirement, or comparator was measured. Cost-conscious separation is therefore a design rationale only.

### 5.9 Strengths

This study's principal strength is claim discipline supported by retained evidence. Tests were executed against unchanged application functions, used disposable local databases, recorded complete raw outputs and environments, and included prespecified failure criteria. The normalization benchmark introduced an official-reference-verified axis independent of the project's own expected architecture. Negative results were retained rather than reframed as partial successes. The original paper and historical artifacts remained unchanged.

### 5.10 Limitations and threats to validity

**Construct validity:** The architecture scenarios measure conformance to project-defined behavior, not clinical correctness. The validator suite measures enforcement of a frozen contract, not live-model defect prevalence. Traceability criteria reflect a bounded interpretation of audit semantics. Latency measures the core function, not user-perceived response time.

**Internal validity:** All evidence was produced within one AI-assisted research process. Scripts and generated fixtures were inspected and executed, but no second researcher independently audited the logic. Some schema setup used SQLAlchemy metadata rather than Alembic. The validator audit inferred, but did not database-test, the risk of persistence before response-builder failure.

**External validity:** Evaluation used synthetic patients and one macOS arm64 machine. No pharmacy, pharmacist, clinical dataset, real DDInter-derived rebuilt database, concurrency, or production deployment was studied. Purposive case proportions cannot be generalized to real input distributions.

**Reproducibility validity:** Raw evidence, hashes, environment records, and disposable harnesses are retained. Full reproducibility remains incomplete because dependencies are not packaged as a one-command environment, the migration is empty, the DDInter transformation cannot be reconstructed, source CSVs are external, and no independent rerun exists.

**Literature validity:** The related-work review was targeted rather than systematic and may miss differently indexed, paywalled, non-English, or newly published work. A librarian or second researcher should update it before submission.

**Clinical and human-factors validity:** No clinical reference set, clinician adjudication, user study, explanation comparison, or patient outcome was included. The findings cannot establish safety, utility, alert-fatigue reduction, or benefit.

### 5.11 Required future sequence

The next work should proceed in the following order:

1. revoke and remediate the exposed credential and determine data-exposure status;
2. select a software license and review third-party data obligations;
3. fix multi-ingredient representation, candidate validation, and controlled terminology failure handling;
4. fix output parsing, strict typing, complete consumption, source/severity checks, controlled failure, and unsupported-content review;
5. make source import and displayed evidence fully manifest-driven and versioned;
6. obtain a second-machine independent reproduction;
7. compare deterministic templates and generated prose with pharmacist reviewers under an appropriate ethics determination; and
8. only then consider workflow or clinical-outcome evaluation.

## 6. Conclusion

RxCheck provides a transparent case in which finding authority is assigned to deterministic stored-data logic and optional generated prose is downstream of a persisted finding. That boundary passed repeated synthetic architecture tests, and the local core checker produced correct, repeatable results under bounded workloads. The same evidence cycle found important failures in output validation, data lineage, traceability, and medication normalization. These failures prevent claims of grounded explanation, complete provenance, general accuracy, clinical safety, workflow benefit, or deployment readiness.

The scholarly value of this work is therefore not a new DDI detector or explanation method. It is an incremental design-science instantiation showing both what a finding-authority boundary can enforce and what it cannot. Further progress requires security remediation, technical correction, independent reproduction, and pharmacist evaluation.

## Declarations

### Ethics approval and consent to participate

[AUTHOR TO SUPPLY: institutional determination. No human participants, real patient records, or identifiable health data were used in the reported evaluation.]

### Consent for publication

Not applicable to the synthetic software evaluation, subject to author/institution confirmation.

### Availability of data and materials

The public repository and research branch contain protocols, scripts, frozen fixtures where redistribution is permitted, raw result summaries, logs, hashes, and the evidence index. The recovered DDInter source CSVs are not redistributed in the evidence package and remain subject to DDInter terms [23]. A submission should link an exact remediated tag or archival identifier after the exposed-credential and licensing actions are complete.

### Code availability

Source code is publicly visible at <https://github.com/shubhamjoshipromail-svg/Pharmacy>. Public visibility does not establish reuse rights because [AUTHOR TO CONFIRM: root software license] is unresolved. Do not cite the repository as a safe release until credential/history remediation is complete.

### Competing interests

[AUTHOR TO SUPPLY]

### Funding

[AUTHOR TO SUPPLY]

### Author contributions

[AUTHOR TO SUPPLY using the target journal's CRediT format]

### Acknowledgments

[AUTHOR TO SUPPLY]

### Use of generative AI and AI-assisted tools

[AUTHOR TO SUPPLY according to target-journal policy. The evidence and manuscript revision process used AI-assisted coding, testing, analysis, and drafting; all reported tests were executed and retained, and no result should be attributed to an unexecuted generation.]

## References

1. Saverno KR, Hines LE, Warholak TL, Grizzle AJ, Babits L, Clark C, et al. Ability of pharmacy clinical decision-support software to alert users about clinically important drug-drug interactions. *J Am Med Inform Assoc.* 2011;18(1):32-37. doi:10.1136/jamia.2010.007609.
2. Hussain MI, Reynolds TL, Zheng K. Medication safety alert fatigue may be reduced via interaction design and clinical role tailoring: a systematic review. *J Am Med Inform Assoc.* 2019;26(10):1141-1149. doi:10.1093/jamia/ocz095.
3. Payne TH, Hines LE, Chan RC, Hartman S, Kapusnik-Uner J, Russ AL, et al. Recommendations to improve the usability of drug-drug interaction clinical decision support alerts. *J Am Med Inform Assoc.* 2015;22(6):1243-1250. doi:10.1093/jamia/ocv011.
4. Chou E, Boyce RD, Balkan B, Subbian V, Romero A, Hansten PD, et al. Designing and evaluating contextualized drug-drug interaction algorithms. *JAMIA Open.* 2021;4(1):ooab023. doi:10.1093/jamiaopen/ooab023.
5. Holbrook AM, Matos Silva J, Faruque JAY, Deng J, Schneider T, Jaffer A. Effect of electronic drug-drug interaction alerts on patient and clinician outcomes: a systematic review. *J Am Med Inform Assoc.* 2025;32(10):1617-1628. doi:10.1093/jamia/ocaf139.
6. Nelson SJ, Zeng K, Kilbourne J, Powell T, Moore R. Normalized names for clinical drugs: RxNorm at 6 years. *J Am Med Inform Assoc.* 2011;18(4):441-448. doi:10.1136/amiajnl-2011-000116.
7. Xiong G, Yang Z, Yi J, Wang N, Wang L, Zhu H, et al. DDInter: an online drug-drug interaction database towards improving clinical decision-making and patient safety. *Nucleic Acids Res.* 2022;50(D1):D1200-D1207. doi:10.1093/nar/gkab880.
8. Tian Y, Yi J, Wang N, Wu C, Peng J, Liu S, et al. DDInter 2.0: an enhanced drug interaction resource with expanded data coverage, new interaction types, and improved user interface. *Nucleic Acids Res.* 2025;53(D1):D1356-D1362. doi:10.1093/nar/gkae726.
9. Lewis P, Perez E, Piktus A, Petroni F, Karpukhin V, Goyal N, et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: *Advances in Neural Information Processing Systems 33.* 2020:9459-9474. <https://proceedings.neurips.cc/paper/2020/hash/6b493230-Abstract.html>.
10. Xiong G, Jin Q, Lu Z, Zhang A. Benchmarking retrieval-augmented generation for medicine. In: *Findings of the Association for Computational Linguistics: ACL 2024.* 2024:6233-6251. doi:10.18653/v1/2024.findings-acl.372.
11. Singhal K, Azizi S, Tu T, Mahdavi SS, Wei J, Chung HW, et al. Large language models encode clinical knowledge. *Nature.* 2023;620(7972):172-180. doi:10.1038/s41586-023-06291-2.
12. Sun Z, Li J, Pergola G, He Y. ExDDI: explaining drug-drug interaction predictions with natural language. *Proc AAAI Conf Artif Intell.* 2025;39(24):25228-25236. doi:10.1609/aaai.v39i24.34709.
13. Sre N, Sudhakar S. Hybrid AI-based drug-drug interaction safety decision tool using machine learning, clinical rule-based reasoning, and LLM-assisted explanation. SSRN preprint. Posted April 17, 2026. [accessed 2026 Jul 15]. <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6527819>.
14. Labkoff S, Oladimeji B, Kannry J, Solomonides A, Leftwich R, Koski E, et al. Toward a responsible future: recommendations for AI-enabled clinical decision support. *J Am Med Inform Assoc.* 2024;31(11):2730-2739. doi:10.1093/jamia/ocae209.
15. World Health Organization. *Ethics and Governance of Artificial Intelligence for Health: WHO Guidance.* Geneva: World Health Organization; 2021. [accessed 2026 Jul 15]. <https://www.who.int/publications/i/item/9789240029200>.
16. Health Level Seven International. FHIR Release 4, Resource Provenance. Version 4.0.1. [accessed 2026 Jul 15]. <https://hl7.org/fhir/R4/provenance.html>.
17. Agency for Healthcare Research and Quality. Clinical Decision Support: CDS Connect. [accessed 2026 Jul 15]. <https://digital.ahrq.gov/health-it-tools-and-resources/clinical-decision-support-cds/>.
18. Hevner AR, March ST, Park J, Ram S. Design science in information systems research. *MIS Quarterly.* 2004;28(1):75-105. doi:10.2307/25148625.
19. Peffers K, Tuunanen T, Rothenberger MA, Chatterjee S. A design science research methodology for information systems research. *J Manag Inf Syst.* 2007;24(3):45-77. doi:10.2753/MIS0742-1222240302.
20. Tran VT, Ravaud P. Frugal innovation in medicine for low resource settings. *BMC Med.* 2016;14:102. doi:10.1186/s12916-016-0651-1.
21. World Health Organization. *WHO Guideline: Recommendations on Digital Interventions for Health System Strengthening.* Geneva: World Health Organization; 2019. [accessed 2026 Jul 15]. <https://www.who.int/publications/i/item/9789241550505>.
22. US Food and Drug Administration. *Clinical Decision Support Software: Guidance for Industry and Food and Drug Administration Staff.* January 2026. [accessed 2026 Jul 15]. <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software>.
23. DDInter. Terms: disclaimer and data licensing. [accessed 2026 Jul 15]. <https://ddinter.scbdd.com/terms/>.
