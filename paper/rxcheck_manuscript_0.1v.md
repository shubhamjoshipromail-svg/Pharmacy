# Architecting Frugal, Evidence-Bound AI for Drug Interaction Review  
## A Design Science Prototype for Budget-Constrained Pharmacy Decision Support

## Abstract

Drug interaction review is a complex decision-support problem involving medication-name ambiguity, incomplete source coverage, patient-specific context, source disagreement, alert burden, and workflow accountability. Large language models may improve the usability of decision-support systems by generating readable explanations, but they introduce risks when used as sources of clinical claims. This paper presents RxCheck, a design science prototype for frugal, evidence-bound drug interaction review. RxCheck is implemented as a Postgres-backed FastAPI and React system that combines RxNorm-oriented medication normalization, unresolved placeholder handling, DDInter-derived interaction records, deterministic interaction orchestration, provenance-preserving source assertions, condition-gated drug-disease interaction logic, review and override workflows, audit-oriented persistence, OpenFDA-assisted explanation context, and a bounded LLM explanation endpoint.

The central design principle is evidence-bound AI: structured evidence and deterministic logic produce the underlying interaction finding, while the language model is restricted to explaining an already-persisted finding. The prototype was evaluated using a 26-scenario formative architecture evaluation, database profiling, failure-mode analysis, automated tests, cost-conscious deployment analysis, and an LLM explanation-quality rubric. The evaluation passed 26 of 26 synthetic scenarios and called no paid or free external APIs during core architecture testing. The profiled database contained 152,416 interaction records and 172,714 source assertions, with interaction coverage predominantly concentrated in drug-drug interactions.

The evaluation supports RxCheck as a working architecture prototype rather than a clinically validated system. The results show that the current artifact enforces selected architecture boundaries under synthetic conditions, including deterministic database-backed checking, placeholder exclusion, condition-gated DDSI behavior, source assertion preservation, acknowledgment suppression, override persistence, and separation of core checking from optional explanation/enrichment services. The study does not establish clinical accuracy, pharmacist usability, alert-fatigue reduction, cost-effectiveness, HIPAA compliance, FDA readiness, or complete interaction coverage. RxCheck contributes a concrete design pattern for safety-oriented, cost-conscious AI decision support: normalize or explicitly reject uncertain inputs, preserve evidence provenance, persist review decisions, and restrict LLMs to explanation over existing findings.

---

# 1. Introduction

Drug interaction review is a recurring problem in pharmacy decision support. Patients may receive multiple medications across providers, care settings, and time periods, creating opportunities for drug-drug, drug-food, and drug-disease interactions. However, useful interaction review is not merely a lookup problem. A decision-support system must also handle ambiguous medication names, inconsistent identifiers, incomplete source coverage, patient-specific context, source disagreement, repeated alerts, user review behavior, and accountability for what was shown to the clinician or pharmacist. [CITE: DDI/CDS overview]

Large language models create new possibilities for this kind of software. They can summarize technical findings, translate mechanism and management information into readable explanations, and improve the usability of dense clinical evidence. At the same time, they are risky when used as sources of clinical truth. A model that is allowed to directly answer whether two drugs interact may generate unsupported claims, omit uncertainty, provide inconsistent severity labels, or produce fluent explanations that are not grounded in structured evidence. [CITE: LLM healthcare hallucination/risk]

This paper argues that the key problem is not whether language models can produce readable explanations. The more important design question is: what should the language model be allowed to do inside a high-stakes decision-support system? RxCheck answers this by using an evidence-bound architecture. In an evidence-bound system, deterministic evidence structures produce the underlying finding, while language models are restricted to explaining that finding. In RxCheck, the database and interaction orchestrator determine whether an interaction exists. The LLM can explain an existing persisted finding, but it cannot create a new interaction, change stored severity, or replace the structured evidence layer.

