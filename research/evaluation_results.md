# RxCheck Expanded Architecture Evaluation Results

Generated at: `2026-06-09T19:59:05.923451+00:00`

Scope: formative architecture behavior, not clinical effectiveness.

## Summary

- Total scenarios: 26
- Passed: 26
- Failed: 0
- Paid APIs called: False
- Free external APIs called: False

## Scenario Results

| Scenario | Result | Expected | Observed | Code evidence | Manuscript-safe interpretation |
|---|---|---|---|---|---|
| `deterministic_ddi_from_stored_row` | PASS | A stored DDI row produces a finding. | DDI present=True; run_id=b7036964-b774-44b1-bf57-718ecce5ac15 | app/services/orchestrator.py::run_interaction_check | The prototype deterministically returns a DDI fixture stored in its database. |
| `canonical_drug_pair_ordering` | PASS | Medications entered in reverse order still match one canonical DDI row. | stored_pair=['eval-33bab07f02-100', 'eval-33bab07f02-200']; occurrences=1 | app/services/orchestrator.py canonical_pairs; app/models/interaction.py interactions_ddi_ordered | Canonical RxCUI ordering prevents A/B and B/A from producing separate DDI findings. |
| `inactive_medication_exclusion` | PASS | The inactive medication is not counted or checked. | active_non_placeholder_count=2; inactive_medication_id=c223f31c-3edf-4eea-a70c-9a7e816a5524 | app/services/orchestrator.py active medication query | The orchestrator excludes medication rows where is_active is false. |
| `placeholder_drug_exclusion` | PASS | The active placeholder medication is excluded from check counts and DDI pairs. | total_medications=2; total_pairs_checked=1 | app/services/orchestrator.py filter Drug.is_placeholder.is_(False) | Unresolved placeholders do not participate in deterministic interaction checking. |
| `placeholder_visible_but_excluded` | PASS | The placeholder remains stored in the patient medication list while excluded from checks. | placeholder_medication_stored=True; checked_medications=2 | app/models/patient.py::PatientMedication; app/services/orchestrator.py placeholder filter | The architecture preserves unresolved input for review without treating it as a verified interaction-check concept. |
| `ddsi_absent_without_active_condition` | PASS | DDSI is absent before the matching patient condition is recorded. | DDSI present=False | app/services/orchestrator.py DDSI PatientCondition subquery | The DDSI query avoids surfacing the fixture when the matching condition is absent. |
| `dfi_independent_of_condition_profile` | PASS | DFI appears for an active drug even when the patient has no condition rows. | DFI present=True | app/services/orchestrator.py DFI query | The prototype treats DFI lookup as drug-based rather than condition-gated. |
| `severity_ranking` | PASS | Findings are ordered from higher to lower severity. | ordered_severities=['major', 'minor'] | app/services/orchestrator.py ranked_items.sort | The returned fixture findings are ordered by the implemented severity priority. |
| `source_severity_conflict_flag` | PASS | Different assertion severities set sources_conflict=true. | sources_conflict=True | app/schemas/interaction.py::build_summary | The summary flags disagreement between stored source severities; it does not adjudicate which source is clinically correct. |
| `source_assertion_preservation` | PASS | Both source assertions retain source, raw severity, source ID, and raw payload. | assertion_count=2; sources=['DDInter', 'manual'] | app/models/interaction.py::InteractionSourceAssertion | The schema preserves multiple source assertions and their provenance for the fixture interaction. |
| `check_run_persistence` | PASS | The completed check run is stored with the checked medication snapshot. | run_persisted=True; snapshot_size=2 | app/models/check.py::InteractionCheckRun; app/services/orchestrator.py medication_snapshot | The prototype persists a run-level record of the non-placeholder active medications evaluated. |
| `finding_snapshot_persistence` | PASS | The finding stores run-time severity, source list, and conflict state. | severity=major; sources=['DDInter', 'manual']; conflicted=True | app/models/check.py::InteractionCheckFinding; app/services/orchestrator.py finding creation | The fixture finding retains selected run-time fields for later review. |
| `findings_exist_before_llm_request` | PASS | Findings exist with no LLM explanation requested. | finding_count=2; llm_explanation_ids=[None, None] | app/services/orchestrator.py; app/models/check.py::InteractionCheckFinding | Interaction findings are created independently of the optional explanation layer. |
| `duplicate_medication_does_not_duplicate_finding` | PASS | A duplicate active medication row does not duplicate the canonical DDI finding. | DDI_occurrences=1; total_medications=3; total_pairs_checked=2 | app/services/orchestrator.py canonical pair set and database interaction query | Duplicate medication rows did not duplicate the fixture finding. The current pair-count metric may still include a same-RxCUI self-pair, so this is not evidence of complete duplicate-medication normalization. |
| `missing_database_interaction_creates_no_finding` | PASS | An active normalized drug with no stored interaction does not create a finding. | drug_c_mentioned=False; total_medications=3; total_interactions=2 | app/services/orchestrator.py database-only interaction queries | The checker does not infer missing interactions from an LLM or external label service. |
| `ddsi_present_with_matching_active_condition` | PASS | DDSI appears after adding the matching active condition. | DDSI present=True | app/services/orchestrator.py DDSI PatientCondition subquery | The DDSI fixture is returned when its matching condition is active for the patient. |
| `severity_ranking_with_three_interaction_types` | PASS | DDI major, DDSI moderate, and DFI minor are returned in severity order. | ordered_severities=['major', 'moderate', 'minor'] | app/services/orchestrator.py ranked_items.sort | The three fixture interaction types follow the implemented severity ordering. |
| `ddsi_absent_after_condition_resolution` | PASS | DDSI is absent after the patient condition receives a resolved date. | DDSI present=False | app/services/orchestrator.py filter PatientCondition.resolved_date.is_(None) | Resolved conditions are excluded from the DDSI fixture query. |
| `override_persistence` | PASS | An override row is persisted for an existing finding. | override_id=3; finding_id=329 | app/models/audit.py::InteractionOverride; app/api/interactions.py::override_finding | The prototype persists override metadata for later review. |
| `override_does_not_suppress_future_finding` | PASS | The overridden interaction remains an unsuppressed finding in a later check. | DFI present=True; suppressed=False | app/services/orchestrator.py does not query InteractionOverride | Current overrides are audit records and do not automatically alter future check behavior. |
| `acknowledgment_severity_escalation_behavior` | PASS | An acknowledgment below the current major severity does not suppress the DDI. | ack_severity=moderate; current_severity=major; suppressed=False | app/services/orchestrator.py acknowledgment severity comparison | The implemented comparison resurfaces a finding when current severity exceeds the stored acknowledgment severity. |
| `acknowledgment_suppression` | PASS | An acknowledgment at current severity marks the DDI suppressed without deleting it. | DDI present=True; suppressed=True; suppressed_count=1 | app/services/orchestrator.py acknowledgment suppression | Acknowledgment changes presentation state while preserving the finding in the result and database. |
| `llm_explanation_requires_existing_finding` | PASS | A nonexistent finding is rejected before explanation generation. | HTTP 404: Finding not found | app/api/interactions.py::get_finding_or_404 and explain_finding | The explanation endpoint is structurally tied to persisted findings and cannot start from an arbitrary drug pair. |
| `anthropic_not_required_for_core_checking` | PASS | Core checking completes when the LLM explanation function is replaced with a failing sentinel. | total_interactions_found=2 | app/services/orchestrator.py has no Anthropic dependency | The deterministic check path does not require Anthropic; this does not evaluate explanation quality. |
| `openfda_not_required_for_core_checking` | PASS | Core checking completes when OpenFDA citation fetching is replaced with a failing sentinel. | total_interactions_found=2 | app/services/orchestrator.py has no OpenFDA dependency | OpenFDA is optional explanation context, not a source of interaction existence. |
| `rxnorm_not_required_at_check_time` | PASS | Core checking completes when normalization is replaced with a failing sentinel. | total_interactions_found=2 | app/services/orchestrator.py consumes stored RxCUIs and does not call normalize_drug_name | Once medications are normalized and stored, the check path does not require a live RxNorm call. |

