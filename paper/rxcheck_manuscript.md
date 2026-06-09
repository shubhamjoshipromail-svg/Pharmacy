# Architecting Frugal, Evidence-Bound AI for Drug Interaction Review  
## A Design Science Prototype for Budget-Constrained Pharmacy Decision Support

## Abstract

### Background  
Drug interaction review is a high-stakes decision-support problem shaped by medication-name ambiguity, incomplete evidence, patient-specific context, source disagreement, alert fatigue, and workflow accountability. Large language models may improve the usability of clinical decision-support systems by translating structured findings into readable explanations, but they introduce risks when used as sources of clinical claims. These risks are especially important in budget-constrained pharmacy settings, where lower-cost software may be attractive but cannot come at the expense of auditability, evidence discipline, or human oversight.

### Objective  
This paper presents RxCheck, a design science prototype for frugal, evidence-bound drug interaction review. The objective is to investigate how drug interaction decision support can be architected so that deterministic evidence structures produce interaction findings while language models are restricted to explaining already-persisted findings.

### Methods  
RxCheck was implemented as a Postgres-backed FastAPI and React prototype for pharmacist-facing drug interaction review. The system includes RxNorm-based medication normalization, exact and fuzzy lookup paths, NDC lookup, alias learning, unresolved placeholder drugs, DDInter-derived interaction records, source assertions, canonical drug-pair representation, drug-drug, drug-food, and drug-disease interaction support, condition-gated DDSI logic, severity ranking, conflict detection, review and override workflows, check-run and finding snapshots, audit-oriented persistence, OpenFDA-assisted context retrieval, and an Anthropic-powered explanation endpoint. The prototype was evaluated using a design science approach through a 26-scenario formative architecture evaluation, database profiling, failure-mode analysis, cost-conscious deployment analysis, automated tests, and an LLM explanation-quality rubric.

### Results  
The profiled database contained 152,416 interaction records and 172,714 source assertions. The formative evaluation passed 26 of 26 architecture scenarios without calling paid external APIs. The scenarios tested deterministic interaction detection, canonical pair ordering, duplicate and inactive medication handling, unresolved placeholder exclusion, drug-disease condition gating, drug-food interaction behavior, severity ranking, source-severity conflict detection, source assertion preservation, check-run and finding persistence, acknowledgment suppression, acknowledgment severity escalation behavior, override persistence, and separation between deterministic findings and language-model explanation. The evaluation provides formative architecture evidence but does not establish clinical accuracy, FDA clearance, HIPAA compliance, cost-effectiveness, or complete drug interaction coverage.

### Conclusions  
RxCheck demonstrates an evidence-bound architecture for AI-augmented pharmacy decision support. Its contribution is not an autonomous clinical reasoning model, but a structured decision-support pattern: normalize uncertain inputs, explicitly represent unresolved cases, determine findings through deterministic evidence, preserve source provenance, gate patient-context alerts, reduce alert burden through review-state design, persist user decisions, and restrict language models to explanation over existing findings. This pattern may be relevant to budget-constrained pharmacy settings seeking auditable and lower-cost decision-support infrastructure. Further work is required before clinical deployment, including stronger security controls, broader source coverage, expert review, pharmacist usability evaluation, explanation-quality scoring, and formal clinical validation.

---

# 1. Introduction

Drug interaction review is a recurring and complex problem in pharmacy decision support. Patients often receive multiple medications from different providers and across different care settings, creating opportunities for drug-drug, drug-food, and drug-disease interactions. A useful decision-support system must do more than detect possible interactions. It must resolve medication-name ambiguity, preserve evidence provenance, account for patient-specific conditions, prioritize alerts, support professional review, and maintain an auditable record of what was shown and how users responded.