This architecture is especially relevant for budget-constrained pharmacy environments. Enterprise clinical decision-support systems may be expensive, difficult to adapt, or embedded within larger health information infrastructures. Smaller pharmacies, teaching environments, rural clinics, public-sector settings, and resource-constrained healthcare environments may need systems that are lower-cost and easier to inspect. However, cost pressure cannot justify weaker safety boundaries. A frugal clinical AI system should be inexpensive in a careful way: core safety behavior should rely on inspectable structured data, optional enrichment services should be separable, uncertainty should remain visible, and human review should be preserved. [CITE: frugal/resource-constrained digital health]

RxCheck was built to explore this design space. The prototype is a pharmacist-facing drug interaction review system implemented with FastAPI, React, and Postgres. It supports medication normalization, patient medication and condition tracking, deterministic interaction checking, source assertion preservation, severity ranking, condition-gated drug-disease interaction logic, review acknowledgment, override persistence, audit-oriented snapshots, OpenFDA-assisted explanation context, and LLM-generated explanations over existing findings. The system is not presented as clinically validated or production-ready. Instead, it is evaluated as a design science artifact: a working prototype used to study whether a specific architecture pattern can be implemented and tested. [CITE: design science]

The research question guiding this paper is:

How can drug interaction decision support be architected as a frugal, evidence-bound AI system that preserves deterministic evidence, explicit non-resolution, source provenance, patient-context filtering, alert-burden workflow, audit-oriented persistence, and bounded LLM explanation?

This paper makes five contributions. First, it defines evidence-bound AI as an architecture pattern for separating deterministic clinical evidence from language-model explanation. Second, it presents RxCheck, a Postgres-backed pharmacist-facing prototype for drug interaction review. Third, it describes the system architecture across normalization, rejection/non-resolution, deterministic interaction checking, provenance modeling, patient-context filtering, alert-burden workflow, audit persistence, and LLM explanation boundaries. Fourth, it evaluates the artifact through a 26-scenario formative architecture evaluation, database profiling, automated tests, failure-mode analysis, cost-conscious deployment analysis, and an explanation-quality rubric. Fifth, it identifies what this architecture does and does not prove, distinguishing prototype architecture evidence from clinical validation.

---

# 2. Background and Related Work

## 2.1 Drug interaction decision support

Drug interaction decision-support systems aim to help identify potential risks arising from combinations of medications, foods, and disease conditions. In practice, these systems must balance sensitivity with usability. Excessive, poorly prioritized, or context-insensitive alerts can contribute to alert fatigue and high override rates. For pharmacy workflows, a useful system must not only detect potential interactions but also support review, prioritization, explanation, and accountability. [CITE: DDI/CDS] [CITE: alert fatigue]

## 2.2 Medication normalization and ambiguity

Medication entries may appear as brand names, generic names, misspellings, abbreviations, local aliases, or structured identifiers such as NDCs. If the system cannot normalize these inputs, interaction checking may miss relevant pairs or create duplicate records. RxNorm provides normalized names for clinical drugs and links names across drug vocabularies, making it a useful normalization layer for medication-related software. [CITE: RxNorm/NLM]

RxCheck treats medication normalization as a safety-relevant architecture layer. The system includes local alias lookup, exact lookup, fuzzy lookup, NDC lookup, ingredient-oriented resolution where possible, and alias persistence. When a medication cannot be resolved, RxCheck creates an unresolved placeholder rather than silently guessing. This allows uncertainty to remain visible while preventing unresolved records from being treated as verified medications during deterministic checking.

## 2.3 Interaction evidence sources and provenance

Drug interaction databases may differ in source coverage, severity labels, management recommendations, and evidence representation. DDInter is an open drug-drug interaction database that provides structured interaction records and associated information such as severity, mechanism, management, and source evidence. [CITE: DDInter] DDInter 2.0 further expands the representation of drug-drug, drug-food, drug-disease, and therapeutic duplication information. [CITE: DDInter 2.0]

