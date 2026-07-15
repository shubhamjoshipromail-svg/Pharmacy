# RxCheck Final Evidence-Completion Review

**Review date:** 2026-07-15

**Evaluated branch:** `research/journal-ready-paper`

**Evidence set:** Evidence 01–07

**Original manuscript:** `paper/rxcheck_manuscript_0.1v.md` (preserved; Git object `cd5c4ab332461544a1f083bfcfd65fd60b2b49e4`)

## Executive decision

All essential research tasks that are both feasible with the current repository and valuable to the proposed formative architecture paper have been completed for this cycle. The evidence base is substantially stronger than the initial review package because it now contains repeated clean-database execution, negative validator testing, source-file provenance recovery, an operational benchmark, a traceability audit, an independently referenced terminology benchmark, and a citation/related-work review.

The new evidence also exposes central limitations. The explanation validator failed, full DDInter transformation lineage could not be recovered, the broad traceability contract failed 5 of 15 criteria, and medication normalization failed 8 of 30 strict cases. These are not reasons to hide or discard the project; they define the appropriate article.

**Go/no-go decisions:**

- **GO** to create a new manuscript v2 as a transparent, formative design-science paper.
- **NO-GO** for journal submission in the current repository state.
- **NO-GO** for clinical use, real patient data, deployment, safety claims, or regulatory claims.

The paper's defensible contribution is an incremental and inspectable authority-boundary instantiation: on the evaluated path, persisted structured records create findings and optional generated prose is downstream of a selected finding. The paper is not evidence of clinical correctness, safe explanation, superior usability, comprehensive provenance, general normalization accuracy, or novelty of DDI explanation or hybrid rule-plus-LLM design.

## 1. Completed evidence and tests

| Evidence | Status | What was completed | Principal result | Publication value |
|---|---|---|---|---|
| 01 — Isolated architecture reproduction | Pass with limitations | Three repetitions of the unchanged 26-scenario evaluator in three fresh, disposable, loopback-only PostgreSQL databases | 26/26 each; 78/78 total scenario executions; identical outcomes; no external APIs reported on exercised paths | Converts the historical 26/26 result into a locally reproducible, bounded architecture result |
| 02 — LLM validator conformance | Fail | Thirty frozen valid, malformed, mistyped, inconsistent, ungrounded, and injection-shaped outputs tested against the unchanged validator | 3/3 valid accepted; only 5/27 invalid cleanly rejected; 15 false accepts; 7 unhandled exceptions | Directly disproves strict schema, grounding, hallucination-resistance, and prompt-injection-resistance claims |
| 03 — DDInter provenance recovery | Partial / full lineage fail | Git/history/local-file inspection, streaming source profile, official live byte comparison, hashes, HTTP metadata, terms review, and database-profile reconciliation | Eight official files verified; 222,383 concatenated rows, 160,235 unique pairs, 62,148 cross-file duplicates; semantic release and import accounting unavailable | Establishes source-file identity while preventing an unsupported clean-import or DDInter 2.0 claim |
| 04 — Core latency and repeatability | Pass with limitations | Eight workloads, 2/10/25/50 medications, zero/10%-matched pairs, 150,000 background rows, 5 warmups, 3 × 30 calls per workload | 720/720 correct; no exceptions/external calls; workload p95 2.586–245.124 ms; all local repeatability rules passed | Adds bounded single-machine operational evidence without implying an SLA or scalability |
| 05 — Persistence and traceability semantics | Mixed / broad contract fail | Fifteen prespecified criteria over attempts, pairs, sources, snapshots, acknowledgments, escalation, overrides, and actor attribution | 10/15 passed; failures in insufficient-attempt history, duplicate pair count, run-level source, display reconstruction, and removal actor | Separates selected persistence that works from broad audit-trail claims that do not |
| 06 — Medication normalization benchmark | Fail | Thirty frozen cases separately verified against RxNorm 06-Jul-2026/API 3.1.353 and, for three NDCs, DailyMed | 22/30 strict passes; exact 8/8, brands 7/7, NDCs 3/3; failures in misspelling/status, all combinations, constructed unknown, and injected outage | Provides the first independently referenced validation axis and a concrete negative result |
| 07 — Citation and related-work review | Complete / novelty narrowed | All 15 references verified and six required comparison categories reviewed through 2026-07-14 | 15/15 identities verified; 9 direct and 6 bounded uses; prior DDI explanation and hybrid rule-plus-LLM work found | Removes the bibliography placeholder and narrows the novelty claim to an incremental instantiation |

