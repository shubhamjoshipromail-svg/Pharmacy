# RxCheck Evaluation Results

Generated at: `2026-06-09T19:14:19.617255Z`

Scope: architecture behavior, not clinical effectiveness.

## Summary

- Total scenarios: 7
- Passed: 7
- Failed: 0
- Paid APIs called: False
- Free external APIs called: False

## Scenarios

| Scenario | Result | Expected | Observed |
|---|---|---|---|
| `deterministic_ddi_check` | PASS | Known DDI fixture appears in check result. | Interaction types returned: ['DDI'] |
| `canonical_pair_and_placeholder_exclusion` | PASS | Two non-placeholder medications and one DDI pair are checked despite three active medication rows. | total_medications=2, total_pairs_checked=1 |
| `ddsi_absent_without_condition` | PASS | DDSI fixture is absent before matching patient condition is recorded. | DDSI present before condition: False |
| `ddsi_present_with_active_condition` | PASS | DDSI fixture appears after matching active patient condition is recorded. | DDSI present after condition: True |
| `acknowledgment_suppression` | PASS | Acknowledged DDI remains in result but is marked suppressed. | DDI suppressed=True |
| `override_persistence` | PASS | Override row is persisted for a finding. | override_persisted=True |
| `llm_separate_from_interaction_existence` | PASS | Findings exist before any LLM explanation is requested. | finding_count=2, all_llm_explanation_id_none=True |

## Fixture IDs

```json
{
  "condition_id": 6,
  "ddi_interaction_id": "adb911af-0b12-49e7-92ed-560d51049f5e",
  "ddsi_interaction_id": "ea2e0a1b-ae28-4166-8baf-924377a47fd1",
  "drug_a_rxcui": "eval-2ff631e92d-a",
  "drug_b_rxcui": "eval-2ff631e92d-b",
  "label": "eval-2ff631e92d",
  "patient_id": "9b5855bd-649d-40db-aff2-81587d90af53",
  "placeholder_rxcui": "eval-2ff631e92d-placeholder",
  "user_id": "412dbb59-54e0-49ce-b5a9-aa4fb18c1b4e"
}
```

## Limitations

- Uses synthetic fixtures rather than clinical cases.
- Does not evaluate clinical correctness or source coverage completeness.
- Does not call RxNorm, OpenFDA, or Anthropic.
- Writes synthetic evaluation rows to the configured database.
