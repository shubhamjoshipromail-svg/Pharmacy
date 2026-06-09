# Formative Evaluation Plan

This plan evaluates architecture behavior of the RxCheck prototype. It does not evaluate clinical effectiveness, diagnostic accuracy, patient outcomes, FDA readiness, or HIPAA compliance.

## Evaluation Goal

Demonstrate that the current prototype implements its intended architectural boundaries:

- Interaction existence is deterministic and database-backed.
- DDI pair checks use canonical pair matching.
- DDSI alerts require matching active patient conditions.
- Placeholder drugs remain visible but are excluded from checks.
- Acknowledgments suppress rather than delete findings.
- Overrides persist without changing future check logic.
- LLM explanations are separate from interaction existence.

## Evaluation Method

The preferred evaluation is automated and uses `research/evaluate_rxcheck.py`.

The script creates controlled synthetic fixtures directly in the configured database:

- Synthetic user.
- Synthetic patient.
- Two real test drugs.
- One placeholder drug.
- One DDI interaction.
- One DDSI interaction.
- One condition.
- Source assertions.
- Patient medications.
- Acknowledgment and override records.

It then runs `run_interaction_check()` and records observed behavior in:

- `research/evaluation_results.json`
- `research/evaluation_results.md`

The script does not call Anthropic, OpenFDA, or RxNorm.

## Evaluation Scenarios

| Scenario | Evaluation Question | Required Fixture/Data | Expected Behavior | What It Proves |
|---|---|---|---|---|
| Deterministic DDI check | Does the checker find a known database DDI? | Patient has two active non-placeholder drugs; DB has DDI row and assertion | Result includes the DDI interaction | Interaction existence comes from database rows |
| Canonical DDI pair ordering | Does pair matching work using sorted RxCUIs? | DDI stored with `drug_a_rxcui < drug_b_rxcui`; medications can be entered in any order | Result finds exactly one DDI | Pair generation matches DB canonical ordering |
| Placeholder exclusion | Does a placeholder medication avoid false checking? | Patient has two real drugs and one active placeholder drug | `total_medications` counts only real drugs; `total_pairs_checked` excludes placeholder | Unresolved drugs remain visible but are not checked |
| DDSI without condition | Does DDSI stay hidden without matching condition? | DDSI interaction exists for a drug and condition; patient lacks condition | No DDSI finding appears | Prevents drug-disease false positives for absent conditions |
| DDSI with active condition | Does DDSI appear once condition is recorded? | Same DDSI interaction; patient has active matching condition | DDSI finding appears | DDSI condition filter works |
| Acknowledgment suppression | Does acknowledgment suppress instead of delete? | Acknowledgment exists for patient + interaction with current severity | Finding appears with `suppressed=true` | Reviewed findings remain auditable |
| Override persistence | Are override records stored? | Create override for a finding | Override row exists and finding remains checkable | Override is persisted but not used as detection logic |
| LLM boundary | Are findings created without LLM calls? | Run check without calling explanation endpoint | Findings exist and `llm_explanation_id` is empty | LLM is separate from interaction existence |

## Pass Criteria

The evaluation is considered successful if:

- All expected checks in the generated JSON are `passed: true`.
- No paid or external API calls are required.
- The generated markdown clearly states run ID, patient ID, scenario results, and limitations.

## Known Limitations Of This Evaluation

- It uses synthetic fixtures, not real clinical cases.
- It does not measure clinical correctness.
- It does not validate DDInter coverage against a gold standard.
- It does not test frontend rendering.
- It does not test live RxNorm, OpenFDA, or Anthropic reliability.
- It writes synthetic evaluation rows to the configured database.

## Manual Protocol If Automation Cannot Run

If database connectivity is unavailable:

1. Start the backend with a reachable Postgres database.
2. Run `python scripts/init_db.py`.
3. Run `python research/evaluate_rxcheck.py`.
4. Review `research/evaluation_results.md`.
5. Confirm every scenario is marked pass.

If the script cannot be used, a manual equivalent is:

1. Create two synthetic non-placeholder drugs and one placeholder drug.
2. Create one DDI interaction between the real drugs.
3. Create one condition and one DDSI interaction for one real drug.
4. Create a synthetic patient with all three medications but no condition.
5. Run the orchestrator and confirm only the DDI appears.
6. Add the condition and rerun; confirm DDSI appears.
7. Add acknowledgment for DDI and rerun; confirm DDI is suppressed.
8. Add override for a finding; confirm override row exists but future checks still run normally.
9. Confirm no LLM explanation rows are required for findings to exist.
