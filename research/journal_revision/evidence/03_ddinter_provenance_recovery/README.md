# Evidence 03: DDInter Source-Provenance Recovery

## Status

**PARTIAL — source bundle recovered and verified; full transformation lineage failed.**

The eight DDInter CSV files referenced by the importer were located in the read-only local directory recorded by the code. Their official origin URLs and April 16, 2026 acquisition timestamps were recovered from browser quarantine metadata. All eight local files were byte-identical to fresh copies downloaded from the official DDInter site on July 15, 2026.

The audit did not recover a semantic release/version label, historical drug-alias mapping snapshot, persisted quarantine rows, complete import log, or a reproducible reconciliation from raw rows to the June database profile. The full provenance pass criterion was therefore not met.

## Dataset and grain

Each CSV row contains two DDInter drug identifiers/names and one severity level for a DDI association. The eight files are therapeutic-category downloads, not mutually exclusive partitions: 62,148 rows are exact cross-file duplicates. The appropriate recovered source-record grain is therefore the unique DDInter identifier pair, not the concatenated row count.

## Recovered source evidence

- Eight expected files present.
- Five expected columns present in every file.
- SHA-256 manifest created.
- Official download URLs recovered for every file.
- Acquisition timestamps recovered for every file: April 16, 2026, 16:43–16:44 UTC.
- Fresh official July 15, 2026 copies are byte-identical.
- Official HTTP sizes match the local files.
- Official server `Last-Modified` values are June 26, 2021.
- [DDInter terms](https://ddinter.scbdd.com/terms/) identify the data license as CC BY-NC-SA 4.0 and caution that the database is incomplete and may contain errors.

The [official download page](https://ddinter.scbdd.com/download/), URLs, filenames, CSV headers, and files do not expose a semantic release label. The recovered data should therefore be identified by acquisition date, official URL, and SHA-256 manifest rather than called “DDInter 2.0” or assigned an inferred version.

## Raw source profile

| Metric | Result |
|---|---:|
| Concatenated rows | 222,383 |
| Unique exact rows | 160,235 |
| Exact duplicate rows | 62,148 |
| Distinct canonical DDInter ID pairs | 160,235 |
| Rows duplicated within an individual file | 0 |
| Pairs with multiple severity labels | 0 |
| Distinct DDInter drug IDs | 1,939 |
| Drug IDs mapped to multiple names | 0 |
| Empty required cells | 0 |
| Self-pair rows | 0 |

Severity values across concatenated rows were 33,896 major, 130,367 moderate, 10,938 minor, and 47,182 unknown. Duplicate rows preserve the same severity; these counts should not be treated as unique-interaction distributions until cross-file duplicates are removed.

## Why full lineage failed

The real source files were never committed; Git history contains only `scripts/ddinter_synthetic.csv`. No historical alias/preferred-name mapping snapshot, persisted quarantine artifact, complete import execution log, or database export was found. The importer reads live database mappings, retains quarantine rows only in memory, attempts all concatenated rows, suppresses some duplicate writes through database conflicts, and appends coverage-check rows without deduplication.

The committed June 9, 2026 profile reported 172,713 DDInter assertions. Git history identifies five DDInter assertions created by the two recorded evaluation runs, leaving 172,708 non-identified-fixture DDInter assertions—12,473 more than the recovered bundle's 160,235 unique source records. This discrepancy can arise from unrecorded prior data, changed mapping state, repeated imports mapped to different canonical interactions, or untagged fixtures; the repository cannot distinguish among them.

## Publication conclusion

The paper may now report a precise source manifest and raw-file profile, but it must not present the configured database counts as a reproducible import result. Source identity is strongly established; source-to-database lineage remains incomplete.

## Evidence map

- `protocol.md` — question, criteria, and method.
- `scripts/audit_ddinter_provenance.py` — streaming source/Git/profile audit.
- `raw_results/provenance_inventory.json` — complete machine-readable profile.
- `raw_results/source_manifest.tsv` — filenames, sizes, rows, hashes, acquisition times, and origin URLs.
- `raw_results/official_http_headers.txt` — retrieval-time HTTP size, last-modified, and ETag evidence.
- `logs/independent_shell_verification.log` — independent line counts, hashes, and byte comparisons.
- `results.md` — data-quality and lineage findings.
- `limitations.md` — residual uncertainty.
- `manuscript_notes.md` — exact claim changes.

The licensed source CSV contents are not copied into this repository.
