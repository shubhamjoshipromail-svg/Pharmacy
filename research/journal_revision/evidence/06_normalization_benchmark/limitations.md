# Limitations: Medication-Normalization Benchmark

1. The 30 cases are purposive and small. The 73.3% strict pass rate is not a prevalence-weighted accuracy estimate and must not be generalized to pharmacy inputs.
2. There was no pharmacist, terminology specialist, or second-researcher adjudication. Expected mappings were official-reference-derived and machine-reverified.
3. Most reference mappings and the application share RxNorm. Independence comes from freezing expected outcomes and using a separate verifier, not from a separate terminology source.
4. The three NDC ingredient labels have a distinct DailyMed basis, but their application resolution still uses RxNorm.
5. Misspellings were investigator-selected rather than sampled from real dispensing, medication-reconciliation, search-log, or transcription errors.
6. The unmatched token was deliberately constructed. Its false match demonstrates a possible failure, not its frequency for real unknown inputs.
7. The test required a live terminology service and captures one RxNorm release/version. Future terminology updates can change approximate matches.
8. Only one connection-failure shape was injected. Timeout, malformed response, rate limit, server error, partial response, and slow-service behavior were not separately tested.
9. Candidate selection UI and user confirmation were not exercised. The candidate case tests service output only.
10. The multi-ingredient criterion requires complete ingredient-set preservation because omitted components can affect downstream pairing; the current scalar application model cannot satisfy it by construction.
11. Correct RxCUI mapping does not establish dose/form correctness, medication-history correctness, DDI coverage, clinical correctness, usability, or patient safety.
12. A fresh terminology table state was used for every case. Cache-hit behavior and conflicting preexisting aliases were not evaluated.
