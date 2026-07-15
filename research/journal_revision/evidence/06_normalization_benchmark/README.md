# Evidence 06: Medication-Normalization Benchmark

## Status

**FAIL — 22/30 strict cases passed (73.3%); eight failed.**

All 30 frozen reference cases first verified against the official RxNorm `06-Jul-2026` service (API `3.1.353`). The unchanged RxCheck normalizer then passed every tested exact ingredient name (8/8), brand name (7/7), and DailyMed-backed NDC (3/3), plus one low-confidence candidate case and the whitespace-only placeholder case.

The failures are publication-relevant:

- one misspelling auto-resolved to an inactive/unresolvable numeric concept instead of aspirin;
- a second misspelling reached the correct ingredient but was mislabeled `matched_exact`;
- all four multi-ingredient products were reduced to only the first returned ingredient;
- a deliberately constructed non-drug token auto-resolved to an unresolvable numeric concept instead of remaining visible as unmatched; and
- an injected RxNorm connection failure escaped as `ConnectError` with no placeholder or unresolved record.

## Independent reference basis

Expected mappings were frozen before application execution and separately rechecked through official RxNorm endpoints. The [NLM RxNorm release page](https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html) records the July 6, 2026 monthly release. NDC cases also use official DailyMed labels for [acetaminophen](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=fd24d0e0-4f36-42d3-9149-2fb957690305), [ibuprofen](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?audience=professional&setid=62e8db95-aaef-4b0e-841e-64a0339f3190), and [aspirin](https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=3ca776c2-47ed-5107-e063-6394a90ac5df&version=2).

This is an independent expected-outcome axis and distinct verification implementation, not an independent vocabulary: most reference mappings and the application both rely on RxNorm.

## Publication conclusion

The benchmark supports a narrow claim that the tested common single-ingredient exact names, brands, and NDCs mapped correctly in the recorded RxNorm release. It disproves a general claim that the current workflow reliably maps medication input to complete ingredient-level concepts or always makes uncertainty explicit. Combination products, some misspellings/unknown strings, and service failure are unsafe or incomplete in the tested implementation.

## Evidence map

- `protocol.md` — frozen design, criteria, metrics, and limitations.
- `fixtures/normalization_cases.json` — 30 prespecified cases and source metadata.
- `scripts/run_normalization_benchmark.py` — independent reference verification and application runner.
- `scripts/run_benchmark.sh` — disposable PostgreSQL lifecycle and environment capture.
- `raw_results/reference_verification.json` — 30/30 official-reference checks.
- `raw_results/normalization_results.json` — all application results and category metrics.
- `raw_results/api_response_log.json` — 168 timestamped reference/application calls or injected events, including official response bodies.
- `raw_results/environment_lock.txt` — exact Python environment.
- `logs/execution.log`, `logs/execution_attempt_01.log`, `logs/postgres.log` — execution and lifecycle evidence.
- `results.md`, `limitations.md`, `manuscript_notes.md` — interpretation and claim changes.
