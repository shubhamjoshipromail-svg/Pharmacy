# RxCheck Data And Source Profile

Generated: `2026-06-09T19:59:39.927169+00:00`

> This is a descriptive profile of the configured prototype database. It is not clinical validation, a completeness assessment, or a gold-standard comparison.

## Core Counts

| Measure | Count |
|---|---:|
| Interactions | 152,416 |
| Source assertions | 172,714 |
| Drugs | 1,967 |
| Drug aliases | 1,934 |
| Unresolved drug entries | 71 |
| Drug external IDs | 5 |
| Research-fixture interactions identifiable by assertion payload | 5 |
| Research-fixture assertions | 6 |

Research fixtures are counted explicitly because formative evaluation runs write synthetic rows to the configured database. Aggregate totals above include those rows.

## Interaction Types

| Type | Rows |
|---|---:|
| DDI | 152,413 |
| DDSI | 2 |
| DFI | 1 |

- DDI rows: **152,413**
- DFI rows: **1**
- DDSI rows: **2**

## Assertion Severity And Sources

| Severity | Assertions |
|---|---:|
| major | 28,605 |
| minor | 8,323 |
| moderate | 105,973 |
| unknown | 29,813 |

| Source | Assertions |
|---|---:|
| DDInter | 172,713 |
| manual | 1 |

## Assertion Structure

- Interactions with more than one distinct asserted severity: **174**
- Average assertions per interaction: **1.1332**
- Maximum assertions on one interaction: **9**

A source conflict means that stored assertions for one interaction contain more than one severity value. It does not establish which source is correct.

## Top Hub Drugs

| Rank | RxCUI | Preferred Name | Interaction Count |
|---:|---|---|---:|
| 1 | 3264 | dexamethasone | 896 |
| 2 | 11289 | Warfarin | 853 |
| 3 | 42316 | Tacrolimus | 845 |
| 4 | 8745 | Promethazine | 817 |
| 5 | 21212 | Clarithromycin | 805 |
| 6 | 3008 | cyclosporine | 801 |
| 7 | 8640 | Prednisone | 787 |
| 8 | 4450 | Fluconazole | 775 |
| 9 | 10432 | Thalidomide | 765 |
| 10 | 6851 | Methotrexate | 762 |

These values are graph-degree counts in the stored interaction table, not clinical risk scores.

## DDInter Import Support

The current bulk importer names these files:

- `ddinter_downloads_code_A.csv`
- `ddinter_downloads_code_B.csv`
- `ddinter_downloads_code_D.csv`
- `ddinter_downloads_code_H.csv`
- `ddinter_downloads_code_L.csv`
- `ddinter_downloads_code_P.csv`
- `ddinter_downloads_code_R.csv`
- `ddinter_downloads_code_V.csv`

Current importer limitations:

- The current importer is tailored to eight locally named DDInter CSV partitions.
- It imports DDI pairs and severity labels but the listed files do not supply mechanism or management text.
- Drug-name resolution depends on aliases and preferred names already present in the database.
- Unresolved names are quarantined rather than imported as verified interactions.
- This profile does not establish completeness, clinical validity, or equivalence to the full DDInter release.
- Source coverage checks are append-only in the current bulk importer and are not profiled as unique evidence records.

## Manuscript-Safe Claims

- The configured prototype database contains the reported counts at the recorded generation time.
- The repository includes a bulk importer for eight named DDInter CSV partitions with DDI severity mapping.
- Interaction records can retain one or more source assertions, enabling descriptive source-conflict detection.
- Hub counts are database-derived interaction-degree counts and are not a measure of clinical risk.

## Claims Not Supported

- The database provides complete DDI coverage.
- The imported interactions are clinically validated by this profiling procedure.
- Hub ranking identifies the most dangerous drugs.
- The source-conflict count measures clinical disagreement quality or correctness.
- The database profile demonstrates FDA clearance, HIPAA compliance, or clinical effectiveness.