## 2. Failed, mixed, or inconclusive tests

### Failed against prespecified contracts

1. **Explanation validator:** The implementation did not enforce the claimed structural or semantic contract. Invalid outputs could be accepted or could raise uncontrolled exceptions. Live-model explanation quality was therefore not pursued as a positive evaluation.
2. **Full DDInter lineage:** The source files are identifiable, but the exact semantic release, alias state, quarantine records, inserted/conflicted counts, fixture separation, and database reconstruction are not recoverable from the retained artifacts.
3. **Broad traceability:** Five failures prevent claims that every attempt is recorded, pair and source metrics are faithful, the prior display can be reconstructed, or actor identity is reliable.
4. **Strict normalization:** The 22/30 result failed the all-cases contract. Multi-ingredient concepts collapse to one ingredient, some approximate candidates are invalid or misclassified, unknown input can become an unresolvable numeric concept, and a network error can escape instead of becoming explicit non-resolution.

### Passed only under narrow local conditions

1. **Architecture reproduction:** Passed self-authored synthetic scenarios on one machine and one local PostgreSQL build. It is not independent or clinical validation.
2. **Latency/repeatability:** Passed sequential warm-cache local tests. It is not end-to-end, concurrent, production, real-dataset, or scalability evidence.

### Not evaluated and therefore inconclusive

- clinical DDI sensitivity, specificity, positive predictive value, negative predictive value, severity correctness, or source completeness;
- pharmacist comprehension, usefulness, trust calibration, task time, or workflow fit;
- generated-explanation factuality, clinical appropriateness, or value versus a deterministic template;
- alert-fatigue reduction, prescribing changes, adverse-event reduction, or patient outcomes;
- authentication, authorization, confidentiality, retention, tamper evidence, incident response, or compliance;
- production reliability, concurrency, throughput, recovery, cost, or low-resource deployment;
- regulatory classification, HIPAA status, intellectual-property clearance, or data-license compatibility.

## 3. Claims now fully supported within explicit bounds

“Fully supported” below applies only to the stated software/evidence boundary. It does not imply clinical validity.

| Bounded claim | Supporting evidence | Required qualifier |
|---|---|---|
| RxCheck is an inspectable FastAPI/React/PostgreSQL research prototype at the evaluated repository snapshot. | Code inspection and review package | Versions and production readiness are not established by this description. |
| On the evaluated core path, findings are created from stored interaction rows, not by the LLM. | Evidence 01 plus inspected orchestrator | A missing row means no stored finding, not no clinical interaction. |
| The explanation endpoint requires a persisted finding and cannot create a check finding through that endpoint. | Evidence 01 and endpoint inspection | Generated prose may still be wrong, unsupported, or unsafe. |
| The unchanged 26-scenario evaluator passed from fresh local databases in three repetitions. | Evidence 01 | Report 26/26 per repetition and 78/78 total as architecture conformance, not accuracy. |
| Anthropic, OpenFDA, and RxNorm were not called by the exercised core-check paths. | Evidence 01 and Evidence 04 | New medication entry and optional explanation can still require external services. |
| The recovered DDInter bundle consists of eight identified official files with recorded acquisition metadata and hashes. | Evidence 03 | Identify the bundle by manifest, not a semantic release or DDInter 2.0 label. |
| The recovered raw bundle has 222,383 concatenated rows, 160,235 unique canonical identifier pairs, and 62,148 cross-file duplicates. | Evidence 03 | These are source-bundle counts, not reconstructed database-import counts. |
| The tested local core calls returned the expected counts with the recorded latency distribution. | Evidence 04 | Report environment/workloads and avoid SLA, throughput, or production language. |
| Selected completed runs, findings, acknowledgment creation/suppression/escalation, and finding-level overrides persist as tested. | Evidence 05 | List the five failed semantics in the same section. |
| The tested exact ingredient, brand, and NDC subsets mapped to expected ingredients. | Evidence 06 | Report 8/8, 7/7, and 3/3 only; do not generalize to population accuracy. |
| All 15 current references have verified bibliographic identities. | Evidence 07 | Six sources are context-only and require bounded wording. |

