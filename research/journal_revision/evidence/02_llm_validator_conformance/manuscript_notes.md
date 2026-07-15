# Manuscript Notes From Evidence 02

## Required result statement

Add a negative formative result:

> A 30-case automated response-validator audit accepted all 3 valid controls but cleanly rejected only 5 of 27 invalid/adversarial outputs. Fifteen invalid outputs were accepted and seven produced unhandled exceptions. The suite did not call a model or assess clinical correctness.

## Required implementation wording

Use:

> The explanation path applies custom JSON parsing, verifies seven required keys, checks that `sources_used` is a list, and scans the raw response for stored non-party drug names.

Do not use:

- “schema-validated output” without immediately specifying that the custom checks are partial and failed the conformance suite;
- “strict RAG”;
- “grounded explanation” as an empirical result;
- “hallucination resistant”;
- “source-validated” or “severity-preserving”;
- “prompt-injection resistant.”

## Abstract implication

If the LLM remains in the abstract, state only that it is downstream of an existing finding. Do not imply that explanation content passed a safety or grounding validation. The negative validator result can be mentioned in Results if space permits; otherwise the explanation layer should be explicitly described as unevaluated/insufficiently validated and non-clinical.

## Results implication

Report both the successful authority-boundary result and the failed content-enforcement result:

- Successful: the LLM cannot create a finding through the evaluated explanation endpoint, and the core checker does not call it.
- Failed: the automated validator did not reliably enforce structure, types, sources, severity, grounding, dosing constraints, unknown names/factors, or injection-shaped output.

This distinction is central. “Downstream” limits finding authority; it does not make the generated prose evidentially faithful.

## Discussion implication

Recast the artifact's contribution as a separation-of-authority pattern with an incompletely implemented content boundary. The negative result is a useful design-science finding: architectural placement and post-generation validation are different controls, and the former cannot substitute for the latter.

Before any live-model evaluation or user-facing explanation claim, the application needs:

1. Full JSON consumption and top-level object enforcement.
2. A strict typed schema with non-empty fields, enumerated confidence, element types, and additional-field policy.
3. Source-set and stored-severity consistency checks.
4. Broader entity/factor detection.
5. Explicit handling of unsupported dosing/prescribing content.
6. Evidence-entailment or human-review procedures for mechanism/effect/management claims.
7. Prompt-injection-oriented defenses and regression tests.
8. Controlled error handling before persistence/return.

## Claim-status changes

| Claim | Status after Evidence 02 |
|---|---|
| Explanation requires a persisted finding | Supported by architecture evidence; unchanged |
| LLM cannot create a check finding on the evaluated path | Supported; unchanged |
| Output undergoes limited custom checks | Supported |
| Output is strictly or comprehensively schema-validated | Not supported |
| Severity and sources are preserved by validation | Not supported |
| Unknown drug/food/condition hallucinations are comprehensively detected | Not supported |
| Unsupported management/dosing is rejected | Not supported |
| Prompt injection is resisted | Not supported |
| Generated explanations are safe, accurate, or grounded | Not supported |

## Manuscript positioning decision

The LLM may remain as an architectural component only if the paper foregrounds this negative result and confines the contribution to finding-authority separation. It should not be presented as a successfully validated explanation system. A stronger alternative is to treat explanation validation as unresolved future work until a remediated implementation passes the frozen suite and live outputs receive appropriate review.
