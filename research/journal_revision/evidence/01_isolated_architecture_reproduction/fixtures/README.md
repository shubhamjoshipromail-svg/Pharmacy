# Fixture provenance

This evidence task introduces no external or clinical fixtures. Each repetition calls the existing `create_fixtures()` function in `research/evaluate_rxcheck.py`, which generates uniquely labeled synthetic users, patients, medications, interactions, source assertions, conditions, acknowledgments, and overrides.

The complete generated fixture identifiers are retained within each `raw_results/run_*.json` file. The disposable databases are deleted after execution.
