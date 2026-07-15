# Manuscript Notes From Evidence 06

## Required normalization wording

Replace general claims such as “normalize or explicitly reject uncertain inputs” with:

> The prototype attempts to map one medication input to one ingredient-level RxCUI through local aliases and RxNorm exact, approximate, and NDC endpoints. In a purposive 30-case benchmark, all tested exact ingredient names, brands, and NDCs resolved as specified, but multi-ingredient, some approximate-match, unknown-token, and service-failure behavior did not meet the prespecified contract. The current workflow therefore does not guarantee complete ingredient preservation or explicit non-resolution of uncertain input.

## Permitted methods/results wording

> Thirty expected outcomes were frozen before execution and independently rechecked against RxNorm release 06-Jul-2026 (API 3.1.353); three NDC ingredients also had official DailyMed label support. Each application case began with empty terminology tables. Twenty-two of 30 strict cases passed. Exact ingredient names (8/8), brands (7/7), and NDCs (3/3) passed. Three of five misspelling/candidate cases, the empty-input case, and no multi-ingredient, constructed-unknown, or injected-outage case met the full prespecified behavior.

Immediately add that this is a purposive terminology-conformance set, not a population accuracy estimate or clinical validation.

## Required failure disclosure

- Four two-ingredient products were reduced to one ingredient because the implementation returned the first related `IN` concept.
- `asprin` and the constructed non-drug token were auto-saved as non-placeholder numeric concepts with no usable name in the recorded responses.
- `warfarine` mapped to warfarin but was labeled `matched_exact`, showing that normalization-status semantics do not reliably distinguish the route taken.
- An injected RxNorm connection failure escaped without creating a placeholder/unresolved entry.

## Claim-status changes

| Claim | Status after Evidence 06 |
|---|---|
| Tested exact ingredients map to expected RxCUIs | Supported for 8 frozen cases |
| Tested brands map to expected ingredients | Supported for 7 frozen cases |
| Tested NDCs map to expected ingredients | Supported for 3 frozen cases |
| Misspellings are reliably normalized or routed to candidates | Not supported; 3/5 full criteria passed |
| Multi-ingredient products preserve all components | Disproved for all 4 tested cases |
| Unknown input is always retained as visible unresolved input | Not supported |
| RxNorm network failure degrades to explicit non-resolution | Disproved for the injected case |
| Normalization-status labels faithfully identify match method | Not supported |
| Overall normalization accuracy is known | Not supported; purposive set only |
| Normalization is clinically safe | Not supported |

## Article implication

The normalization layer can no longer be presented as a demonstrated safety contribution in its current general form. The paper may present explicit placeholder handling as an implemented design mechanism, but Evidence 06 shows that not all uncertain inputs reach it. Treat complete multi-ingredient representation, candidate validation, and controlled service failure as required engineering remediation/future work.
