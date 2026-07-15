# Results: Medication-Normalization Benchmark

## Aggregate result

| Metric | Result |
|---|---:|
| Frozen reference cases | 30 |
| Official-reference verifications passed | 30/30 |
| Application cases completed | 30/30 |
| Strict application cases passed | 22/30 (73.3%) |
| Strict application cases failed | 8/30 (26.7%) |
| Escaping application exceptions | 1 |
| Reference + application official API calls/events retained | 168 |
| Application official API calls/events | 111 |
| Overall strict contract | FAIL |

The eight failures are not an estimate of population error rate because the cases were purposively selected. They identify concrete unsupported input classes and failure modes.

## Category results

| Category | Passed | Failed | Pass rate |
|---|---:|---:|---:|
| Exact ingredient | 8 | 0 | 100% |
| Brand | 7 | 0 | 100% |
| Misspelling (automatic) | 2 | 2 | 50% |
| Misspelling candidate | 1 | 0 | 100% |
| Multi-ingredient | 0 | 4 | 0% |
| NDC | 3 | 0 | 100% |
| Constructed unmatched token | 0 | 1 | 0% |
| Empty input | 1 | 0 | 100% |
| Injected service failure | 0 | 1 | 0% |

## Failed cases

| ID | Input | Expected | Observed | Interpretation |
|---|---|---|---|---|
| M01 | `asprin` | Aspirin RxCUI 1191, fuzzy | RxCUI 218770, preferred name `218770`, fuzzy | A high approximate score was accepted even though the candidate had no active properties or related ingredient in the recorded API responses |
| M02 | `warfarine` | Warfarin RxCUI 11289, fuzzy | Correct RxCUI 11289, status `matched_exact` | `search=2` normalized matching was labeled exact; ingredient was correct but provenance/status was not |
| C01 | `amoxicillin / clavulanate` | RxCUIs 48203 and 723 | Only 48203 (clavulanate) | First related ingredient only |
| C02 | `sulfamethoxazole / trimethoprim` | RxCUIs 10180 and 10829 | Only 10180 (sulfamethoxazole) | First related ingredient only |
| C03 | `acetaminophen / hydrocodone` | RxCUIs 161 and 5489 | Only 161 (acetaminophen) | First related ingredient only |
| C04 | `lisinopril / hydrochlorothiazide` | RxCUIs 29046 and 5487 | Only 29046 (lisinopril) | First related ingredient only |
| U01 | constructed non-drug token | Visible unmatched placeholder | RxCUI 835748, preferred name `835748`, fuzzy | High approximate score caused false automatic resolution of an unresolvable candidate |
| F01 | aspirin with injected connection failure | Controlled visible non-resolution | Escaped `ConnectError`; no stored drug/unresolved entry | Network failure is not converted to the explicit non-resolution path |

## Key interpretation

The scalar `NormalizationResult.rxcui` and `_resolve_ingredient_concept()` return contract cannot preserve a multi-ingredient set. The function iterates official related ingredients and returns the first item. In an interaction checker, that means another component may never enter the candidate-pair set.

The fuzzy path uses a score threshold without requiring that the selected candidate resolve to an active concept or ingredient. Both `asprin` and the constructed non-drug token were saved as non-placeholder drugs whose preferred names were bare numeric IDs. This directly challenges the proposed fail-visible principle.

The correct `warfarine` ingredient is useful but does not meet the frozen full criterion because the system calls normalized RxNorm search results `matched_exact`. The paper can report ingredient correctness separately in prose, but must not treat the stored normalization-status labels as validated provenance.

## Integrity record

- Execution-time repository HEAD: `6d2d120b7a35460810e43374c179f02d531d36ca`.
- Last commit affecting evaluated normalization/model sources: `4d9d32f6e2ccdb8d32703ce2e0546543273963d7`.
- Fixture SHA-256: `e518cc4fa84cd46218663f85842e08f93909702a53f98d1cd7f73e7a033c06ad`.
- Results SHA-256: `999cde750927aa93472d7dc2ae4c10decd426643ce4f005a3ff50c65fded955c`.
- Reference verification SHA-256: `82fdc35c991aa8e8e5f0b179025b35b6ece679dfa6cfe7f8ec4d4c56fbf4a4e0`.
- API response log SHA-256: `e12b7ee6b091a0d84f9333dad9fae68dbd12428b0b998d0d180761a07e293e4c`.
- Environment lock SHA-256: `b6169f706047c4b5763d2157110cdcd96a79b347c8151a3f1c0c324b2c70350e`.

The results also retain the runner/source hashes, database metadata, package versions, case artifacts, exceptions, and complete category decisions.