## 4. Claims now partially supported

| Claim area | Supported component | Unsupported component | Required disposition |
|---|---|---|---|
| Medication normalization | Exact, brand, and NDC cases passed in the frozen set | General accuracy, complete ingredient representation, safe unknown handling, method-label fidelity, outage degradation | Report the full 22/30 result and concrete failure classes |
| Explicit non-resolution | Empty input and some unmatched paths are represented without checking | Constructed unknown and injected outage did not reliably reach the safe unresolved path | Replace universal language with “attempts resolution; selected failure paths are unsafe or uncontrolled” |
| Source provenance | Source assertions exist; raw source bundle identity and hashes are known | Semantic release, complete transformation lineage, faithful run source, historical display reconstruction | Use “source-assertion model and partial provenance record,” not “complete provenance” |
| DDI/DFI/DDSI support | Schema/query branches and synthetic behavior exist | Real importer is DDI-only; genuine DFI/DDSI coverage and clinical correctness are absent | Separate representational capability from imported coverage |
| Review-state traceability | Selected run/finding/review records persist | Every attempt, exact display, reliable actor, immutability, read audit, and compliance controls | Use “audit-oriented persistence of selected events” |
| Reproducibility | Evidence 01 and 04–06 have executable local harnesses and retained raw outputs | Empty migration, unpinned dependencies, no one-command prerequisite setup, no complete data reconstruction, no independent rerun | Use “locally reproducible protocols under recorded prerequisites,” not “fully reproducible system” |
| Output validation | JSON parsing, required-key checks, one list check, and a stored-drug-name scan exist | Strict typing, complete JSON consumption, severity/source consistency, unsupported-content rejection, controlled failures | Describe only the exact custom checks and report the failed audit |
| Performance | Core warm-cache sequential latency is measured | End-to-end, concurrent, production, external-service, real-data, and cost behavior | Keep results in a formative operational subsection |
| Cost-conscious separation | Core checking can avoid optional paid generation on tested paths | Affordability, total cost, staffing, bandwidth, or suitability in constrained settings | Keep only as design rationale/future work |
| Scholarly contribution | The implemented authority boundary is clear and inspectable | Broad novelty is precluded by prior DDI explanation and hybrid architectures | Use “incremental instantiation and negative formative evaluation” |

## 5. Claims that must be removed or narrowed

| Remove or avoid | Required replacement |
|---|---|
| “strict RAG” | “optional generated explanation supplied with structured finding context and heuristic label excerpts” |
| “schema-validated output” | “custom JSON parsing and limited post-generation checks; a 30-case audit found major enforcement failures” |
| “normalize or explicitly reject uncertain inputs” | “attempt medication resolution; retain some unresolved inputs, with documented failures for combinations, invalid candidates, unknowns, and outages” |
| “complete audit trail” or “what was displayed can be reconstructed” | “audit-oriented persistence of selected completed runs, findings, and review actions” |
| “DDInter 2.0 data were imported” | “eight manifest-identified official DDInter DDI files were recovered; their semantic release is unknown” |
| “multi-source evidence reconciliation” | “a model can retain multiple assertions and flag stored severity-label differences; observed data are overwhelmingly one source” |
| “patient-specific DDI prioritization” | “implementation-defined maximum severity, conflict flag, graph-degree count, and limited condition gating” |
| “safe,” “grounded,” “hallucination resistant,” or “prompt-injection resistant” explanation | State that these properties are unsupported and that the validator failed |
| “novel” or “first” evidence-bounded/hybrid DDI explanation architecture | “incremental, inspectable authority-boundary instantiation” |
| “superior to templates” or “improves comprehension” | State that a deterministic source-filled template and pharmacist comparison remain required |
| “frugal,” “affordable,” or “suitable for resource-constrained pharmacies” | “cost-conscious separation of core checking from optional external generation” |
| “clinically validated,” “clinically accurate,” “reduces alert fatigue,” “improves outcomes,” or “deployment ready” | Remove; explicitly state these were not evaluated |
| “HIPAA compliant,” “FDA non-device,” or other regulatory conclusion | Remove; state that no legal/regulatory determination was performed |
| “open-source reusable software” | “publicly visible source repository without a confirmed root software license” until the rights holder selects a license |

