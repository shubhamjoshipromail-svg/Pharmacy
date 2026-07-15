# Revised Article Framing and Outline

## Recommended research framing

**Proposed title**  
*Separating Drug-Interaction Detection From Generative Explanation: Design and Formative Evaluation of the RxCheck Evidence-Bounded Architecture*

**Article type**  
Design-science health-informatics system paper with formative architecture evaluation.

**Central contribution**  
A concrete architecture pattern and prototype in which deterministic, database-backed logic creates drug-interaction findings and an optional LLM is structurally limited to rendering an existing finding, supported by explicit medication non-resolution, source-assertion provenance, condition gating, and persisted review state.

**Primary objective**  
To determine whether the inspected RxCheck prototype enforces a predefined evidence boundary between deterministic finding creation and optional generative explanation under controlled synthetic scenarios.

**Secondary objectives**

1. Describe how the artifact represents uncertain medication identity, evidence provenance, patient-condition context, and longitudinal review state.
2. Identify which architecture properties are verified by the recorded formative evaluation and which clinical, human-factors, operational, and security questions remain open.

**Intended audience**  
Health-informatics researchers, pharmacy-informatics practitioners, clinical decision-support designers, responsible-AI researchers, and software architects developing human-reviewed health applications.

**Key contributions**

1. An evidence-bounded explanation pattern that denies the LLM authority to create interaction findings on the evaluated path.
2. An explicit non-resolution pattern that keeps unmatched medication input visible while excluding it from deterministic checking.
3. A provenance-oriented interaction model separating canonical interactions from source assertions and runtime finding snapshots.
4. Patient-context and longitudinal-review mechanisms: active-condition DDSI gating, acknowledgment suppression with severity resurfacing, and override persistence.
5. A formative architecture evaluation and transparent account of the boundary between verified software behavior and untested clinical claims.

## Detailed outline

### Title page

- Final title.
- [AUTHOR TO SUPPLY: Names, degrees, affiliations, ORCID identifiers, and corresponding-author details.]
- [AUTHOR TO SUPPLY: Word count, table/figure count, and target journal.]

### Structured abstract

**Background**

- Drug-interaction CDS must balance coverage, context, alert burden, and traceability.
- Generative explanation may improve readability but creates unsupported-generation risk if it is allowed to determine findings.

**Objective**

- State one objective: evaluate whether RxCheck enforces the proposed deterministic/generative boundary and associated architecture requirements.

**Methods**

- Design-science artifact at a named commit.
- Static repository inspection plus recorded 26-scenario synthetic formative evaluation.
- Timestamped database profile and three focused tests.
- State that no clinical cases, users, patient outcomes, or generated explanations were evaluated.

**Results**

- Recorded 26/26 scenario result.
- Major verified boundaries: stored-row finding creation, placeholder exclusion, condition gating, persistence, acknowledgment/override behavior, and service independence.
- Timestamped database counts with fixture and coverage caveats.

**Conclusions**

- Architecture feasibility only.
- No clinical performance, usability, explanation factuality, cost, security, or deployment conclusion.

### Keywords

Clinical decision support; drug interactions; pharmacy informatics; large language models; design science; provenance; human oversight; formative evaluation.

## 1. Introduction

### 1.1 Problem

- DDI CDS can miss important interactions and produce high alert burden.
- Medication identity and patient context complicate deterministic lookup.
- Generative systems add a second problem: fluent explanation can be mistaken for evidence.

### 1.2 Gap

- Existing literature supports structured drug terminologies, DDI resources, and responsible AI-CDS evaluation.
- The paper does not claim to invent deterministic CDS or retrieval-grounded generation.
- The narrow gap is an inspectable implementation and evaluation of a boundary that makes generation downstream of a persisted finding.

### 1.3 Objective and questions

- Present the primary and secondary questions exactly as framed above.

### 1.4 Contributions and scope

- List five contributions.
- State early that RxCheck is not for clinical use and the study is preclinical/software-focused.

## 2. Related work and design context

### 2.1 Drug-interaction CDS and alert burden

- Summarize evidence that pharmacy DDI CDS can have variable sensitivity/specificity and alert burden.
- Do not claim RxCheck improves either outcome.

### 2.2 Medication normalization and interaction knowledge sources

- Explain RxNorm’s role as a normalized medication terminology.
- Describe DDInter and DDInter 2.0 as third-party interaction resources.
- Separate source capability from RxCheck’s actual imported release and coverage.

