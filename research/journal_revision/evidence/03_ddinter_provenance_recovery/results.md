# Results: DDInter Source-Provenance Recovery Audit

## Overall assessment

**PARTIAL / NOT COMPLETE.** Source origin, acquisition timing, checksums, raw structure, and current official byte identity were recovered. Exact semantic release identity and raw-to-database transformation accounting were not.

## Execution context

- Audit date: July 15, 2026 UTC.
- Repository HEAD: `8730bb7e9ae54088e6e9ff622ebfa047628e7aa4`.
- Most recent commit affecting the importer/profile paths: `5038106ada9c66fb2cd1fc0e33c8322553b4d699`.
- Database connections: 0.
- Source data copied into repository: No.
- Machine-readable audit: `raw_results/provenance_inventory.json`.
- Source manifest: `raw_results/source_manifest.tsv`.

## Dataset and intended grain

The source bundle contains five-column DDI association records: `DDInterID_A`, `Drug_A`, `DDInterID_B`, `Drug_B`, and `Level`. The eight downloads group interactions by therapeutic category and overlap. Concatenated row count is therefore an ingestion-volume measure; the directly supported unique source-record grain is the canonical DDInter identifier pair.

## Checks performed

1. Current-tree and all-ref Git object inventory.
2. Importer history and expected-file comparison.
3. Local source presence, size, SHA-256, header, timestamps, and extended attributes.
4. Fresh official download and byte-for-byte comparison.
5. Combined/per-file completeness, duplicate, validity, pair, severity, and ID/name consistency checks.
6. Comparison with the committed June 9 database profile.
7. Search for alias-map snapshots, quarantine outputs, import logs, raw database exports, tags, and source-version labels.
8. Official download-page and terms review.

## Source manifest

| File | Rows | Bytes | SHA-256 |
|---|---:|---:|---|
| A | 56,367 | 3,343,434 | `a22ca451d2b755ca2331886f7e00540c86f555f9f55704a59a19c691251f52e0` |
| B | 15,140 | 867,726 | `76de5115a55587f0e822e1096b684fd3ddde058fbefcbb19896df58820ace130` |
| D | 25,681 | 1,520,704 | `c0627ec39965dbe27829e4934cd20d71eb079f4e373287678737bba9423a306a` |
| H | 11,727 | 705,088 | `f0f925f0ba1ee68c4668d3e7a6732719b34623b22a0f5d017f9090e59f63c88e` |
| L | 65,389 | 3,885,702 | `f54f4486cc00344f8c86508c31c2ca3fad6d1d37ec3af5bcf609b4bbda5507ef` |
| P | 5,492 | 317,460 | `83f8c0edb20d09ef29b8500b48f9623e208379525688ade9e70a7df2d8749d55` |
| R | 30,563 | 1,793,766 | `1c39c3d4a6e41659b7a988538d7f363867592abc6f41a815de8746f6e2150574` |
| V | 12,024 | 700,777 | `353973fb300453946aea95733e8fb52338e4b59426d2ce6ca318363d4f84f10a` |

The acquisition timestamps recovered from macOS quarantine metadata fall between `2026-04-16T16:43:26Z` and `2026-04-16T16:44:09Z`. Every file records its corresponding `https://ddinter.scbdd.com/static/media/download/…` URL and the DDInter download page.

Fresh copies downloaded on July 15, 2026 had the same SHA-256 values. HTTP responses reported content lengths equal to the local sizes, `Last-Modified` timestamps on June 26, 2021, and stable ETags recorded in `official_http_headers.txt`.

## Raw data-quality findings

### Finding 1 — Cross-file duplication

- **Severity:** Medium for source profiling; High if concatenated rows are reported as unique interactions.
- **Evidence:** 222,383 concatenated rows, 160,235 unique exact rows, and 62,148 duplicates (27.9% of concatenated rows). No file contains an internal duplicate; duplication occurs across files.
- **Impact:** Raw row counts and severity distributions overstate unique source records if partitions are naively concatenated. The importer does concatenate without a pre-deduplication step.
- **Likely cause:** Therapeutic-category files overlap when an interaction belongs in more than one category.
- **Remediation:** Deduplicate by a documented source-record key before transformation, retain per-file membership separately, and report both ingestion rows and unique records.