Large language models have created new possibilities for clinical software interfaces. They can summarize complex evidence, explain technical terminology, and generate readable text for professional review. However, their fluency creates risk when they are treated as clinical knowledge sources. A model that directly answers whether two drugs interact may produce unsupported claims, omit uncertainty, generate inappropriate management advice, or provide inconsistent severity labels. In high-stakes decision support, the central design problem is therefore not simply whether a language model can produce a useful explanation. The more important question is how the software architecture constrains the model’s role.

This paper introduces RxCheck as a prototype of evidence-bound AI for pharmacy decision support. Evidence-bound AI refers to a system pattern in which structured evidence and deterministic logic produce the underlying decision-support finding, while a language model is restricted to explaining retrieved evidence and cannot create the clinical claim itself. In RxCheck, the database determines whether an interaction exists. The language model may explain an already-persisted finding, but it is not used to create a finding, change the stored severity, or replace the structured result.

The project is also motivated by frugal and budget-constrained healthcare design. Enterprise clinical decision-support systems can be expensive, difficult to adapt, or tightly integrated into larger institutional infrastructures. Smaller pharmacies, teaching environments, rural clinics, public-sector facilities, and resource-constrained health systems may need lower-cost software patterns. Yet lower cost cannot justify weaker safety boundaries. Frugal clinical AI should therefore be designed around explicit constraints: transparent evidence, graceful non-resolution, auditable workflows, optional enrichment services, and human oversight.

RxCheck addresses this design space as a Postgres-backed, pharmacist-facing prototype. Its architecture includes medication normalization through RxNorm-based lookup, exact and fuzzy matching, NDC lookup, local alias learning, unresolved placeholder handling, deterministic interaction checking over imported records, provenance-preserving source assertions, condition-gated drug-disease interaction logic, alert-burden controls, review and override persistence, and bounded language-model explanation. The contribution is not a claim that RxCheck is clinically validated or ready for deployment. Instead, the paper evaluates whether the artifact enforces its intended architecture boundaries.

The guiding research question is:

How can drug interaction decision support be architected as a frugal, evidence-bound AI system that preserves deterministic evidence, auditability, rejection of unresolved inputs, alert-burden controls, and human oversight while enabling language-model explanations?

This paper makes five contributions. First, it defines evidence-bound AI as an architecture pattern for separating clinical evidence from language generation. Second, it presents RxCheck, a design science prototype for drug interaction review. Third, it describes the system’s architecture across normalization, deterministic checking, provenance modeling, alert-fatigue workflow, audit persistence, and LLM explanation boundaries. Fourth, it evaluates the prototype through 26 architecture scenarios, database profiling, failure-mode analysis, cost-conscious design analysis, and an explanation-quality rubric. Fifth, it derives design implications for frugal AI decision-support systems intended for budget-constrained pharmacy settings.

---

# 2. Background and Related Work

## 2.1 Drug Interaction Decision Support  
Drug interaction decision support is not simply a lookup problem. A practical system must determine whether medications are represented consistently, whether an interaction source supports the finding, whether the patient context makes the finding relevant, and whether the alert can be reviewed without overwhelming the user. Existing clinical decision-support systems can help identify risks, but they also face known challenges around alert fatigue, override behavior, source disagreement, and workflow integration.

## 2.2 Medication Normalization and Ambiguity  
Medication names may appear as brand names, generic names, misspellings, abbreviations, NDC identifiers, or local aliases. Without normalization, systems may miss interactions or create duplicate records. RxCheck treats normalization as a safety-relevant architecture layer rather than a convenience feature. The system attempts local alias lookup, exact RxNorm lookup, fuzzy lookup, NDC lookup, and ingredient-level resolution where possible. If resolution fails, the input is not silently treated as a valid medication. It becomes an unresolved placeholder visible to the user but excluded from deterministic checking.

## 2.3 Alert Fatigue and Review Burden  
A decision-support system that maximizes alert volume may reduce usability and encourage overrides. Alert fatigue is therefore an architecture concern, not only a user-interface concern. RxCheck addresses this through severity grouping, suppression of previously acknowledged findings, severity escalation behavior, duplicate prevention, condition-gated drug-disease alerts, and review/override workflows. These mechanisms do not prove reduced alert fatigue, but they represent design decisions intended to reduce unnecessary or repetitive burden.

