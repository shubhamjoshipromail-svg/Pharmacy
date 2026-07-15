# RxCheck Journal-Readiness Review

## Editorial decision

**Reject and resubmit.**

The project contains a coherent architecture contribution and a candid formative evaluation, but the current manuscript is not ready to enter peer review as a journal article. The most consequential blockers are an exposed database credential, incomplete reproducibility, absent source/version provenance, no completed evaluation of generated explanations, no independent benchmark, citation placeholders, and an underdeveloped comparison with related work. These deficiencies are remediable without a clinical trial if the article remains a design-science/formative architecture paper.

## Reviewer-style summary

The manuscript describes RxCheck, a Postgres-backed FastAPI/React prototype for pharmacist-oriented drug-interaction review. The artifact normalizes medication input toward RxNorm identifiers, stores unresolved input as placeholders, checks imported interaction rows deterministically, condition-gates drug-disease interactions, preserves source assertions, persists selected review state, and offers an optional LLM explanation endpoint for existing findings. A recorded formative evaluation reports 26 of 26 synthetic architecture assertions passing, accompanied by a timestamped database profile and three focused tests.

The central design idea—limiting a language model to rendering an existing deterministic finding—is clear, relevant, and implemented. The manuscript also avoids many common overclaims. However, the study currently demonstrates only selected software behavior in one configured environment. It does not establish interaction accuracy, normalization performance, explanation grounding, pharmacist usefulness, alert-fatigue reduction, cost advantage, or production safety. Several claims and terms, especially “strict RAG,” “frugal,” “reproducible,” and “source disagreement,” require narrower wording. The repository’s exposed credential and incomplete research packaging are immediate barriers to submission.

## Submission-readiness score

**46/100**

| Category | Score | Maximum | Editorial assessment |
|---|---:|---:|---|
| Originality | 5 | 10 | The boundary pattern is useful, but novelty relative to deterministic CDS plus LLM explanation is not established through a focused comparison. |
| Significance | 5 | 10 | The safety-boundary problem matters, but no user, clinical, or operational benefit is demonstrated. |
| Technical contribution | 7 | 10 | The artifact is substantive and inspectable; several implementation inconsistencies and security defects remain. |
| Methodological rigor | 5 | 15 | Requirements and scenarios are explicit, but the evaluation is self-authored, persistent-database coupled, and lacks independent or negative validation. |
| Evidence and evaluation quality | 5 | 15 | The 26 assertions verify architecture behavior only; LLM, normalization, clinical coverage, and usability evaluations are missing. |
| Reproducibility | 3 | 10 | Code/results exist, but data/version/checksums, migrations, dependency lock, clean fixtures, teardown, and safe configuration are absent. |
| Clarity and organization | 7 | 10 | The draft is clear and conservative, but repetitive and not yet tailored to a specific journal format. |
| Safety and ethics | 4 | 10 | Limitations are stated, but the exposed secret, absent access controls, and missing ethics/security remediation record are serious. |
| Citation quality | 2 | 5 | Related-work sections contain placeholders and no completed bibliography. |
| Journal fit | 3 | 5 | A formative informatics venue is plausible once claims and methods are aligned. |
| **Total** | **46** | **100** | **Promising but not submission-ready.** |

## Major concerns