### Finding 2 — Required fields and identifier/name consistency are complete in the recovered bundle

- **Severity:** No defect detected for the checked dimensions.
- **Evidence:** Zero empty values in all five columns, zero self-pairs, 1,939 distinct drug IDs, and zero IDs associated with more than one name.
- **Impact:** The raw bundle is structurally consistent for the importer-required fields.
- **Limitation:** This does not validate clinical correctness or terminology mapping to RxNorm.

### Finding 3 — Severity values are internally consistent at source-pair grain

- **Severity:** No pair-conflict defect detected; descriptive caveat remains.
- **Evidence:** Major 33,896; moderate 130,367; minor 10,938; unknown 47,182 across concatenated rows. No canonical DDInter ID pair has more than one severity label. All source values fall within these four observed categories.
- **Impact:** Cross-file duplicates do not create conflicting source severity labels, but concatenated severity counts include the same records multiple times.

### Finding 4 — Semantic release/version is absent

- **Severity:** High for publication reproducibility.
- **Evidence:** No Git tag; no version in filenames, headers, origin URLs, source content schema, or official download page. Current HTTP metadata identifies file modification dates, not a semantic DDInter release.
- **Impact:** The files cannot be defensibly labeled “DDInter 2.0” or assigned a release number from repository evidence.
- **Remediation:** Identify the publisher-defined release through author/source correspondence or use a manifest-based description: official URL, acquisition date, server last-modified value, and SHA-256.

### Finding 5 — Raw-to-database lineage is not reconstructable

- **Severity:** Critical for treating the committed database totals as a reproducible import result.
- **Evidence:** Git contains no real source CSV, alias-map snapshot, persisted quarantine rows, complete import log, or database export. The importer resolves names against mutable database state and prints quarantine counts without saving them.
- **Impact:** Exact resolved, quarantined, collapsed, inserted, and pre-existing row counts cannot be recovered. The June database profile remains a timestamped observation, not a rebuildable result.
- **Remediation:** Add an immutable import run manifest, input hashes, mapping snapshot/hash, persisted quarantine file, deduplication accounting, before/after counts, fixture flag/run ID, and database/schema revision.

### Finding 6 — Database assertion total does not reconcile to the recovered unique source records

- **Severity:** High.
- **Evidence:** The recovered bundle has 160,235 unique exact source rows/pairs. The committed profile reports 172,713 DDInter assertions. Historical evaluator inspection accounts for five tagged DDInter evaluation assertions, leaving 172,708 non-identified-fixture DDInter assertions—12,473 above the recovered unique source-record count.
- **Impact:** A single stable-mapping import of the recovered unique source records does not explain the profile. The exact database population and repetition/mapping history are unknown.
- **Likely causes:** One or more of prior/unrecorded source records, alias remapping across import runs, repeated source records attached to different canonical interactions, or untagged fixtures/manual data. The available evidence cannot select among them.
- **Remediation:** Do not derive quarantine counts by subtraction. Rebuild in a fresh database from a frozen mapping snapshot and compare source-record IDs explicitly.

## Importer-specific implications

- Duplicate interaction/assertion attempts can be suppressed by database conflicts when mapping is stable.
- Coverage-check rows are append-only for every resolved concatenated row and have no deduplication constraint; cross-file duplicates and repeated imports can inflate this table.
- `quarantine_rows` is in memory only and is lost after the process exits.
- The importer prints attempted counts and aggregate database totals but no run ID, before-state, inserted-vs-conflicted count, input hashes, or durable report.

## License and source terms

The [official DDInter terms](https://ddinter.scbdd.com/terms/) state that data are available under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International and warn that the database is incomplete and may contain errors. The [official download page](https://ddinter.scbdd.com/download/) lists the same eight filenames and sizes. This audit records metadata and does not redistribute source rows. Author/legal review remains necessary before archiving or redistributing a derived data package.

## Conclusion

Source integrity is now substantially documented: the exact eight-file bundle, acquisition timing, hashes, raw profile, official origin, and current byte identity are known. Full research reproducibility remains incomplete because the publisher release label and transformation lineage are absent. The manuscript should identify the bundle by manifest rather than semantic version and must treat database counts as unreconciled observations.
