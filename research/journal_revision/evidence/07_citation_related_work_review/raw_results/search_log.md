# Search and Source-Check Log

**Date:** 2026-07-14

**Purpose:** bounded citation verification and related-work comparison, not exhaustive evidence synthesis

## Existing-reference checks

- DOI metadata queried through Crossref for references 1–5, 7–8, 10–12 and added DOI-bearing sources.
- Publisher/proceedings pages checked for DDInter, DDInter 2.0, RAG, Med-PaLM, responsible AI-CDS, and the JAMIA sources.
- PubMed checked for Saverno, RxNorm, and frugal-innovation records.
- WHO publication pages checked for the 2021 AI ethics guidance and 2019 digital-interventions guideline.
- FDA final-guidance page checked; it states January 2026 and content current 2026-01-29.
- DDInter terms and Evidence 03 were used for the provider's license/incompleteness statements.
- The final Hevner PDF prints pages 75–105; Crossref reports 75–106. The publisher artifact was treated as controlling.

## Targeted related-work queries

Representative queries:

- `drug-drug interaction clinical decision support alert usability recommendations`
- `contextualized drug-drug interaction algorithms patient context`
- `ExDDI explaining drug-drug interaction predictions natural language`
- `benchmarking retrieval-augmented generation for medicine`
- `drug interaction alert templated explanation clinical decision support`
- `clinical decision support provenance FHIR CDS Connect`
- `rule-based DDI LLM-assisted explanation architecture`
- `effect of electronic drug-drug interaction alerts patient clinician outcomes systematic review`

## Included comparison records

- Payne et al., JAMIA 2015, DDI alert usability recommendations.
- Chou et al., JAMIA Open 2021, contextualized DDI algorithms.
- Sun et al., AAAI 2025, ExDDI.
- Xiong et al., Findings of ACL 2024, MedRAG/MIRAGE.
- HL7 FHIR Provenance and AHRQ CDS Connect official pages.
- Holbrook et al., JAMIA 2025, DDI alert outcomes systematic review.
- Sre and Sudhakar, SSRN 2026, retained only as non-peer-reviewed contemporaneous overlap.

## Exclusion choices

- Generic DDI prediction papers without an explanation or CDS relationship were not added.
- General clinical LLM papers were not added when MedRAG, ExDDI, or the existing governance sources answered the comparison question more directly.
- Low-detail aggregator, vendor-marketing, Wikipedia, Reddit, and non-primary summaries were not used as evidence.
- Recent unrelated agentic-CDS work was not added because it would broaden the review without changing the RxCheck novelty conclusion.
