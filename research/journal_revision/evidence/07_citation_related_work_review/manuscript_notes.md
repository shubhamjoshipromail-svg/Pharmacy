# Manuscript Notes

These notes apply to the future v2 manuscript. Do not edit `05_journal_ready_manuscript.md` in place.

## Required framing changes

1. Replace the unresolved related-work marker with a compact structured comparison based on `related_work_comparison.md`.
2. Describe the contribution as an **incremental, inspectable design-science instantiation** of a conservative authority boundary.
3. Explicitly state that DDI lookup, RAG, provenance, natural-language DDI explanation, and hybrid deterministic-plus-LLM architectures have prior art.
4. Distinguish RxCheck from ExDDI precisely: ExDDI explains learned DDI predictions; RxCheck allows prose only after a persisted stored-data finding. This difference is architectural scope, not proof of superiority.
5. State that a deterministic source-filled template is the missing baseline. Do not claim an LLM benefit without comparative and pharmacist evidence.
6. Cite the 2025 DDI-outcomes systematic review to reinforce that software architecture evidence is not clinical benefit.
7. Mention the 2026 SSRN hybrid DDI preprint only as contemporaneous, non-peer-reviewed overlap if the target journal accepts preprint citations.

## Required citation-use changes

- Use Saverno and Hussain only for prior-system variability and alert-design/fatigue context.
- Use RxNorm literature for terminology infrastructure; use Evidence 06, not reference 3, for RxCheck's measured 22/30 result.
- Separate statements about the published DDInter resource from claims about the recovered RxCheck source bundle. Never identify that bundle as DDInter 2.0.
- Replace the RAG arXiv URL with the official NeurIPS proceedings URL and add MedRAG for medical-RAG context.
- Use Singhal et al. only for general medical-LLM capability/limitation context, not DDI explanation performance.
- Retain governance, WHO, frugal-innovation, and FDA sources only with the explicit non-compliance/non-classification boundaries in `results.md`.
- Add access dates for WHO, FDA, DDInter terms, AHRQ, and standards pages.

## Suggested related-work synthesis

> Rule-based and knowledge-base DDI alerts long predate RxCheck, with documented variability in detection and persistent human-factors challenges. Expert recommendations already define concise alert content, including the drug pair, seriousness, mechanism, contextual factors, actions, and evidence, while contextualized DDI algorithms have used patient data to suppress low-relevance alerts. Separately, medical RAG and natural-language DDI explanation have been evaluated in research systems. RxCheck therefore does not introduce DDI checking, retrieval grounding, or generated DDI explanation. Its narrower contribution is an inspectable prototype in which stored interaction records create persisted findings and optional prose is requested only for an existing finding. The present study evaluates that authority allocation and selected persistence semantics, not the benefit of generation.

## Reference additions for v2

Use journal style and verify again at submission:

1. Payne TH, Hines LE, Chan RC, et al. Recommendations to improve the usability of drug-drug interaction clinical decision support alerts. *J Am Med Inform Assoc.* 2015;22(6):1243–1250. doi:10.1093/jamia/ocv011.
2. Chou E, Boyce RD, Balkan B, et al. Designing and evaluating contextualized drug-drug interaction algorithms. *JAMIA Open.* 2021;4(1):ooab023. doi:10.1093/jamiaopen/ooab023.
3. Sun Z, Li J, Pergola G, He Y. ExDDI: Explaining Drug-Drug Interaction Predictions with Natural Language. *Proc AAAI Conf Artif Intell.* 2025;39(24):25228–25236. doi:10.1609/aaai.v39i24.34709.
4. Xiong G, Jin Q, Lu Z, Zhang A. Benchmarking Retrieval-Augmented Generation for Medicine. *Findings of ACL 2024.* 2024:6233–6251. doi:10.18653/v1/2024.findings-acl.372.
5. Holbrook AM, Matos Silva J, Faruque JAY, Deng J, Schneider T, Jaffer A. Effect of electronic drug-drug interaction alerts on patient and clinician outcomes: a systematic review. *J Am Med Inform Assoc.* 2025;32(10):1617–1628. doi:10.1093/jamia/ocaf139.
6. HL7. FHIR Provenance resource. Use the target journal's preferred standard-version citation and state that RxCheck is not FHIR-conformant.

## Claims prohibited by this review

- first evidence-bounded explanation architecture;
- novel use of an LLM downstream of DDI rules;
- novel natural-language DDI explanation;
- provenance-complete or standards-conformant CDS;
- superior to templated alerts;
- improved comprehension, alert burden, decisions, safety, or outcomes;
- clinically grounded merely because context was supplied to the model.
