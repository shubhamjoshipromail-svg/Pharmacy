# Protocol: Independently Specified Medication-Normalization Benchmark

## Research question

How accurately and safely does the unchanged RxCheck normalization workflow map a small, frozen set of representative medication inputs to the ingredient concepts specified by an official terminology reference?

## Independent axis

The 30 expected outcomes in `fixtures/normalization_cases.json` were frozen before application execution. Canonical-name, brand, misspelling-target, combination-product, and NDC mappings are rechecked by a separate reference-verification path against the official RxNorm API before the application normalizer runs. Three NDC ingredient labels are additionally supported by official DailyMed pages.

The official RxNorm version endpoint reported release `06-Jul-2026` and API version `3.1.353`. The benchmark aborts if that version differs from the frozen fixture metadata. NLM's official release page identifies the July 6, 2026 monthly release. The expected labels therefore do not come from project-authored architecture expectations, although the application and reference verifier necessarily use the same underlying public terminology service for most mappings.

## Cases

| Category | Cases | Expected behavior |
|---|---:|---|
| Exact ingredient name | 8 | Resolve to the specified single ingredient with `matched_exact` |
| Brand name | 7 | Resolve to the specified ingredient with `matched_brand` |
| Misspelling | 4 | Resolve to the specified ingredient with `matched_fuzzy` |
| Low-confidence misspelling candidate | 1 | Return candidates containing the specified ingredient without automatic resolution |
| Multi-ingredient name | 4 | Preserve the complete specified ingredient set |
| NDC | 3 | Resolve to the DailyMed/RxNorm-supported ingredient with `matched_ndc` |
| Constructed unmatched/empty input | 2 | Return a visible unmatched placeholder |
| Injected RxNorm connection failure | 1 | Return a controlled non-resolution result rather than propagate an exception |

## Case evaluation

- `resolved_single`: returned RxCUI exactly equals the one expected ingredient; expected status matches; no placeholder/candidates.
- `candidate_contains`: no automatic RxCUI; expected status matches; candidate RxCUIs include the expected ingredient.
- `resolved_set`: the set represented by the returned normalization result exactly equals all expected ingredient RxCUIs.
- `unmatched_placeholder`: unmatched status, placeholder flag, and deterministic placeholder RxCUI are present.
- `controlled_service_failure`: no exception escapes and a visible unmatched placeholder is returned.

Each application case starts with empty drug/alias/unresolved tables so cache order cannot influence the result. Full official reference responses and application-consumed API responses are retained with timestamps.

## Metrics

- reference verification pass count;
- overall exact case pass rate;
- category-level pass counts/rates;
- exception count;
- complete-set accuracy for multi-ingredient inputs;
- controlled non-resolution accuracy;
- NDC accuracy;
- number and type of official API calls;
- saved database artifact counts per case.

No sensitivity, specificity, clinical safety, or real-world prevalence metric is estimated because the set is purposive and small.

## Pass/fail rule

The benchmark contract passes only if:

1. all independently checkable reference mappings verify against the frozen official service version;
2. all 30 application cases complete without an escaping exception; and
3. all 30 cases meet their exact prespecified expected behavior.

Category results are reported even when the overall strict contract fails. A failed category must narrow the corresponding normalization claim.

## Reproduction command

```bash
PG_BIN=/path/to/postgresql/bin \
PYTHON_BIN=/path/to/python \
bash research/journal_revision/evidence/06_normalization_benchmark/scripts/run_benchmark.sh
```

The command requires internet access to the official RxNorm API. The runner refuses a non-loopback database and returns exit status 1 when the application contract fails.

## Prespecified limitations

- Purposive 30-case sample; no prevalence weighting or external human adjudication.
- Most mappings use the same official terminology service that the application queries; the independent axis is the frozen/reference-verified expected outcome and distinct verification logic, not an independent vocabulary.
- Four combinations test set preservation even though the current result model is scalar; this is a deliberate test of the manuscript's ingredient-level normalization wording.
- Misspelling choices are investigator-selected and not drawn from pharmacy error logs.
- DailyMed labels support NDC ingredients, but the application still resolves those NDCs through RxNorm.
- One service outage shape and one execution environment.
- Terminology conformance is not proof of medication-history accuracy, clinical decision quality, or safe deployment.