## 2.4 LLMs and Clinical Explanation  
Language models may improve readability and help users interpret structured findings. However, if the model is allowed to determine interaction existence or severity, it can introduce unsupported clinical claims. RxCheck uses an explanation-only architecture. The language model receives structured findings and optional OpenFDA context after the deterministic system has already produced and persisted a finding. The model’s output is parsed into expected fields, associated with prompt/model metadata, and subject to drug-reference checks.

## 2.5 Frugal Clinical AI and Budget-Constrained Settings  
Budget-constrained healthcare settings require software designs that are not merely cheaper, but maintainable, auditable, and safe under infrastructure constraints. RxCheck’s design separates core interaction checking from optional enrichment services. Anthropic is not required for core checking. OpenFDA is not required for core checking. RxNorm is not required at check time after medications have already been normalized. This supports a cost-conscious architecture, while stopping short of any claim of formal cost-effectiveness.

## 2.6 Design Science Framing  
This study is positioned as design science research. The artifact is RxCheck. The evaluation asks whether the artifact satisfies its intended design requirements under controlled synthetic scenarios. The paper does not claim clinical effectiveness, regulatory clearance, or production readiness. Instead, it evaluates the architecture as a prototype system for evidence-bound decision support.

---

# 3. Design Requirements

The architecture was shaped by nine design requirements.

## Requirement 1: Resolve medication ambiguity before checking  
Drug interaction review depends on consistent medication representation. RxCheck uses RxNorm-based normalization, exact lookup, fuzzy lookup, NDC lookup, and alias learning to map entered medications to normalized concepts where possible.

## Requirement 2: Represent uncertainty explicitly rather than guessing  
A system should not silently treat an unresolved medication as clinically resolved. RxCheck records unresolved entries as placeholder drugs. These placeholders remain visible in the UI but are excluded from interaction checking.

## Requirement 3: Determine interaction existence through deterministic evidence  
The system should not ask an LLM whether an interaction exists. RxCheck determines interactions through stored Postgres records and deterministic orchestration logic.

## Requirement 4: Preserve provenance and source disagreement  
Interaction evidence may come from source-specific records with differing severity labels or payloads. RxCheck separates canonical interaction records from source assertions, preserving source record identifiers, raw payloads, severity labels, and conflict indicators.

## Requirement 5: Gate patient-context-specific alerts  
Drug-disease interactions should not be shown merely because they exist in a database. RxCheck surfaces DDSI findings only when the patient has the relevant active condition.

## Requirement 6: Reduce alert burden without hiding evidence  
Review workflows should reduce repeated burden while preserving auditability. RxCheck supports severity grouping, acknowledgment suppression, escalation behavior, duplicate prevention, and override persistence.

## Requirement 7: Persist check state and user decisions  
A pharmacist-facing decision-support tool should retain what was checked, what was found, and how users responded. RxCheck stores check runs, finding snapshots, acknowledgments, overrides, audit events, and LLM explanation records.

## Requirement 8: Bound language generation to explanation  
The LLM should explain existing findings, not create them. RxCheck’s explanation endpoint requires an existing persisted finding and uses structured interaction context and optional label excerpts.

## Requirement 9: Separate core checking from optional paid/enrichment services  
Cost-conscious systems should avoid making paid or external AI services necessary for core safety functions. RxCheck can perform core checking without Anthropic, OpenFDA, or RxNorm at check time once stored data and normalized medications exist.

---

# 4. Artifact Architecture: RxCheck

## 4.1 Full-Stack Architecture  
RxCheck is implemented as a modular monolith using FastAPI, React, and Postgres. The backend exposes patient, medication, condition, interaction-checking, review, override, audit, and explanation endpoints. The React frontend supports patient selection, medication and condition management, interaction review, AI explanation display, review status, and override actions. The deployed architecture serves the frontend and backend from the same application.

