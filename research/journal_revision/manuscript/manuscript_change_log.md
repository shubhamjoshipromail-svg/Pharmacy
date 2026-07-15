# Manuscript v2 Change Log

**Source materials treated as read-only:**

- Original paper: `paper/rxcheck_manuscript_0.1v.md`
- Prior revision draft: `research/journal_revision/05_journal_ready_manuscript.md`
- Review and evidence materials: `research/journal_revision/01_*.md` through `final_evidence_review.md` and Evidence 01–07

**New manuscript:** `research/journal_revision/manuscript/journal_ready_manuscript_v2.md`

**Revision date:** 2026-07-15

## Revision purpose

The prior draft was written before the feasible evidence cycle. V2 replaces historical-only and unexecuted statements with Evidence 01–07, reports negative results without dilution, narrows novelty, and retains explicit submission blockers. No original source or prior manuscript was edited.

## Major structural changes

| V2 section | Change from prior draft | Evidence basis |
|---|---|---|
| Title | Replaced broad “evidence-bounded architecture” title with explicit deterministic finding-authority boundary and prototype/formative status | E01, E07, final review |
| Abstract | Replaced historical-only results with all executed principal results and failed contracts | E01–E07 |
| Introduction | Reframed contribution as authority allocation and incremental case study, not new DDI explanation/RAG | E07 |
| Related Work | Removed unresolved placeholder; added conventional alerts, contextual algorithms, outcomes, ExDDI, MedRAG, provenance, and template baseline | E07 |
| Methods | Added seven evidence protocols, environments, pass/fail rules, safety guards, and preservation method | E01–E07 |
| Results | Added repeated architecture, validator, provenance, latency, traceability, normalization, and novelty results with exact denominators | E01–E07 |
| Discussion | Centered the distinction between a passed authority boundary and failed adjacent controls | Final review |
| Safety/Governance | Elevated exposed credential, unauthenticated identity, and non-regulatory status to a dedicated discussion | E05; prior reviews; final review |
| Limitations | Added construct, internal, external, reproducibility, literature, and clinical/human-factors validity threats | E01–E07 |
| Declarations | Added explicit author-supplied placeholders and AI-assistance disclosure requirement | Final review |
| References | Replaced RAG arXiv link, verified existing sources, and added closest related work | E07 |

## Quantitative evidence added

- Three fresh-database architecture repetitions: 26/26 each, 78/78 total.
- Validator audit: 3/3 valid accepted; 5/27 invalid controlled-rejected; 15 false accepts; 7 exceptions.
- DDInter bundle: 222,383 concatenated rows; 160,235 unique canonical identifier pairs; 62,148 cross-file duplicates.
- Core benchmark: 720/720 correct calls; workload p95 2.586–245.124 ms.
- Traceability audit: 10/15 criteria passed.
- Normalization: 22/30 strict cases; exact 8/8, brand 7/7, NDC 3/3; all four multi-ingredient cases failed.
- Citation audit: 15/15 identities verified; 9 direct and 6 bounded uses.
- Updated publication-readiness score: 61/100.

## Claims removed or materially narrowed

| Prior claim or implication | V2 treatment |
|---|---|
| Strict RAG | Replaced with optional generated explanation using selected structured context and heuristic label excerpts |
| Schema-validated explanation | Replaced with limited custom checks and failed validator result |
| Universal normalize-or-reject behavior | Replaced with 22/30 benchmark and concrete unsafe/uncontrolled failure modes |
| Full provenance/reproducible import | Replaced with verified source manifest and failed transformation-lineage result |
| Complete audit trail | Replaced with selected audit-oriented persistence and 10/15 traceability result |
| DDInter 2.0 imported data | Removed; recovered bundle is identified by manifest only |
| Novel generated DDI explanation/hybrid architecture | Removed; contribution described as incremental authority-boundary instantiation |
| LLM benefit over templates | Removed; deterministic source-filled template named as missing comparator |
| Frugal or affordable system | Replaced with cost-conscious service separation |
| Clinical safety, accuracy, workflow benefit, fatigue reduction, outcomes, regulatory status, or deployment readiness | Explicitly disclaimed |
| Open-source reuse | Replaced with publicly visible source pending root license decision |

## New references and comparisons

- Payne et al. DDI alert usability recommendations.
- Chou et al. contextualized DDI algorithms.
- Holbrook et al. 2025 DDI alert outcomes systematic review.
- ExDDI natural-language DDI prediction explanations.
- MedRAG/MIRAGE medical RAG benchmark.
- FHIR Provenance and AHRQ CDS Connect.
- A contemporaneous 2026 hybrid DDI preprint, explicitly labeled non-peer-reviewed.

## New supporting figures

- `figures/authority_boundary_v2.mmd` shows authoritative and non-authoritative paths plus observed normalization/validation failures.
- `figures/evidence_flow_v2.mmd` shows Evidence 01–07 feeding the synthesis and claim classifications.

These Mermaid sources still require journal-format rendering, visual QA, accessible alt text, and final captions.

## Intentional unresolved placeholders

V2 does not invent unavailable author information. The following remain clearly marked:

- authors, affiliations, ORCIDs, and corresponding author;
- institutional ethics determination;
- competing interests, funding, CRediT contributions, and acknowledgments;
- root software license and rights review;
- target-journal AI-assistance disclosure wording.

## Preservation verification required at handoff

- Original paper Git object must remain `cd5c4ab332461544a1f083bfcfd65fd60b2b49e4`.
- `research/journal_revision/05_journal_ready_manuscript.md` must have no diff.
- Application source and historical research outputs must have no diff.