### 2.3 Generative explanation, retrieval context, and clinical risk

- Introduce RAG as a general method, then explain why RxCheck’s implementation is more conservatively described as structured evidence context.
- Cite healthcare LLM limitations and governance/human-oversight guidance.

### 2.4 Design science

- Use Hevner et al. and Peffers et al. to justify artifact construction and formative evaluation.
- Identify problem, objectives, design/development, demonstration, evaluation, and communication.

### 2.5 Positioning table

Suggested columns: approach, finding authority, explanation method, provenance, patient context, evaluation type, and RxCheck distinction.

[AUTHOR TO COMPLETE: Conduct a focused literature search and populate with comparable systems; do not infer novelty from the absence of examples in the current repository.]

## 3. Design-science method

### 3.1 Artifact and unit of analysis

- Artifact: repository commit `6b763c0`.
- Unit of analysis: observable architecture behavior of the prototype.
- Exclusions: clinical accuracy, user performance, patient outcomes, cost-effectiveness, regulatory status.

### 3.2 Design requirements and provenance

Group the nine existing requirements into five higher-level principles:

1. Identity: normalize or explicitly reject.
2. Evidence: findings arise from stored rows and retain source assertions.
3. Context: differentiate DDI/DFI/DDSI and gate DDSI by active condition.
4. Review: preserve run/finding state, acknowledgments, and overrides.
5. Generation: permit explanation only after finding creation and treat external services as optional boundaries.

[AUTHOR TO VERIFY: State which requirements were defined prospectively and which were reconstructed post hoc from the implementation.]

### 3.3 Evaluation strategy

- Explain scenario-based architecture verification.
- Define expected/observed/pass before results.
- Explain synthetic fixture creation, persistent writes, external-service mocks, and lack of teardown.
- State the recorded run timestamp and code/data limitations.

## 4. Artifact architecture

### 4.1 System boundary and user workflow

- React/Vite client, FastAPI service, SQLAlchemy/Postgres persistence.
- Pharmacist-oriented prototype, not authenticated pharmacist workflow.
- Insert rendered overall architecture figure.

### 4.2 Medication identity and explicit non-resolution

- Local alias, RxNorm exact/approximate/NDC, ingredient-resolution attempt.
- Placeholder creation, visibility, and check exclusion.
- Risks: false automatic mapping, network failure, incomplete results.

### 4.3 Interaction and provenance model

- Canonical DDI/DFI/DDSI rows.
- Exactly-one counterpart constraint and pair ordering.
- Source assertion fields and raw payload.
- Limitation: current real importer is DDI-only and nearly all assertions are DDInter.

### 4.4 Deterministic checking and patient-context gating

- Active, non-placeholder medications.
- Canonical pair query, DFI query, condition-gated DDSI query.
- Maximum severity, conflict flag, degree-count hub heuristic.
- Persisted run/finding behavior and early-return exception.

### 4.5 Review-state persistence

- Acknowledgment semantics, expiry, severity resurfacing.
- Override storage and its non-effect on future checks.
- Selected audit events; explicitly not compliance-grade.

### 4.6 Evidence-bounded explanation layer

- Finding-ID precondition.
- Context fields and optional OpenFDA excerpts.
- Anthropic call and custom output checks.
- Persistence of prompt/model metadata and raw response.
- Limitations: first assertion selection, shallow schema checks, unversioned labels, model-reported confidence, prompt injection.

### 4.7 Cost-conscious service separation

- Core check independent from Anthropic/OpenFDA/RxNorm at check time after normalization.
- Present as a design property, not economic evidence.

## 5. Data and implementation context

### 5.1 Interaction source

- Exact DDInter version, date, license, partitions, checksums.
- [AUTHOR TO VERIFY: The current repository does not record these facts.]

### 5.2 Import and transformation

- Alias/preferred-name resolution.
- Canonical pair construction, severity mapping, assertion upsert, quarantine.
- [RESULT REQUIRED: Raw rows, mapped rows, quarantined rows, duplicates, final rows, and fixture-adjusted totals.]

### 5.3 Reproducibility environment

- [AUTHOR TO SUPPLY: OS, Python, package versions/lock hash, Postgres version, migration revision, hardware, environment variables excluding secrets.]
- Identify commit SHA and a safe tagged release/DOI.

## 6. Formative evaluation

### 6.1 Scenario families