## 6. Remaining external-validation and author-authority needs

| Remaining action | Why it is blocked now | Resource/authority required | Manuscript treatment until complete |
|---|---|---|---|
| Revoke/rotate the exposed credential, inspect access, and remediate Git history | Requires provider and repository-owner control; history rewrite affects all clones | Repository owner, database provider, and incident/security review | Prominent no-real-data/prototype warning; no submission while the exposed credential remains active/history unresolved |
| Determine whether any real or identifiable data were exposed | Cannot be inferred safely from code alone | Data owner, provider logs, institutional privacy/security authority | Do not claim de-identification, HIPAA compliance, or safe public release |
| Clinical DDI reference validation | No authoritative, adjudicated case set or clinical reviewer is available | Pharmacist/clinical pharmacologist and transparent reference standard | No clinical accuracy, safety, or coverage claim |
| Explanation remediation and comparative evaluation | Current validator failed; live prose would not be a defensible positive result | Engineering authorization, frozen model/version, deterministic template, pharmacist reviewers | Keep generation optional, downstream, and unevaluated for benefit |
| Pharmacist usability/human-factors evaluation | Requires actual users, ethics determination, protocol, and recruitment | Pharmacist participants, methods support, and institutional review/waiver | No workflow, trust, comprehension, fatigue, or usefulness claim |
| Fresh manifest-driven DDInter import | Historical alias/quarantine/import state is missing and source licensing must be reviewed | Publisher/source clarification, reviewed importer, complete logs, license review | Report raw manifest only; database totals remain unreconciled observations |
| Independent reproduction | All current executions were performed by the same AI-assisted research process on one machine | Second researcher and second machine/environment | Describe local reproduction, not independent reproduction |
| Software/data licensing | Rights selection and compatibility are legal/author decisions | Copyright holder and qualified license review | No reuse-rights claim; state DDInter's separate terms |
| Ethics, authorship, funding, conflicts, contributions, acknowledgments | Information is not discoverable from the repository | Authors and institution | Keep explicit author-supplied placeholders; do not invent statements |
| Target-journal compliance and current policies | Journal choice and fees are author decisions and policies change | Corresponding author, current journal instructions, possibly librarian | Do not claim submission readiness until a journal-specific check is complete |

## 7. Updated publication-readiness score

**Updated score: 61/100** (previous review: 46/100; change: +15)

The increase rewards executed evidence, reproducibility artifacts, transparent negative results, and completed scholarship. It does not indicate improved clinical performance.