1. **Repository security and research integrity.** A credential-bearing database URL is committed in three files. The credential must be revoked/rotated, removed from the active tree and history, and the incident assessed before a public manuscript points reviewers to the repository.
2. **Reproducibility is not demonstrated.** The exact DDInter release, checksums, data-transformation counts, database snapshot, schema migration, dependency versions, and clean evaluation environment are unavailable. The sole Alembic migration is empty.
3. **The evaluation is too internal for the breadth of the claims.** The 26 scenarios assert behavior the authors encoded. That is useful verification but needs at least one modest independent axis: reference interaction cases, normalization cases, or completed explanation-boundary review.
4. **The generative component is not evaluated.** The paper proposes a rubric but reports no scored explanations. It cannot claim effective grounding, safe explanation, or quality improvement.
5. **Clinical-data coverage is easily misunderstood.** The real importer is DDI-only; the profile reports only one DFI and two DDSI rows, including fixtures/manual entries. Schema capability and source coverage must be separated everywhere.
6. **Novelty is not yet established.** The paper defines “evidence-bound AI” but does not compare the design with conventional rule-based CDS, retrieval-grounded explanation systems, templated explanation, provenance models, or responsible AI-CDS frameworks.
7. **Frugality is not evaluated.** Optional-service separation is a legitimate architecture property; affordability in resource-constrained pharmacy settings is not.
8. **Security, privacy, and governance are architectural limitations, not footnotes.** No authentication, route-level authorization, reliable identity, strict CORS, immutable audit, or production secret management exists, despite a schema capable of storing identifiable health data.

## Minor concerns

- The abstract gives exact database totals without foregrounding that they are timestamped, live-configuration observations containing fixtures.
- The manuscript refers to “schema validation” more strongly than the custom parser warrants.
- “Confidence” is model-reported text, not calibrated uncertainty.
- The explanation context uses only the first assertion’s mechanism/management.
- `sources_used` is hard-coded to DDInter at run level and can disagree with finding assertions.
- The check path returns early without persisting attempts involving fewer than two verified active medications.
- Duplicate medication rows do not duplicate a finding but can distort pair-count reporting.
- The phrase “clinical decision support” should consistently be preceded by “prototype” or “preclinical” to avoid implying deployment status.
- No exact software versions, operating system, database version, or hardware are reported.
- Author information, contributions, funding, ethics determination, conflicts, and acknowledgments are absent.
- Existing Mermaid diagrams need rendering, numbering, captions, and accessibility text.
- The repository has no explicit software license.

## Likely reasons for rejection

1. Immediate editorial concern about an exposed secret in a linked public repository.
2. Manuscript claims a reproducible evaluation without providing enough materials to reproduce the database and environment.
3. Evaluation shows code conformance to authored scenarios but not external validity, clinical validity, or explanation quality.
4. Related work and references are incomplete.
5. Article title and framing imply economic/setting relevance that was not studied.
6. The paper could be read as a clinical CDS report despite having no authenticated users, clinical data, clinicians, or clinical benchmark.
7. Data/source licensing and software licensing are unresolved.

## Changes most likely to improve acceptance probability

1. Resolve the credential incident and document a safe, secret-free research release.
2. Package a one-command, isolated evaluation with pinned dependencies, a real migration, seeded synthetic data, teardown, commit SHA, and machine-readable results.
3. Add an independently specified small reference set. For the proposed article type, 20–50 transparent interaction/normalization cases reviewed by a pharmacist or derived from cited authoritative examples would materially strengthen the work; a trial is not necessary.
4. Complete the explanation-boundary assessment on a frozen sample, report all criterion-level scores and failures, and avoid clinical-accuracy language.
5. Reframe the title and objective around evidence-bounded explanation architecture; move cost-consciousness to design rationale/future evaluation.
6. Add a focused related-work table comparing RxCheck with rule-based DDI CDS, DDInter/RxNorm resources, RAG/grounded generation, and responsible AI-CDS design guidance.
7. Report exact data provenance, quarantine/mapping results, fixture-adjusted counts, and known coverage gaps.
8. Add a license, data-use notice, author/disclosure statements, and rendered figures.

## Sections missing, misplaced, repetitive, or underdeveloped

| Issue | Recommendation |
|---|---|
| Background repeats limitations and architecture claims. | Compress background and move repository-specific behavior to artifact design. |
| Design requirements are useful but not linked to derivation. | State whether requirements came from literature, author judgment, implementation constraints, or post hoc inspection. |
| Evaluation methods do not identify software/data revision in the results artifact. | Add commit SHA, schema revision, environment, data release, fixture lifecycle, and analysis procedure. |
| Results combine verification, database description, and proposed rubric. | Separate executed results from unexecuted evaluation instruments. |
| Security is spread across limitations. | Add a dedicated safety, privacy, and governance section with explicit prototype boundaries. |
| No related-work comparison table. | Add one, emphasizing the claimed architecture contribution. |
| No threat-to-validity section. | Add construct, internal, external, and reproducibility validity threats. |
| No formal availability statements or author declarations. | Add data/code availability, ethics, funding, conflicts, contributions, and acknowledgments. |