RxCheck uses DDInter-derived records as its structured evidence base, but it does not treat imported data as complete clinical truth. Instead, the schema separates canonical interaction records from source-specific assertions. This design allows the system to preserve source record identifiers, raw payloads, source-specific severity labels, import metadata, and severity disagreement. The paper therefore frames RxCheck as provenance-oriented rather than clinically complete.

## 2.4 Alert fatigue and review workflow

Alert fatigue is a known challenge in clinical decision support. If alerts are repetitive, low relevance, or poorly prioritized, users may override or ignore them. [CITE: alert fatigue/override literature] RxCheck does not claim to reduce alert fatigue in practice because no pharmacist user study has been conducted. However, the architecture includes alert-burden-aware mechanisms: severity ranking, severity grouping, duplicate prevention, condition-gated DDSI behavior, acknowledgment suppression, severity escalation behavior, override persistence, and reviewed-state separation.

These features are evaluated as workflow logic, not as real-world usability outcomes. The safe claim is that RxCheck implements mechanisms intended to manage alert burden. Whether these mechanisms improve pharmacist workflow remains future work.

## 2.5 LLMs, grounded generation, and clinical risk

Language models can make clinical information easier to read, but they may also hallucinate, produce unsupported recommendations, or overstate certainty. Retrieval-augmented generation and structured prompting can improve grounding, but they do not eliminate all risk. [CITE: LLM healthcare risk] [CITE: RAG/grounding] RxCheck responds to this problem by restricting the LLM to explanation over existing persisted findings. The model is downstream of deterministic checking and receives structured context rather than open-ended authority to determine interaction existence.

## 2.6 Frugal and resource-constrained digital health

Resource-constrained healthcare settings may benefit from lower-cost, adaptable digital tools, but responsible design requires more than cost reduction. Systems must also preserve transparency, maintainability, auditability, and human oversight. [CITE: frugal digital health] RxCheck’s architecture separates core deterministic checking from optional enrichment and explanation services. Anthropic is not required for core checking. OpenFDA is not required for core checking. RxNorm is not required at check time after medications have already been normalized and stored. This design supports cost-conscious analysis, while not proving cost-effectiveness.

## 2.7 Design science research

This study is positioned as design science research. The artifact is RxCheck, and the evaluation asks whether the artifact satisfies selected design requirements under controlled synthetic scenarios. The paper does not claim clinical effectiveness or regulatory readiness. Instead, it evaluates architecture behavior, failure modes, and design implications. [CITE: Hevner design science] [CITE: Peffers design science]

---

# 3. Design Requirements

RxCheck was designed around nine requirements.

| Requirement | Design problem | RxCheck implementation | Evaluation evidence | Limitation |
|---|---|---|---|---|
| Medication normalization | Medication names are ambiguous | RxNorm-oriented normalization, exact/fuzzy/NDC lookup, aliases | Architecture inventory; normalization code | Real-world normalization accuracy not benchmarked |
| Explicit non-resolution | Uncertain drugs should not be silently guessed | Unresolved placeholder drugs | Placeholder scenarios passed | Does not solve all normalization failures |
| Deterministic interaction evidence | LLMs should not create findings | Postgres interaction records and deterministic orchestrator | Stored DDI/missing interaction scenarios passed | Missing database rows remain missed risks |
| Provenance preservation | Sources may disagree | Source assertions, raw payloads, conflict flags | Source preservation/conflict scenarios passed | Does not adjudicate correct source |
| Patient-context filtering | DDSI depends on patient condition | Active-condition-gated DDSI | DDSI absent/present/resolved scenarios passed | Current DDSI database coverage is limited |
| Alert-burden workflow | Repeated alerts can overwhelm users | Severity grouping, acknowledgment suppression, escalation, overrides | Acknowledgment/override scenarios passed | No pharmacist user study |
| Audit-oriented persistence | Review actions should be inspectable | Check runs, finding snapshots, acknowledgments, overrides, audit events | Persistence scenarios passed | Not compliance-grade audit logging |
| Bounded LLM explanation | LLM should explain, not decide | Explanation endpoint requires existing finding | LLM boundary scenario passed | Explanation factuality not clinically scored |
| Cost-conscious separation | Core checks should not depend on paid APIs | Anthropic/OpenFDA/RxNorm not required for core checking | External-service boundary scenarios passed | Not proven cost-effective or fully offline |