- Identity/exclusion.
- Deterministic detection and interaction-type behavior.
- Ranking/provenance.
- Persistence/review state.
- Generative/external-service boundary.

### 6.2 Recorded evaluation procedure

- Real production orchestrator, synthetic database fixtures, expected versus observed results.
- External services mocked to fail in boundary scenarios.
- Explicitly state database contamination and lack of clinical cases.

### 6.3 Additional required evaluation before submission

- [RESULT REQUIRED: Clean rerun in isolated database.]
- [RESULT REQUIRED: Independently specified reference cases or normalization benchmark.]
- [RESULT REQUIRED: Completed explanation-boundary sample if the LLM remains a central contribution.]
- [RESULT REQUIRED: Core latency summary with sample size and environment.]

## 7. Results

### 7.1 Architecture verification

- Report 26/26 as a recorded historical result.
- Prefer counts by scenario family and a supplementary scenario table.
- Avoid interpreting a perfect pass rate as accuracy.

### 7.2 Data profile

- Timestamped counts.
- DDI/DFI/DDSI distribution.
- Assertion-source distribution and fixture caveat.
- Avoid “non-trivial,” “comprehensive,” or “complete.”

### 7.3 Focused automated tests

- Report three recorded tests and exact scope.
- State that tests do not cover most API, import, security, normalization, or LLM paths.

### 7.4 Unexecuted evaluation instruments

- Move the explanation rubric out of results unless completed.
- Mention it as supplementary future protocol only.

## 8. Safety, privacy, governance, and human oversight

- Prototype-only and no real patient data.
- Deterministic finding authority and pharmacist verification requirement.
- Missing authentication, authorization, immutable audit, and production controls.
- [AUTHOR TO REPORT: Credential incident remediation and secret scan.]
- Human oversight is required but not evaluated.
- Regulatory classification is outside the study.

## 9. Discussion

### 9.1 Principal finding

- The artifact enforced selected architecture boundaries under synthetic conditions.

### 9.2 Design implications

- Separate finding authority from language rendering.
- Make unresolved identity visible.
- Preserve provenance and review state.
- Treat external generation as optional and failure-isolated.

### 9.3 Comparison with related approaches

- Compare with rule-based DDI CDS, templated summaries, and retrieval-grounded LLM systems.
- Do not claim superiority without direct evaluation.

### 9.4 What the findings do not establish

- Clinical correctness, complete coverage, user benefit, explanation quality, alert-fatigue reduction, affordability, security, or regulatory readiness.

## 10. Threats to validity and limitations

### Construct validity

- Passing architecture assertions is not clinical safety.
- Model confidence is not calibrated uncertainty.
- Severity conflict is a label difference, not clinical disagreement.

### Internal validity

- Self-authored scenarios and shared configured database.
- Persistent fixtures and incomplete test isolation.

### External validity

- No pharmacists, real workflows, external sites, real patients, or representative normalization inputs.

### Reproducibility validity

- Missing data version, lockfile, populated migration, snapshot, and safe default.

### Technical limitations

- DDI-only real import, sparse DFI/DDSI, shallow LLM checks, external-service failure handling, and security gaps.

## 11. Future work

Use a staged progression:

1. Security/reproducibility remediation.
2. Reference-case and normalization evaluation.
3. Explanation-boundary evaluation.
4. Pharmacist formative usability study.
5. Source expansion and prospective workflow evaluation.
6. Cost and clinical-outcome studies only after earlier stages succeed.

## 12. Conclusion

- One paragraph.
- Restate that the contribution is architecture, not validated clinical performance.
- End with the need for independent clinical, human-factors, and security evaluation before any care use.

## Declarations

### Ethics statement

[AUTHOR TO VERIFY: Institutional determination for synthetic/software-only research and any later expert review.]

### Funding

[AUTHOR TO SUPPLY.]

### Author contributions

[AUTHOR TO SUPPLY using CRediT roles.]

### Conflicts of interest

[AUTHOR TO SUPPLY.]

### Acknowledgments

[AUTHOR TO SUPPLY.]

### Data availability

- Current draft must say that the profiled live database and exact source files are not archived.
- Replace with a DOI-backed synthetic/reproducibility package before submission if licensing permits.

### Code availability

- Cite the public repository, exact commit/tag, software license, and archived DOI after the safe release is created.

## References

- Use numbered Vancouver-style references for the revised manuscript.
- Verify every DOI and access date.
- Cite DDInter data terms separately from the DDInter articles.
