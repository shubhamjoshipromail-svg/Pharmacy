# Protocol: DDInter Source-Provenance Recovery Audit

## Research question

Can the source identity, acquisition history, integrity, raw-data profile, licensing context, and raw-to-database import accounting underlying the RxCheck DDInter claims be reconstructed from the repository, Git history, importer-referenced local files, and current official download artifacts without connecting to the configured database?

## Why this task is publication-relevant

All prior reviews identify exact DDInter versioning, checksums, import accounting, fixture separation, and licensing as submission-critical gaps. Evidence 01 reproduced synthetic architecture behavior but did not reconstruct the real interaction data. A source-provenance audit is therefore the highest-value remaining reproducibility task that can be completed without clinical partners or the unsafe database.

## Objective

Recover and separately classify:

1. What is directly verified.
2. What is strongly linked but lacks a semantic release label.
3. What remains unrecoverable because mapping state, quarantine output, or import logs were not preserved.

## Inputs

- Current repository and all reachable Git refs/objects.
- `scripts/import_ddinter.py` and its history.
- `research/data_profile.json` and related committed research artifacts.
- The importer's read-only local source directory: `/Users/shubhamjoshi/Desktop/pharmacy/ddinter/`.
- A temporary July 15, 2026 download of the same eight files from the official DDInter URLs, stored outside the repository for byte comparison.
- Official DDInter download and terms pages.

The configured Postgres database is not contacted.

## Required source files

- `ddinter_downloads_code_A.csv`
- `ddinter_downloads_code_B.csv`
- `ddinter_downloads_code_D.csv`
- `ddinter_downloads_code_H.csv`
- `ddinter_downloads_code_L.csv`
- `ddinter_downloads_code_P.csv`
- `ddinter_downloads_code_R.csv`
- `ddinter_downloads_code_V.csv`

Expected columns: `DDInterID_A`, `Drug_A`, `DDInterID_B`, `Drug_B`, `Level`.

## Procedure

1. Inventory every current and historical Git path relevant to DDInter, data files, importers, profiles, logs, and quarantine outputs.
2. Confirm whether the eight real source files were ever committed.
3. Follow the importer-recorded local source directory in read-only mode.
4. For each source file, record byte size, SHA-256, filesystem birth/modification timestamps, extended-attribute origin URLs, browser quarantine acquisition timestamp, header, row count, empty values, severity distribution, duplicates, and identifier/name consistency.
5. Profile the combined source bundle for exact duplicates, distinct pairs, pair-level severity differences, self-pairs, distinct drug IDs/names, and conflicting ID-to-name mappings.
6. Compare each local file byte-for-byte with a fresh file downloaded from its official DDInter URL on July 15, 2026.
7. Record official HTTP metadata, including content length, last-modified value, and ETag.
8. Compare source-bundle counts with the committed June 9, 2026 database profile without treating unmatched totals as a known quarantine count.
9. Determine whether exact semantic release/version, alias-map snapshot, resolved-row count, quarantine rows, inserted-row counts, and fixture-adjusted database counts can be reconstructed.
10. Save raw machine-readable inventory, HTTP metadata, live-comparison log, and conclusions without copying the licensed CSV contents into the repository.

## Metrics and checks

- Presence and hash coverage of all eight files.
- Byte identity with the official current download.
- Acquisition timestamp/origin metadata coverage.
- Per-file and combined row counts.
- Missing-cell counts and allowed severity values.
- Exact duplicate rows and duplicate/source pair counts.
- Distinct drug identifiers and ID-to-name conflicts.
- Current/historical Git presence of raw files, import logs, quarantine artifacts, mapping snapshots, or database exports.
- Availability of exact semantic release label.
- Availability of complete raw→resolved→quarantined→canonical-interaction→assertion accounting.

## Pass/fail criteria

The full provenance task passes only if all of the following are available and directly supported:

1. Exact semantic DDInter release/version and acquisition date.
2. All source filenames and SHA-256 checksums.
3. Official source origin and license/terms.
4. Complete raw row counts.
5. Exact resolved and quarantined row counts with retained quarantine reasons/rows.
6. Exact inserted canonical-interaction and assertion counts, separated from pre-existing data and research fixtures.
7. Reproducible mapping state or snapshot sufficient to repeat resolution.

If source identity is recovered but one or more transformation-lineage requirements are missing, the result is **PARTIAL / NOT COMPLETE**, not a pass.

## Reproduction command

```bash
PYTHON_BIN=/path/to/python \
"$PYTHON_BIN" research/journal_revision/evidence/03_ddinter_provenance_recovery/scripts/audit_ddinter_provenance.py \
  --source-dir /path/to/local/ddinter \
  --live-verify-dir /path/to/fresh/official/downloads \
  --output research/journal_revision/evidence/03_ddinter_provenance_recovery/raw_results/provenance_inventory.json
```

## Prespecified limitations

- Filesystem and quarantine timestamps support acquisition timing but are not a publisher-issued release identifier.
- Byte identity with files currently served proves file identity at two observed times, not a semantic version label.
- Current official pages may change; their retrieval date must be recorded.
- Raw source profiling cannot reconstruct database-dependent alias resolution without the historical mapping state.
- No clinical validity or completeness assessment is performed.
- DDInter data are not copied into the repository because redistribution/licensing implications require author review.