## Fixture IDs

```json
{
  "assertion_ids": [
    244829,
    244830,
    244831,
    244832
  ],
  "condition_id": 7,
  "ddi_interaction_id": "0e1cdc35-ddb4-430f-8b1f-699f159d2e83",
  "ddsi_interaction_id": "8fb917a6-5df5-4467-a605-6daea0a7298f",
  "dfi_interaction_id": "3610bdb3-fd3e-4c27-8e8d-8345652cf684",
  "drug_a_rxcui": "eval-33bab07f02-100",
  "drug_b_rxcui": "eval-33bab07f02-200",
  "drug_c_name": "Evaluation Drug With No Stored Interaction",
  "drug_c_rxcui": "eval-33bab07f02-300",
  "food_id": 1,
  "label": "eval-33bab07f02",
  "medication_a_id": "f74799a8-cf84-414e-b596-7d02d120dffe",
  "medication_b_id": "d7e7f584-04a3-4f9e-be1b-66acef17709a",
  "medication_c_id": "c223f31c-3edf-4eea-a70c-9a7e816a5524",
  "patient_id": "6cd2937e-1d08-482f-beb0-fada834571b5",
  "placeholder_medication_id": "fcf434d7-dc01-40ae-a46a-1cd699757fab",
  "placeholder_rxcui": "eval-33bab07f02-placeholder",
  "user_id": "db4fa61b-0071-4bf0-9c56-ba662f6b56a4"
}
```

## Limitations

- Uses synthetic fixtures rather than clinical cases.
- Evaluates architecture behavior, not clinical correctness or patient outcomes.
- Does not evaluate interaction-source completeness.
- Does not call RxNorm, OpenFDA, or Anthropic.
- Writes clearly labeled synthetic evaluation rows to the configured database.
- Duplicate medication handling is evaluated only for duplicate finding prevention; the pair-count metric can include a same-RxCUI self-pair.