## 4.2 Medication Normalization and Non-Resolution  
Medication normalization is handled before interaction checking. The normalization service first checks local aliases, then attempts exact RxNorm lookup, fuzzy lookup, and NDC lookup. Resolved medications are linked to normalized drug records and aliases may be learned back into the database. If resolution fails, the system creates an unresolved placeholder rather than silently guessing. Placeholder medications are shown as unverified but excluded from interaction pair generation.

This design is important because it converts ambiguity into an explicit system state. The system does not claim to know what a medication is when normalization fails.

## 4.3 Postgres Evidence Model  
The database is not merely storage; it is part of the decision-support architecture. RxCheck uses Postgres-specific structures such as UUIDs, JSONB, arrays, constraints, and indexes. The schema groups records into drug normalization tables, interaction evidence tables, patient workflow tables, check snapshot tables, explanation tables, and audit/review tables.

Canonical interaction records are separated from source-specific assertions. This allows the system to represent a normalized interaction while preserving source IDs, raw payloads, source severity labels, and severity disagreement. Canonical DDI pair ordering prevents the same pair from appearing as two different records when drug order is reversed.

## 4.4 Deterministic Interaction Orchestration  
The orchestrator loads active, non-placeholder medications and active patient conditions. It generates canonical medication pairs for DDI checking, queries stored interaction records, applies patient-condition filtering for DDSI findings, and returns severity-ranked results. OpenFDA and the LLM are not used to determine whether an interaction exists.

The system supports DDI, DFI, and DDSI representation, although current profiled database coverage is predominantly DDI. The architecture supports DFI and DDSI logic, but broader DFI/DDSI source ingestion remains future work.

## 4.5 Alert Fatigue and Review Workflow  
RxCheck includes several alert-burden design decisions. Findings are grouped by severity. Duplicate records are reduced through canonical pair constraints and unique indexes. DDSI findings are gated by active patient conditions. Acknowledged interactions can be suppressed rather than deleted, preserving visibility and review history. A lower-severity acknowledgment cannot suppress a higher-severity current finding. Overrides are persisted as user decisions but do not automatically suppress future checks.

These mechanisms do not prove reduced alert fatigue, but they show that alert burden was treated as a system design problem.

## 4.6 Audit-Oriented Persistence  
The system persists interaction check runs, finding snapshots, acknowledgments, overrides, audit events, and LLM explanations. Check runs preserve medication snapshots and finding records. Findings can be linked to explanation records. Prompt and model metadata support later inspection of generated explanations.

This persistence is audit-oriented, not compliance-grade. RxCheck does not currently implement authentication, role-based access control, immutable audit logs, HIPAA controls, or production access monitoring.

## 4.7 Bounded LLM Explanation Layer  
The LLM layer is downstream of deterministic checking. A user can request an explanation only for an existing finding. The explanation context includes structured interaction details, source assertions, and optional OpenFDA label excerpts. The model is instructed not to invent unsupported claims, not to provide prescribing decisions, and not to change the stored severity.

Generated outputs are parsed into expected fields such as summary, mechanism, clinical effect, management, severity rationale, sources used, and confidence. Failed parsing or validation can be stored. Drug-reference checks identify whether the explanation mentions drugs outside the structured finding. The LLM’s confidence is model-reported explanation confidence, not clinical certainty.

## 4.8 Frugal Deployment and Service Separation  
RxCheck is cost-conscious by architecture rather than by proven cost-effectiveness. The core interaction check depends on stored Postgres records and patient data. Anthropic is optional for explanations. OpenFDA provides optional explanation context. RxNorm is needed for new normalization but not for checking already-normalized medications. This separation is relevant for budget-constrained pharmacy settings because core safety behavior does not depend on a paid LLM call.

---