| Category | Updated | Maximum | Change | Rationale |
|---|---:|---:|---:|---|
| Originality | 4 | 10 | -1 | Related work is now established, but it shows direct method-class precedent and requires an incremental claim. |
| Significance | 5 | 10 | 0 | The authority-boundary problem remains relevant; no user or clinical benefit is demonstrated. |
| Technical contribution | 7 | 10 | 0 | The artifact is substantive and inspectable, but normalization, traceability, security, and validator defects remain. |
| Methodological rigor | 9 | 15 | +4 | Fresh-database repetitions, prespecified failure contracts, retained raw results, and an independent terminology-reference axis materially improve rigor. |
| Evidence and evaluation quality | 9 | 15 | +4 | Seven evidence units now cover architecture, failure modes, data, operations, traceability, normalization, and scholarship; external/clinical validity remains absent. |
| Reproducibility | 6 | 10 | +3 | Multiple local harnesses, environment records, raw outputs, hashes, and teardown exist; schema/dependency/data reconstruction and independent rerun remain incomplete. |
| Clarity and organization | 8 | 10 | +1 | The evidence trail and claim implications are clear; manuscript v2 and final journal tailoring are not yet complete. |
| Safety and ethics | 4 | 10 | 0 | Risks are now tested and disclosed more clearly, but the exposed credential, absent auth, and unresolved incident remain serious. |
| Citation quality | 5 | 5 | +3 | All current references are verified and a structured comparison is complete. |
| Journal fit | 4 | 5 | +1 | A candid formative design-science paper is plausible; it remains unsuitable as a clinical/production paper. |
| **Total** | **61** | **100** | **+15** | **Stronger research record, still not submission-ready.** |

## 8. Updated go/no-go recommendation

### GO: manuscript v2 preparation

Create a new manuscript that reports both passes and failures and targets a formative health-informatics/design-science article. The central research question should remain software-architectural: whether the prototype allocates finding authority to stored deterministic logic and places optional generation downstream.

### NO-GO: current submission

Do not submit yet. Immediate submission blockers are:

1. exposed-credential revocation/history remediation and incident determination are incomplete;
2. software licensing and third-party data-use review are unresolved;
3. author, ethics, funding, conflicts, contributions, and acknowledgments are missing;
4. no target-journal compliance review has been completed;
5. no external clinical or pharmacist validation exists; and
6. the final v2 manuscript and figures have not been quality checked.

For a strictly formative venue, the absence of clinical outcomes can be acceptable if the scope is explicit. The security, rights, authorship, and submission-declaration blockers are not optional.

## 9. Exact changes required in the final manuscript

### Title and identity

- Use a title that names the authority boundary and prototype status. Recommended working title: **“A Deterministic Finding-Authority Boundary for Optional Generative Explanation in Drug-Interaction Review: Design and Formative Evaluation of the RxCheck Prototype.”**
- Keep a prominent prototype warning: not clinically validated, not for clinical use, and no real patient data.
- Identify the evaluated application snapshot and separately identify the evidence-branch revision.

### Abstract

- Replace the historical-only method with the executed Evidence 01–06 methods.
- Report the principal results numerically: repeated 26/26 architecture passes; validator 5/27 invalid controlled rejects with 15 false accepts and 7 exceptions; source bundle counts/lineage limitation; 720/720 local calls and p95 range; traceability 10/15; normalization 22/30.
- State that the architecture boundary passed on synthetic paths while supporting validation, lineage, traceability, and normalization contracts had material failures.
- Conclude only that the case study demonstrates an inspectable authority allocation and the value of adversarial formative testing.

### Introduction and contribution

- Recast the gap as safe allocation of authority and transparent evaluation, not absence of DDI explanations or RAG.
- Define “evidence-bounded” as an access/authority boundary, not a factuality guarantee.
- State explicitly that the contribution is incremental and that negative findings are part of the contribution.
- Retain one primary research question and reduce secondary questions to identity, provenance/traceability, and operational behavior.

### Related work

- Replace the unresolved marker with Evidence 07's structured comparison.
- Add Payne et al., Chou et al., ExDDI, MedRAG, Holbrook et al., and an appropriately versioned FHIR Provenance citation.
- Distinguish RxCheck from ExDDI and from the 2026 non-peer-reviewed hybrid DDI preprint without claiming superiority.
- Name a deterministic source-filled template as the missing comparator.

### Methods

- Describe the artifact snapshot, local PostgreSQL/Python environment, safety guardrails, and read-only preservation rules.
- Present Evidence 01–06 as distinct protocols with objectives, frozen inputs, metrics, pass/fail rules, and retained outputs.
- Make clear which cases were self-authored and which expected outcomes were independently checked against official terminology sources.
- State that no live model output, clinician, patient, or clinical outcome was evaluated.
- Explain that the citation review was targeted, not systematic.