## Claims that should be narrowed

- “strict RAG” → “structured evidence context with optional label excerpts.”
- “evidence-bound AI” → “evidence-bounded explanation architecture.”
- “frugal” → “cost-conscious service separation.”
- “reproducible formative evaluation” → “committed evaluator and recorded formative run” until independent rerun is possible.
- “source disagreement” → “stored severity-label differences.”
- “schema-validated” → “custom JSON and required-field checks.”
- “audit trail” → “audit-oriented persistence of selected events.”
- “supports DFI/DDSI” → distinguish schema/query support from negligible current imported coverage.
- “working system” → “research prototype at the inspected commit.”
- “pharmacist-facing” → “pharmacist-oriented,” unless actual pharmacists are studied.

## Publication positioning

Best current positioning after required revisions:

1. **JMIR Formative Research — formative technology/design evaluation.** Its stated scope includes feasibility, pilot, process, and other formative work before summative outcomes evaluation. This is the closest conceptual match: <https://formative.jmir.org/about-journal/focus-and-scope>.
2. **JAMIA Open — Application Note or Research and Applications.** The journal accepts software implementations and formative evaluations, but its author guidance expects public code and repeatable archived analyses. An Application Note would require a tighter manuscript; a full Research and Applications paper would need stronger evaluation: <https://academic.oup.com/jamiaopen/pages/General_Instructions>.
3. **Frontiers in Digital Health — Technology and Code or Methods in Health Informatics.** This is plausible only after appropriate validation because its scope explicitly requires validation for computational studies using public data: <https://www.frontiersin.org/journals/digital-health/about>.

JAMIA Open is a stretch target in the current state. JMIR Formative Research is the most realistic first target after remediation. Journal of Open Source Software should not be targeted until a software license, installation/reproduction path, and research-grade tests exist.

## Recommended article structure

1. Title
2. Structured Abstract: Background, Objective, Methods, Results, Conclusions
3. Keywords
4. Introduction and Objective
5. Related Work and Design Context
   - DDI decision support and alert burden
   - Medication normalization and interaction knowledge sources
   - Generative AI, grounding, and health-AI governance
   - Gap addressed by the artifact
6. Design-Science Approach
   - Problem identification
   - Artifact objective and scope
   - Design requirements and their provenance
7. Artifact Architecture
   - Input normalization and explicit non-resolution
   - Interaction and provenance model
   - Deterministic orchestration and patient-context gating
   - Review-state persistence
   - Evidence-bounded explanation layer
8. Data and Implementation Context
   - Exact source/version and import path
   - Software stack, schema, versions, and deployment boundary
9. Formative Evaluation
   - Architecture scenario protocol
   - Independent reference cases or completed boundary evaluation
   - Reproducibility environment
10. Results
   - Scenario-family results
   - Data profile with fixture adjustment
   - Independent/boundary-evaluation results
11. Safety, Privacy, Governance, and Human Oversight
12. Discussion
   - Design implications
   - Comparison with related approaches
   - What the artifact does and does not establish
13. Threats to Validity and Limitations
14. Future Work
15. Conclusion
16. Ethics, Funding, Contributions, Conflicts, and Acknowledgments
17. Data and Code Availability
18. References

## Editorial conclusion

The paper should be invited back only after the secret is remediated, the research package is safely reproducible, the bibliography and novelty argument are completed, and at least one external or independently specified validation component is added. The artifact does not need a clinical trial to support a design-science contribution, but it does need evidence that goes beyond confirming its own implementation rules.