---

# 4. System Architecture

## 4.1 Full-stack structure

RxCheck is implemented as a modular full-stack prototype. The backend uses FastAPI and SQLAlchemy with a Postgres database. The frontend is built with React and Vite and is served through the FastAPI application in production when a frontend build is available. The system includes endpoints for patients, medications, conditions, interaction checks, review actions, overrides, audit events, and LLM explanations.

The architecture is intentionally centered on the database and orchestrator rather than on the LLM. Patient medications and conditions are stored as structured records. Interaction evidence is stored in normalized tables. The orchestrator performs deterministic checking. The LLM explanation layer is optional and downstream.

## 4.2 Medication normalization layer

Medication normalization is handled before checking. RxCheck attempts to resolve user-provided medication input through local aliases, exact lookup, fuzzy lookup, NDC lookup, and RxNorm-oriented concept mapping. When resolution succeeds, the medication is linked to a normalized drug record. When resolution fails, RxCheck records an unresolved placeholder drug.

The placeholder pattern is important because it creates an explicit non-resolution state. The system does not silently treat unresolved text as a verified medication. The unresolved medication remains visible for human review but is excluded from deterministic interaction checking. This design favors visible uncertainty over false confidence.

## 4.3 Evidence data model

The Postgres schema is part of the decision-support architecture. It includes drug normalization tables, interaction evidence tables, patient workflow tables, check-run and finding snapshot tables, LLM explanation records, review/override tables, and audit events.

The interaction model separates canonical interaction records from source-specific assertions. Canonical interactions represent normalized DDI, DFI, or DDSI entities. Source assertions preserve source-specific severity labels, source identifiers, raw payloads, and provenance metadata. This allows the system to detect and represent severity conflicts across sources without flattening all evidence into a single unexplained label.

For DDI records, canonical pair ordering ensures that Drug A + Drug B and Drug B + Drug A resolve to the same representation. Database constraints and indexes support consistency and reproducible lookup.

## 4.4 Deterministic interaction orchestrator

The interaction orchestrator loads active, non-placeholder medications and active patient conditions. It generates canonical drug pairs for DDI checking, queries stored interaction records, applies condition gating for DDSI findings, includes DFI findings where available, ranks findings by severity and other summary features, and persists check-run and finding snapshots.

The orchestrator does not call Anthropic to decide whether an interaction exists. It does not use OpenFDA to create findings. It does not require RxNorm during checking once medications are already normalized. This is the core of the evidence-bound architecture.

## 4.5 DDI, DFI, and DDSI support

RxCheck’s schema supports drug-drug, drug-food, and drug-disease interaction types. The current profiled database is predominantly DDI, with limited DFI and DDSI rows. Therefore, the paper distinguishes between architecture support and imported source coverage. The evaluation tests that the orchestrator handles these types correctly under synthetic fixtures, but it does not prove broad DFI or DDSI coverage.

## 4.6 Alert-burden-aware workflow

RxCheck includes workflow mechanisms intended to manage alert burden. Findings are grouped and ranked by severity. Condition-gated DDSI logic prevents drug-disease alerts from appearing unless the relevant patient condition is active. Acknowledgments suppress reviewed findings without deleting the underlying evidence. If a later check produces a higher-severity version of a previously acknowledged finding, the finding is resurfaced. Overrides are persisted as user decisions but do not mutate the underlying evidence base or automatically suppress future findings.

These mechanisms are evaluated as architecture behavior. The paper does not claim that they reduce alert fatigue in real users.

## 4.7 Audit-oriented persistence