# 5. Evaluation Methods

The evaluation was formative and architecture-focused. It did not test clinical accuracy, patient outcomes, pharmacist usability, regulatory compliance, or complete interaction coverage.

The evaluation consisted of five components:

1. A 26-scenario synthetic architecture evaluation.
2. Database profiling.
3. Focused automated tests.
4. Failure-mode analysis.
5. LLM explanation-quality rubric.

The 26-scenario evaluation tested whether the implemented artifact satisfied its intended design boundaries. Scenarios covered deterministic DDI detection, canonical pair ordering, duplicate and inactive medication handling, unresolved placeholder exclusion, missing interaction behavior, DDSI condition gating, DFI behavior, severity ranking, source conflict detection, source assertion preservation, check-run and finding persistence, acknowledgment suppression, severity escalation after acknowledgment, override persistence, explanation endpoint boundaries, and independence of core checking from Anthropic, OpenFDA, and RxNorm at check time.

---

# 6. Results

## 6.1 Database Profile  
The profiled database contained 152,416 interaction records and 172,714 source assertions. The profile included 1,967 drugs, 1,934 aliases, and 71 unresolved drug entries. The interaction records were predominantly DDI rows, with limited DFI and DDSI rows in the current configured database. This profile demonstrates a non-trivial structured artifact but does not establish clinical coverage or completeness.

## 6.2 Formative Architecture Evaluation  
All 26 synthetic architecture scenarios passed. The evaluation did not call paid external APIs. The results support the claim that RxCheck enforces key architecture boundaries under controlled fixtures.

The strongest findings were:

- Deterministic interaction findings were produced from stored database rows.
- Canonical pair ordering prevented drug-order duplication.
- Inactive medications and unresolved placeholders were excluded from checking.
- Missing database interactions did not become generated findings.
- DDSI findings appeared only when the matching patient condition was active.
- Acknowledgment suppressed findings without deleting them.
- Severity escalation logic prevented stale lower-severity acknowledgments from suppressing higher-severity findings.
- Overrides were persisted but did not alter future deterministic checks.
- Findings existed before LLM explanations.
- The explanation endpoint required an existing finding.
- Core checking did not require Anthropic, OpenFDA, or RxNorm at check time.

## 6.3 Automated Tests  
Focused pytest checks passed, covering health endpoint behavior and selected interaction-summary logic such as severity selection, conflict flags, DDI summary fields, hub scores, and DDSI condition naming. These tests provide limited support for implementation behavior but do not replace broader test coverage.

## 6.4 Failure-Mode Analysis  
The failure-mode analysis identified residual risks. RxNorm failure creates visible unresolved placeholders but can result in missed checks. Missing database interactions remain undetected. OpenFDA failures can reduce explanation context. Prompt-injection defenses remain limited. No authentication or authorization is implemented. Database availability remains a hard dependency. These limitations define the boundary between prototype architecture evidence and clinical deployment readiness.

## 6.5 Explanation-Quality Rubric  
The project defines a rubric for evaluating generated explanations on schema validity, drug-name consistency, severity preservation, absence of new interaction claims, absence of unsupported dosing or prescribing instructions, evidence grounding, uncertainty, readability, source use, and prompt-injection risk. The rubric is an evaluation instrument and does not by itself establish clinical correctness.

---

# 7. Discussion

RxCheck demonstrates that LLM-augmented clinical decision support can be designed around evidence boundaries rather than model capability alone. The key architectural move is to prevent the language model from becoming the source of interaction existence. However, the broader contribution is larger than the LLM boundary. RxCheck combines normalization, explicit non-resolution, deterministic evidence modeling, provenance preservation, patient-context gating, alert-burden workflow, audit-oriented persistence, and bounded explanation into a single decision-support artifact.

