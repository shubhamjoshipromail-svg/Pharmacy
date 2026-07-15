# Limitations

1. **No semantic release label.** The server's 2021 modification timestamp and the 2026 acquisition timestamp identify files, not a publisher-defined release version.
2. **No historical database access.** The audit intentionally avoided the configured database. It cannot inspect actual source-record IDs, alias mappings, import timestamps, or fixture tags beyond committed profiles/code.
3. **Mutable local files are external to Git.** Hashes freeze the observed bytes, but the source CSVs remain outside the repository and are not DOI-archived.
4. **Current official comparison is time-specific.** Byte identity was checked on July 15, 2026. A future download may differ without a changed filename.
5. **Acquisition timestamps come from local browser metadata.** They are strong local evidence but not an independent publisher receipt.
6. **Duplicate interpretation is structural.** Exact duplicates across category files are measured; their publisher-intended semantics were not independently documented.
7. **No terminology-quality assessment.** ID/name consistency within these files does not establish correct RxNorm mapping or clinical identity.
8. **No clinical validity assessment.** Interaction existence, severity, completeness, mechanism, management, and patient relevance were not evaluated.
9. **Database reconciliation uses committed summary counts.** The 12,473 excess calculation relies on the committed profile and identifiable evaluation fixtures, not row-level database records.
10. **Potential untagged fixtures or prior imports remain.** The repository cannot exclude them.
11. **License conclusions are not legal advice.** The official terms are recorded, but redistribution compatibility requires author/institutional review.