RxCheck stores check runs, finding snapshots, acknowledgments, overrides, audit events, and explanation records. This allows the system to preserve what was checked, what was found, what was displayed, what was acknowledged, what was overridden, and what explanation was generated.

This is described as audit-oriented persistence rather than compliance-grade auditing. The prototype does not currently implement authentication, role-based access control enforcement, immutable logs, HIPAA controls, or production-grade access monitoring.

## 4.8 Bounded LLM explanation layer

The LLM explanation endpoint requires an existing persisted finding. The model receives structured interaction context, source assertions, and optional OpenFDA label excerpts. The LLM is instructed to explain the existing finding, not to create a new finding or alter stored severity. Generated outputs are expected to follow a structured format and include fields such as summary, mechanism, clinical effect, management, severity rationale, sources used, and confidence.

RxCheck stores prompt/model metadata and can preserve failed validation output. It also performs drug-reference checking to detect whether an explanation mentions drugs outside the structured finding context. The confidence field is model-reported explanation confidence, not clinical certainty.

## 4.9 Cost-conscious service separation

RxCheck separates core deterministic checking from optional external services. Anthropic is optional for explanation generation. OpenFDA is optional for label-context enrichment. RxNorm is needed during new medication normalization but not at check time after medications are already normalized. This supports cost-conscious design analysis for budget-constrained settings, but it does not prove that the system is cheaper, cost-effective, or fully deployable offline.

---

# 5. Evaluation Methods

The evaluation was designed as a formative architecture evaluation. Its purpose was to test whether the implemented RxCheck artifact enforced selected architecture boundaries under controlled synthetic conditions.

The evaluation inserted uniquely named synthetic fixture records into the configured Postgres database and called the real production interaction-checking service. It then compared observed behavior with expected behavior for 26 scenarios. The evaluation recorded pass/fail status, observed outputs, code evidence, and manuscript-safe interpretation. It also verified that no paid or free external APIs were called during the core evaluation path.

The evaluation was not designed to test clinical accuracy, pharmacist usability, patient outcomes, source completeness, regulatory compliance, or cost-effectiveness.

The 26 scenarios tested:

1. Deterministic DDI from a stored row.
2. Canonical drug-pair ordering.
3. Inactive medication exclusion.
4. Placeholder drug exclusion.
5. Missing database interaction behavior.
6. DDSI absence without matching active condition.
7. DFI behavior independent of condition profile.
8. Severity ranking.
9. Source severity conflict flagging.
10. Source assertion preservation.
11. Check-run persistence.
12. Finding snapshot persistence.
13. Findings before LLM request.
14. Duplicate medication handling.
15. Placeholder visibility but exclusion.
16. DDSI presence with matching active condition.
17. Ranking across DDI, DDSI, and DFI.
18. DDSI absence after condition resolution.
19. Override persistence.
20. Override does not suppress future finding.
21. Acknowledgment severity escalation behavior.
22. Acknowledgment suppression behavior.
23. LLM explanation requires an existing finding.
24. Anthropic not required for core checking.
25. OpenFDA not required for core checking.
26. RxNorm not required at check time.

Additional evaluation artifacts included database profiling, focused automated tests, failure-mode analysis, cost-conscious deployment analysis, and an LLM explanation-quality rubric.

---

# 6. Results

## 6.1 Formative architecture evaluation

All 26 synthetic architecture scenarios passed. The evaluation called no paid external APIs and no free external APIs during the tested core architecture path.