## 7.1 Evidence-Bound AI as a Design Pattern  
Evidence-bound AI treats language generation as a presentation and explanation layer over structured findings. This is different from asking an LLM to reason directly over a patient’s medication list. The model may improve explanation quality, but it cannot create the interaction record. In high-stakes decision support, this separation reduces a class of hallucination-related risk by design.

## 7.2 The Importance of Rejection and Non-Resolution  
A major design principle in RxCheck is that the system can refuse to resolve uncertain inputs. Unresolved medications become placeholders, remain visible, and are excluded from checking. This is important because false certainty can be more dangerous than visible uncertainty. A frugal clinical AI system should not be pressured to answer every question when the evidence is insufficient.

## 7.3 Provenance and Source Disagreement  
RxCheck separates canonical interaction entities from source assertions. This design supports source provenance, raw payload preservation, severity conflict detection, and future multi-source expansion. In decision-support systems, representing disagreement may be more useful than flattening all evidence into a single confidence-free label.

## 7.4 Alert Fatigue as Architecture  
Alert fatigue is often treated as an interface issue, but RxCheck treats it as an architecture issue. Condition-gated DDSI logic, severity grouping, acknowledgment suppression, escalation behavior, duplicate prevention, and persistent review state all affect how alerts are surfaced and revisited. These mechanisms require future pharmacist evaluation, but they show that alert burden can be addressed below the surface-level UI.

## 7.5 Frugal Clinical AI  
The frugal design contribution is not that RxCheck proves lower cost or replaces enterprise systems. Rather, it shows how core checking can be separated from optional services. A budget-constrained pharmacy environment could prioritize deterministic database-backed checking and add LLM explanation only when feasible. This design may be relevant to settings where enterprise clinical decision-support infrastructure is inaccessible, but further deployment, cost, and usability studies are required.

---

# 8. Limitations

This study has several important limitations. First, the evaluation uses synthetic architecture scenarios rather than clinical cases reviewed by pharmacists. Second, RxCheck has not been validated against a clinical gold standard and does not establish sensitivity, specificity, or patient-safety impact. Third, the current database profile is not a completeness claim. The configured database is predominantly DDI and has limited DFI/DDSI coverage. Fourth, the system does not implement authentication, authorization, HIPAA compliance controls, immutable audit logs, or production-grade security. Fifth, the LLM explanation layer has limited prompt-injection defenses and no completed expert-scored explanation evaluation. Sixth, RxNorm, OpenFDA, Anthropic, and Postgres availability remain infrastructure dependencies in different parts of the workflow. Seventh, no pharmacist usability study has been conducted.

---

# 9. Future Work

Future work should proceed in four directions.

First, technical hardening is needed: authentication, role-based access control, secret management, stronger CORS configuration, expanded test coverage, immutable audit trails, source versioning, and better external-service failure handling.

Second, data and clinical validation should be expanded: broader source ingestion, DFI/DDSI import expansion, source coverage analysis, unresolved-normalization review, gold-standard comparison, and expert review of interaction prioritization.

Third, LLM evaluation should be completed: explanations should be scored with the proposed rubric, adversarial prompt-injection tests should be added, citation grounding should be strengthened, and model-reported confidence should be clearly separated from clinical confidence.

Fourth, deployment and humanitarian relevance should be studied: self-hosting guides, low-bandwidth modes, offline-capable data mirrors, multilingual support, cost modeling, and small usability studies in budget-constrained pharmacy environments.

---

# 10. Conclusion

RxCheck demonstrates a frugal, evidence-bound architecture for AI-augmented drug interaction review. The system’s contribution is not autonomous clinical reasoning, but the careful separation of uncertain input handling, deterministic evidence, source provenance, patient-context filtering, alert-burden workflow, audit-oriented persistence, and bounded language-model explanation. A 26-scenario formative architecture evaluation supports the prototype’s internal design boundaries, while database profiling and failure-mode analysis clarify its current scope. Further work is required before clinical deployment, but the prototype provides a concrete design pattern for responsible AI decision support in budget-constrained pharmacy settings.
