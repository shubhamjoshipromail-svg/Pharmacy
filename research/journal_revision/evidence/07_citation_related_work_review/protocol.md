# Protocol

## Objective

Verify the identity and claim fit of every current manuscript reference, then determine whether the proposed contribution remains defensible against the closest related work.

## Review type

Targeted citation audit and structured related-work review. This is not a systematic review, scoping review, or meta-analysis.

Source discovery began before this protocol file was written. The method is therefore documented for reproducibility but was not prospectively registered.

## Scope and cutoff

- Manuscript source: `research/journal_revision/05_journal_ready_manuscript.md`
- Existing references: 1–15
- Related-work cutoff: sources available on 2026-07-14
- Preferred evidence: publisher/proceedings records, PubMed, official agencies, official standards, and official data-provider pages
- Preprints: permitted only to identify contemporaneous overlap; not treated as equivalent to peer-reviewed evidence

## Prespecified comparison categories

1. rule- or knowledge-base-based DDI CDS;
2. DDI alert presentation and a deterministic/template explanation baseline;
3. patient-contextualized DDI algorithms;
4. source and artifact provenance in CDS;
5. medical RAG or grounded LLM systems; and
6. natural-language DDI explanation systems.

## Citation-audit fields

For each existing reference:

- title, authorship, outlet/issuing organization, year, volume/issue/pages or report identity;
- DOI, ISBN, or official URL where applicable;
- source authority;
- the manuscript claim for which it is used;
- claim-fit classification; and
- required manuscript action.

## Claim-fit definitions

- **Direct:** the source directly supports the bounded statement as written or with only copyediting.
- **Bounded/context-only:** the source is relevant, but it cannot support a system-specific, clinical, causal, regulatory, or novelty inference.
- **Insufficient:** the cited source does not establish the manuscript proposition and another source or removal is required.
- **Contradicted:** the source conflicts with the manuscript proposition.

## Success and failure criteria

The review is complete if:

- all 15 current references have a verified identity or are flagged for removal;
- every current citation use has a claim-fit classification;
- all six comparison categories are represented; and
- a conservative novelty statement and exact manuscript actions are recorded.

A broad novelty claim fails if a prior source already demonstrates the same general method class, even if implementation details differ. Absence of an identical product does not establish novelty.

## Reproducibility record

- `raw_results/source_inventory.tsv` contains normalized source and claim-fit data.
- `raw_results/search_log.md` records the bounded searches and official pages checked.
- URLs were last checked on 2026-07-14; live content can change.

## Safety and preservation

This review is read-only with respect to the application, original paper, and previously created review materials. It creates only new Evidence 07 files and tracker entries.