| Evaluation category | What was tested | Result | What it supports |
|---|---|---|---|
| Deterministic checking | Stored DDI row creates finding; missing row creates no finding | Passed | Interaction findings come from stored data |
| Medication rejection | Inactive and placeholder medications are excluded | Passed | Unresolved inputs do not enter deterministic checks |
| Pair canonicalization | Reversed drug order maps to same DDI pair | Passed | Drug-pair lookup is reproducible |
| DDI/DFI/DDSI behavior | DFI independent of conditions; DDSI gated by active condition | Passed | Interaction types are handled differently |
| Severity and provenance | Ranking, source assertion preservation, conflict flags | Passed | Source provenance and disagreement are represented |
| Review workflow | Acknowledgment, escalation, override persistence | Passed | Alert-burden workflow behaves as designed |
| Audit persistence | Check runs and findings are persisted | Passed | Reviewable history is stored |
| LLM boundary | Explanation requires existing finding | Passed | LLM is downstream of deterministic findings |
| Service separation | Anthropic/OpenFDA/RxNorm not required for core check | Passed | Core checking is separated from optional services |

## 6.2 Database profile

The profiled database contained:

- 152,416 interaction records.
- 172,714 source assertions.
- 1,967 drugs.
- 1,934 aliases.
- 71 unresolved drug entries.
- 152,413 DDI rows.
- 1 DFI row.
- 2 DDSI rows.
- 174 interactions with more than one distinct asserted severity.

These numbers show that RxCheck is a non-trivial structured artifact rather than a toy lookup table. However, the database profile is descriptive. It does not establish clinical completeness, clinical accuracy, or source coverage quality. The strong concentration of DDI rows and limited DFI/DDSI rows means the paper must distinguish architecture support from imported coverage.

## 6.3 Automated tests

Focused automated tests passed. These tests covered the health endpoint and selected interaction-summary logic, including highest-severity selection, source conflict flags, DDI summary fields, hub scores, and DDSI condition naming. These tests support selected implementation behaviors but do not replace the broader formative architecture evaluation.

## 6.4 Failure-mode analysis

The failure-mode analysis identified several risks. Missing database interactions remain missed. RxNorm failures can produce unresolved placeholders or workflow disruption depending on failure type. OpenFDA failures reduce explanation context. LLM explanations may still hallucinate within the explanation layer. Prompt-injection defenses are incomplete. Authentication, authorization, production audit controls, HIPAA compliance, and FDA readiness are not implemented.

This failure-mode analysis is important because it prevents the paper from overstating the prototype’s maturity.

## 6.5 Explanation-quality rubric

The LLM explanation-quality rubric defines how future generated explanations should be evaluated. Criteria include schema validity, drug-name consistency, severity preservation, absence of unsupported new interaction claims, absence of unsupported dosing or prescribing instructions, evidence grounding, uncertainty handling, readability, source use, and prompt-injection resistance. In this version of the study, the rubric is an evaluation instrument, not completed clinical validation of explanation quality.

---

# 7. Discussion

The evaluation supports RxCheck as a design-science artifact for evidence-bound drug interaction decision support. The strongest result is not that RxCheck is clinically validated. The strongest result is that the current implementation enforces a set of architecture boundaries under synthetic evaluation.

First, RxCheck separates interaction detection from language generation. The LLM does not decide whether an interaction exists. Findings are produced by deterministic checking over stored interaction records. This reduces one category of LLM risk: model-generated interaction existence claims. However, it does not eliminate all LLM risk because generated explanations can still be incomplete, misleading, or insufficiently grounded.

Second, RxCheck treats uncertainty as a first-class system state. Unresolved medications are stored and visible but excluded from checking. This creates a rejection pattern: when the system does not know what a medication is, it does not pretend to know. This is especially important in drug interaction review because false certainty can be harmful.

Third, RxCheck preserves provenance rather than flattening evidence. Source assertions, raw payloads, and conflict flags allow the system to represent disagreement among imported sources. This does not determine which source is clinically correct, but it preserves information that a flattened interaction label would hide.

Fourth, RxCheck handles patient context through condition-gated DDSI logic. In the synthetic evaluation, DDSI findings appeared only when the matching condition was active and disappeared when the condition was resolved. This supports patient-context filtering as an architecture mechanism, although current DDSI database coverage remains limited.

