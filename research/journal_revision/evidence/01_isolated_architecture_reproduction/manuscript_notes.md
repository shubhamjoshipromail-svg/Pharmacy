# Manuscript Notes From Evidence 01

## Required result update

Replace language that treats the 26/26 result only as an unreproduced historical run with:

> The committed architecture evaluator was rerun on July 15, 2026 in three newly created databases within a disposable loopback-only PostgreSQL 16.14 cluster. All three repetitions passed the same 26 predefined synthetic scenarios (78/78 scenario executions), with identical scenario outcomes and no external API calls reported on the exercised paths.

Immediately qualify this result:

> The scenarios and expected outcomes were self-authored and verify architecture behavior rather than clinical correctness. The clean rerun used SQLAlchemy model metadata because the committed migration was empty, and the real interaction dataset was not reconstructed.

## Methods additions

- State that each repetition began with zero user tables and that `Base.metadata.create_all()` created 20 expected tables.
- Report the evaluated-source commit `5038106ada9c66fb2cd1fc0e33c8322553b4d699` and the evidence-run repository HEAD `63fb4c043e6e16561f6cc9a46eaa152584de83b0`.
- Report macOS 15.7.7/arm64, Python 3.12.13, PostgreSQL 16.14, and the resolved package file.
- Describe the local-only hostname, database-name, and server-address guards.
- State that three fresh databases were used and the cluster was deleted after execution.
- Cite the evidence folder and machine-readable results.

## Results additions

- Report 3/3 repetitions passing 26/26 scenarios, not a new clinical accuracy rate.
- Report identical scenario-level outcomes across repetitions.
- Report zero external paid/free API flags.
- Do not use the approximately 0.15-second evaluator times as core-check latency; they were not designed as a latency study.

## Claim-status changes

| Claim | Previous status | New status |
|---|---|---|
| The 26-scenario evaluator can run on a fresh database. | Requires verification | Supported in the recorded local environment. |
| The tested architecture scenarios pass from clean synthetic state. | Historical result only | Supported across three repeated fresh-database runs. |
| Core checking avoids Anthropic/OpenFDA/RxNorm on tested paths. | Supported by historical run/code inspection | Supported by repeated sentinel-backed execution. |
| The repository is fully reproducible from a clean clone. | Unsupported | Still unsupported. |
| Database/source data can be reconstructed. | Unsupported | Still unsupported. |
| The system is clinically accurate or safe. | Unsupported | Still unsupported. |

## Abstract implication

The Methods and Results may now describe an executed isolated rerun rather than saying that database-writing code was not rerun. The abstract must still state that no clinical cases, pharmacists, patient outcomes, or generated explanations were evaluated.

## Threats-to-validity implication

Retain self-authorship, synthetic-fixture, missing-source-data, and absent-clinical-validation threats. Replace the earlier “configured persistent database only” threat with the narrower limitations that schema setup bypassed the empty migration and that reproduction has not yet been performed by an independent researcher or on a second platform.
