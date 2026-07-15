# Results

## Overall disposition

| Measure | Result | Disposition |
|---|---:|---|
| Existing references checked | 15/15 | Complete |
| Bibliographic identities verified | 15/15 | Pass |
| Direct claim fit | 9/15 | Retain within stated bounds |
| Bounded/context-only claim fit | 6/15 | Retain only with explicit limits |
| Insufficient or contradicted uses | 0/15 | None if the limits below are followed |
| Required related-work categories covered | 6/6 | Pass |
| Broad novelty position | Unsupported | Must narrow |

## Existing-reference audit

| Ref. | Identity | Fit | Finding and required action |
|---:|---|---|---|
| 1 | Verified | Direct | Supports variable performance of pharmacy DDI CDS in a standardized 64-pharmacy evaluation. It does not validate RxCheck or all commercial systems. |
| 2 | Verified | Direct | Supports alert-fatigue, interaction-design, and role-tailoring context. It does not show that RxCheck reduces fatigue or improves acceptance. |
| 3 | Verified | Direct | Supports RxNorm as normalized clinical-drug nomenclature and identifier infrastructure. It does not establish RxCheck mapping accuracy; use Evidence 06 for that. |
| 4 | Verified | Bounded | Supports the published DDInter resource and its richer web/database annotations. It does not prove that RxCheck's recovered five-column files include or preserve those annotations. |
| 5 | Verified | Bounded | Supports DDInter 2.0 capabilities. Evidence 03 did not establish that the recovered bundle is a DDInter 2.0 release, so never label the imported bundle as 2.0. |
| 6 | Verified | Bounded | Supports the definition and original evaluation of RAG. It is not health-specific and does not establish faithful or safe clinical generation. Replace the arXiv link with the official NeurIPS proceedings URL and add medical-RAG evidence. |
| 7 | Verified | Bounded | Supports both strong medical-question-answering performance and important human-evaluation limitations. It is not a DDI explanation or workflow study. The Nature page identifies a publisher correction; cite the corrected article record. |
| 8 | Verified | Direct | Supports staged validation, governance, monitoring, privacy, and human-centered AI-CDS recommendations. It is guidance, not evidence that RxCheck complies. |
| 9 | Verified | Direct | Supports WHO ethical/governance principles. It does not certify RxCheck as safe or responsible. |
| 10 | Verified | Direct | Supports general design-science framing. The final PDF prints pages 75–105; Crossref currently reports 75–106, so retain the publisher-artifact range 75–105 and record the discrepancy. |
| 11 | Verified | Direct | Supports the six-step design-science research methodology. The issue is often styled Winter 2007–2008; DOI metadata gives 2007 and pages 45–77, matching the draft. Do not imply the project followed the process prospectively without author evidence. |
| 12 | Verified | Bounded | This commentary supports only the concept of frugal innovation. It cannot establish affordability, resource suitability, or frugality of RxCheck. |
| 13 | Verified | Direct | The official WHO guideline explicitly considers benefits, harms, acceptability, feasibility, resource use, and equity. It is generic digital-health guidance, not an RxCheck evaluation. |
| 14 | Verified | Bounded | The FDA page confirms final Clinical Decision Support Software guidance in January 2026 and Non-Device CDS criteria. Applying those criteria to RxCheck requires case-specific legal/regulatory analysis. |
| 15 | Verified | Direct | The official DDInter terms support the CC BY-NC-SA 4.0 and incompleteness statements. Licensing obligations still require author/publisher review. |

## Bibliographic actions

1. Keep references 1–5 and 7–15 with the boundaries above.
2. Change reference 6 from the arXiv landing page to the official NeurIPS proceedings record.
3. Add access dates to mutable organizational and terms pages.
4. Add the closest related work listed below rather than leaving a related-work placeholder.
5. Preserve the publisher-artifact page range of 75–105 for Hevner et al.; document rather than silently copy Crossref's conflicting endpoint.

## Related-work result

The structured comparison is in `related_work_comparison.md`. The most important findings are:

- Commercial/rule-based DDI checking and its variable performance predate RxCheck.
- Expert-designed patient-context algorithms have already been implemented and tested retrospectively; RxCheck's condition gating is narrower and only synthetically tested.
- Usability guidance already specifies interacting drugs, seriousness, consequences, mechanism, context, actions, and evidence as alert content. A deterministic source-filled template is therefore the essential baseline for any explanation benefit claim.
- ExDDI (AAAI 2025) already generates natural-language explanations for DDI predictions. It addresses predicted unknown interactions rather than RxCheck's persisted known findings, but it prevents any broad claim that natural-language DDI explanation is novel.
- MedRAG (ACL 2024) already benchmarks medical RAG at scale. RAG is contextual background, not an RxCheck contribution.
- FHIR Provenance and CDS Connect demonstrate mature concepts for versioned provenance and reusable CDS knowledge artifacts. RxCheck's custom source assertions and snapshots are not standards-conformant and Evidence 05 found material traceability gaps.
- A contemporaneous April 2026 SSRN preprint explicitly combines rule-based DDI reasoning with LLM-assisted explanation. It is not peer reviewed and its claims were not independently validated here, but its existence makes a broad hybrid-architecture novelty claim especially untenable.
- A 2025 systematic review found little high-quality evidence that DDI alerts improve patient-important outcomes. RxCheck has no clinical outcome evidence and must remain a formative software-architecture study.

## Narrowest defensible contribution

> RxCheck is an inspectable design-science instantiation of a conservative authority allocation: stored deterministic interaction records create persisted findings, while optional generated prose is downstream of a selected finding. The contribution is the documented integration and formative evaluation of that boundary together with selected source-assertion and review-state semantics—not a new DDI detection method, RAG method, provenance model, or explanation-generation method.

Even this contribution must be paired with the failed Evidence 02 validator result and the mixed Evidence 05 traceability result. The paper should use terms such as **prototype**, **instantiation**, **design pattern**, **formative evaluation**, and **incremental contribution**, not **first**, **novel**, **validated**, **safe**, or **evidence-grounded** without a precise qualifier.

## Step disposition

The review protocol's completion criteria passed. Its scientific result is a mandatory narrowing of novelty and claims, not a positive efficacy finding.