### Results

- Separate results into: architecture reproduction; validator conformance; source provenance; core latency; traceability; normalization; and related-work outcome.
- Report all failed criteria, not only aggregate pass rates.
- Do not combine the raw source-bundle counts with unreconciled configured-database totals.
- Include exact denominators and label purposive case rates as non-population estimates.

### Architecture and data description

- Correct universal normalization language using Evidence 06.
- Describe run/finding snapshots using the precise supported fields and list absent historical display fields.
- State that run-level source can be inaccurate and that actor identity is unauthenticated.
- Separate DDI/DFI/DDSI representational branches from actual imported coverage.
- Describe graph degree and maximum severity as implementation rules, not validated risk or clinical-priority scores.

### Safety, privacy, governance, and regulation

- Add a dedicated section reporting the exposed credential, missing authentication/authorization, permissive prototype controls, and prohibition on real data.
- Report the validator failure as a safety-relevant negative result.
- Make no HIPAA, FDA, compliance, or deployment determination.
- State that no stored finding is not evidence of no clinical interaction.

### Discussion and conclusion

- Lead with the supported authority-boundary result, then the four major failure areas.
- Explain why negative tests changed the interpretation of the artifact.
- Compare the result with conventional/template alerts, contextualized DDI algorithms, ExDDI, medical RAG, and provenance standards.
- Do not claim that an LLM adds value; frame it as an optional component requiring remediation and comparative human evaluation.
- End with a formative conclusion and external-validation sequence, not readiness language.

### Availability and declarations

- Link the exact research branch/commit and evidence index after security remediation.
- Describe which artifacts are included and which DDInter files are external under separate terms.
- Add author-supplied ethics, funding, conflicts, CRediT contributions, acknowledgments, and corresponding-author data.
- Do not claim open-source reuse until an explicit license is selected.

### References, tables, and figures

- Replace reference 6's arXiv link with the official NeurIPS proceedings record.
- Add access dates to mutable agency/provider/standards pages.
- Retain the Hevner publisher-artifact page range 75–105 and document the metadata discrepancy outside the manuscript if needed.
- Include a requirements-to-evidence table, a consolidated evidence-results table, and the related-work comparison.
- Update the authority-boundary diagram to show invalid-output and external-service failure paths; label the LLM output as non-authoritative prose.

## 10. Recommended manuscript revision order

1. Create `research/journal_revision/manuscript/journal_ready_manuscript_v2.md` as a new file; never edit the original paper or v1 draft in place.
2. Freeze a claim-to-evidence map from Sections 3–5 of this review and use it as the controlling source for all wording.
3. Rewrite the research question, contribution statement, and section architecture around the incremental finding-authority boundary.
4. Rewrite Methods from the executed Evidence 01–07 protocols, including denominators, pass/fail criteria, environments, and limitations.
5. Rewrite Results from retained raw outputs; insert all positive and negative quantitative results before writing interpretation.
6. Correct the artifact/data description using the normalization, provenance, and traceability findings.
7. Replace the related-work placeholder using Evidence 07 and add the deterministic-template baseline gap.
8. Rewrite Discussion, Safety/Governance, Threats to Validity, and Future Work from the consolidated claim classifications.
9. Write the Conclusion to match only the supported authority-boundary contribution and negative formative findings.
10. Draft the title and abstract last so they match the completed body and do not overstate novelty or validation.
11. Create the manuscript change log, claim-to-evidence map, and submission-readiness checklist required by the task.
12. Run a final numerical, citation, internal-link, terminology, placeholder, and original-file-preservation audit before committing and pushing the manuscript phase.

## Stop-condition determination

The feasible evidence cycle stops here. Additional self-authored synthetic cases would have diminishing value and would not address the central remaining risks. The next high-value evidence requires one or more of: provider/repository authority, a pharmacist or clinical pharmacologist, a second independent researcher, institutional review, legal/license review, or a selected journal. Those needs are recorded as external actions rather than silently omitted.