Fifth, RxCheck treats alert burden as an architecture problem. Acknowledgment suppression, severity escalation behavior, duplicate prevention, condition gating, and override persistence are workflow controls rather than merely visual interface choices. These mechanisms are intended to reduce repeated burden while preserving evidence and review history. Whether they reduce alert fatigue in practice requires pharmacist user evaluation.

Sixth, RxCheck separates core checking from optional services. The formative evaluation showed that core checking did not require Anthropic, OpenFDA, or RxNorm at check time. This supports the frugal design argument: the core decision-support behavior can remain database-backed and inspectable, while LLM explanation and label-context retrieval remain optional enrichment layers.

Overall, RxCheck contributes an architecture pattern rather than a finished clinical tool. The pattern can be summarized as: normalize inputs, represent unresolved cases explicitly, determine findings through structured evidence, preserve source provenance, gate patient-context alerts, persist review decisions, and bound LLMs to explanation.

---

# 8. Limitations

This study has important limitations.

First, the evaluation is synthetic and architecture-focused. It tests whether selected system boundaries behave as intended, not whether the system is clinically accurate.

Second, RxCheck has not been evaluated by pharmacists or clinicians. The paper cannot claim improved decision quality, usability, alert-fatigue reduction, or patient-safety impact.

Third, the database profile does not establish complete interaction coverage. The current configured database is predominantly DDI, with very limited DFI and DDSI rows.

Fourth, RxCheck is not production-ready. It does not currently implement authentication, role-based access control enforcement, HIPAA controls, immutable audit logs, production access monitoring, or formal security hardening.

Fifth, the LLM explanation layer remains partially evaluated. The system includes structured context, expected output fields, confidence reporting, validation behavior, and drug-reference checks, but generated explanations have not been clinically scored by experts.

Sixth, external-service behavior is only partially addressed. Core checking does not require Anthropic, OpenFDA, or RxNorm at check time, but new medication normalization may still require RxNorm, and explanation enrichment may require OpenFDA or Anthropic.

Seventh, no formal cost analysis has been conducted. The paper can describe cost-conscious architecture, but not cost-effectiveness.

---

# 9. Future Work

Future work should proceed in five directions.

First, technical hardening is required. RxCheck needs authentication, role-based access control, safer CORS configuration, production secret management, immutable audit logs, access monitoring, stronger external-service failure handling, and expanded automated tests.

Second, source coverage should be expanded and evaluated. Future versions should improve DFI and DDSI ingestion, document source versions, compare imported coverage with source releases, and distinguish missing source evidence from absence of interaction risk.

Third, normalization should be evaluated more rigorously. Realistic medication-name inputs, misspellings, brand/generic cases, NDC examples, and ambiguous terms should be benchmarked against expected RxNorm mappings.

Fourth, LLM explanation quality should be scored using the proposed rubric. Explanations should be evaluated for schema validity, drug consistency, severity preservation, grounding, unsupported claims, prompt-injection resistance, and readability.

Fifth, pharmacist-facing evaluation is needed. A small usability study or expert review could assess whether the workflow, explanation layer, acknowledgment behavior, and override persistence are understandable and useful in realistic review scenarios.

---

# 10. Conclusion

RxCheck demonstrates a frugal, evidence-bound architecture for AI-augmented drug interaction review. The project’s contribution is not a clinically validated drug interaction checker or an autonomous clinical reasoning model. Its contribution is an architecture pattern for constrained decision support: normalize medication inputs, explicitly represent unresolved cases, determine findings through structured evidence, preserve source provenance, gate patient-context alerts, manage alert burden through review-state logic, persist user decisions, and restrict language models to explaining existing findings.

A 26-scenario formative architecture evaluation showed that the current prototype enforces selected architecture boundaries under synthetic conditions. Database profiling showed a non-trivial structured artifact with 152,416 interaction records and 172,714 source assertions, while also revealing limited DFI and DDSI coverage. The findings support RxCheck as a design-science prototype and a basis for future work, not as a deployable clinical system. Further validation, expert review, security hardening, source expansion, and usability evaluation are required before clinical use.