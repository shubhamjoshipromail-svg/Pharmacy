# Manuscript Notes From Evidence 03

## Required data-source wording

Use a manifest-based description rather than an inferred semantic version:

> The analyzed source bundle comprised eight five-column DDI CSV files downloaded from the official DDInter site on April 16, 2026. The files were identified by URL and SHA-256 manifest and were byte-identical to copies served on July 15, 2026. The official server reported June 26, 2021 last-modified timestamps, but the files and download page exposed no semantic release label.

Do not call the imported bundle “DDInter 2.0.” The recovered files contain DDI pairs and severity only and are the same legacy-named downloads listed on the official site.

## Required raw-data result

Report:

> The eight files contained 222,383 concatenated rows but 160,235 unique exact DDInter ID pairs; 62,148 rows (27.9%) were exact cross-file duplicates. No required cells were empty, no within-file duplicates or self-pairs were detected, and no DDInter ID was associated with multiple names in the recovered files.

If reporting severity, distinguish concatenated from unique-record counts. The current profile records concatenated counts and duplicates preserve the same label; a unique-record severity table should be generated before final submission if needed.

## Required database-profile caveat

Use:

> The June 9, 2026 configured-database profile is a timestamped observation rather than a reproducible import total. Historical alias mappings, quarantine rows, and import logs were not preserved, and the assertion count could not be reconciled to the recovered source-record manifest.

Add the observed discrepancy:

> The profile reported 172,713 DDInter assertions. Five were identifiable DDInter evaluation fixtures, leaving 172,708 non-identified-fixture assertions, 12,473 more than the recovered bundle's 160,235 unique source records. Available artifacts could not determine whether this difference reflected prior source data, changed mappings across runs, repeated imports attached to different interactions, or untagged fixtures.

Do not label `222,383 - database assertions` as quarantine count. Cross-file duplicates, mapping collapse, mutable alias state, pre-existing rows, and repeated imports make that subtraction invalid.

## Methods additions

- Add all eight filenames, official origin, acquisition date, and manifest location.
- State that source rows have five columns and do not provide mechanism/management text.
- Describe cross-file deduplication as a required preprocessing/accounting step.
- Distinguish attempted rows, unique source records, resolved rows, canonical interactions, assertions, conflicts, and coverage-check rows.
- State that the current importer does not persist quarantine rows or run manifests.

## License/data-availability additions

- Cite the official DDInter terms and CC BY-NC-SA 4.0 license.
- State that the audit repository retains metadata/hashes, not the source CSV contents.
- Do not promise redistribution or a DOI data archive until license compatibility is reviewed.

## Claim-status changes

| Claim | Status after Evidence 03 |
|---|---|
| The importer references eight named official DDInter DDI files | Fully supported |
| The observed local files came from official DDInter URLs | Fully supported by extended metadata and live comparison |
| File acquisition date and SHA-256 are known | Fully supported |
| The exact semantic DDInter release is known | Not supported |
| The files are DDInter 2.0 data | Not supported |
| Raw bundle structure/counts are reproducible | Supported for the recovered manifest |
| Database import counts are reproducible from the bundle | Not supported |
| Quarantine count is known | Not supported |
| The June database profile equals one clean import | Not supported |
| Source data are clinically complete/correct | Not supported |

## Discussion implication

Treat this as both a recovery success and a reproducibility warning. File-level provenance can sometimes be reconstructed from local download metadata and hashes, but database-level provenance requires deliberate import-run artifacts. The duplicate overlap and unreconciled assertion count justify explicit source/run manifests in future versions.
