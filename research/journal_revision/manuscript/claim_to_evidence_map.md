# RxCheck Manuscript v2 Claim-to-Evidence Map

**Controlling synthesis:** `research/journal_revision/final_evidence_review.md`

**Status definitions:**

- **Supported:** direct evidence supports the exact bounded wording.
- **Partial:** one implementation/test component is supported but broader wording is not.
- **Remove:** the claim is contradicted, failed, not evaluated, or prohibited until new evidence exists.

This map controls `journal_ready_manuscript_v2.md`. “Supported” never implies clinical validity unless explicitly stated; no clinical claim is supported in this study.

| ID | Claim area | Status | Evidence | Permitted v2 wording or action | V2 location |
|---|---|---|---|---|---|
| C01 | Artifact identity and stack | Supported | Code inspection; review package | “FastAPI/React/PostgreSQL research prototype at the evaluated snapshot” | Abstract Methods; 3.1 |
| C02 | Deterministic finding authority | Supported | E01; orchestrator inspection | “On the evaluated core path, stored interaction rows create findings” | Abstract; 1; 4.1; 5.1 |
| C03 | Existing-finding explanation precondition | Supported | E01 scenario 23; endpoint inspection | “The explanation endpoint requires a persisted finding and cannot create a check finding through that endpoint” | Abstract; 1; 4.1 |
| C04 | Fresh-database architecture result | Supported | E01 | “26/26 in each of three repetitions; 78/78 synthetic scenario executions” | Abstract; 3.4; 4.1 |
| C05 | Exercised core service boundary | Supported | E01; E04 | “No Anthropic, OpenFDA, or RxNorm call occurred on the exercised core-check paths” | Abstract; 4.1; 4.4 |
| C06 | DDInter source-file identity | Supported | E03 | “Eight official manifest-identified files with recovered acquisition metadata and verified hashes” | 3.6; 4.3 |
| C07 | Raw source-bundle counts | Supported | E03 | “222,383 concatenated rows; 160,235 unique canonical identifier pairs; 62,148 cross-file duplicates” | Abstract; 4.3 |
| C08 | Local core correctness and latency | Supported | E04 | “720/720 expected-count calls; p95 2.586–245.124 ms in the recorded sequential warm-cache workloads” | Abstract; 3.7; 4.4 |
| C09 | Selected run/finding/review persistence | Supported | E05 passing criteria | List the exact passing snapshots, acknowledgment, escalation, and finding-level override behaviors | 3.8; 4.5 |
| C10 | Exact/brand/NDC frozen subsets | Supported | E06 | “Exact 8/8, brand 7/7, NDC 3/3 in the frozen set” | Abstract; 4.6 |
| C11 | Bibliographic identity | Supported | E07 | “All 15 prior references were verified; 9 direct and 6 bounded uses” | 4.7 |
| C12 | General medication normalization | Partial | E06 | Report 22/30 and all failure classes; do not state an overall accuracy estimate | Abstract; 3.9; 4.6; 5.4 |
| C13 | Explicit non-resolution | Partial | E01; E06 | Some paths preserve/exclude unresolved input; unknown and outage cases show the universal behavior is false | 3.2; 4.6; 5.4 |
| C14 | DDI/DFI/DDSI support | Partial | E01; code; E03 | Separate schema/query/synthetic capability from the DDI-only recovered importer and unvalidated coverage | 2.2; 3.2; 5.10 |
| C15 | Source provenance | Partial | E03; E05 | “Source-assertion model and partial provenance record”; identify missing semantic release, lineage, run source, and display snapshot | Abstract; 4.3; 4.5; 5.5 |
| C16 | Stored severity disagreement | Partial | E01 | “Flags stored severity-label differences”; do not imply independent-source or clinical disagreement | 3.2; 4.1 |
| C17 | Auditability/traceability | Partial | E05 | “Audit-oriented persistence of selected events”; report 10/15 and five failures | Abstract; 4.5; 5.5 |
| C18 | Reproducibility | Partial | E01; E03–E06 | “Locally reproducible protocols under recorded prerequisites”; list empty migration, unpinned package/setup, incomplete data reconstruction, and no independent rerun | 3.4; 5.10 |
| C19 | Output validation | Partial | E02 | Describe only JSON parse, required-key, outer list, and stored-name checks; report validator failure | Abstract; 3.5; 4.2 |
| C20 | Operational performance | Partial | E04 | Bounded core benchmark only; no SLA, throughput, concurrency, end-to-end, or production inference | 4.4; 5.6 |
| C21 | Cost-conscious design | Partial | E01; E04; literature | Optional paid generation is separated from core checking on tested paths; no cost or constrained-setting claim | 5.8 |
| C22 | Pharmacist orientation | Partial | Interface/code inspection | “Pharmacist-oriented”; no identity verification or pharmacist study | Abstract/Introduction; Limitations |
| C23 | “Strict RAG” | Remove | E02; E07 | Replace with “optional generated explanation supplied with structured finding context and heuristic label excerpts” | Throughout |
| C24 | “Schema-validated” explanation | Remove | E02 failed | Replace with limited custom checks and the negative 30-case result | Abstract; 4.2 |
| C25 | Safe, grounded, hallucination-resistant, injection-resistant prose | Remove | E02 failed; no live-model study | Explicitly state unsupported | Abstract; 5.2; Conclusion |
| C26 | Complete provenance or complete audit trail | Remove | E03/E05 failed | Use partial provenance and selected persistence wording | Abstract; 4.3; 4.5 |
| C27 | Imported DDInter 2.0 | Remove | E03 | Identify recovered files by manifest; semantic release unknown | 2.2; 4.3 |
| C28 | Novel/first DDI explanation or rule-plus-LLM architecture | Remove | E07; ExDDI; contemporaneous preprint | “Incremental, inspectable authority-boundary instantiation” | Abstract; 2.5; 4.7; Conclusion |
| C29 | Superior to deterministic templates or improved comprehension | Remove | No comparator/human study | Name deterministic template as required future comparator | 2.1; 2.5; 5.3 |
| C30 | Clinical accuracy, safety, usefulness, fatigue reduction, or outcomes | Remove | No clinical/human evidence; Holbrook context | Explicitly disclaim; no clinical performance inference | Warning; Abstract; 5.7; Conclusion |
| C31 | Frugal/affordable/low-resource suitability | Remove | No economic/setting evidence | “Cost-conscious service separation” only | 5.8 |
| C32 | HIPAA compliance, FDA non-device status, or deployment readiness | Remove | No legal/regulatory/security evaluation | State no determination was performed | 5.7; Declarations |
| C33 | Open-source reuse rights | Remove pending rights decision | No root license confirmed; DDInter separate terms | “Publicly visible source”; author must select/review licenses | Declarations |
| C34 | Reproducible configured-database totals | Remove | E03 failed reconciliation | Treat prior database profile as an unreconciled timestamped observation or omit totals | 4.3 |

## Numerical cross-checks

| Quantity | Controlling value | Evidence |
|---|---:|---|
| Architecture repetitions | 3 | E01 |
| Scenarios per repetition | 26 | E01 |
| Total passing scenario executions | 78/78 | E01 |
| Validator valid controls | 3/3 accepted | E02 |
| Validator invalid controlled rejects | 5/27 | E02 |
| Validator invalid false accepts | 15/27 | E02 |
| Validator invalid exceptions | 7/27 | E02 |
| DDInter concatenated rows | 222,383 | E03 |
| DDInter unique canonical identifier pairs | 160,235 | E03 |
| DDInter cross-file duplicates | 62,148 | E03 |
| Core measured calls | 720/720 correct | E04 |
| Workload p95 range | 2.586–245.124 ms | E04 |
| Traceability criteria | 10/15 pass | E05 |
| Normalization strict cases | 22/30 pass | E06 |
| Normalization exact/brand/NDC | 8/8; 7/7; 3/3 | E06 |
| Existing references verified | 15/15 | E07 |
| Updated readiness score | 61/100 | Final evidence review |
