# Research Artifacts

This folder contains design science research-support artifacts for the current RxCheck prototype. The materials are intentionally conservative: they document what the repository currently supports and explicitly flag unsupported claims.

## Files

| File | Purpose | Manuscript Section Supported |
|---|---|---|
| `claim_evidence_matrix.md` | Maps defensible claims to code evidence and safe wording | Design artifact description, validity boundaries |
| `failure_mode_analysis.md` | Documents likely failure modes, current behavior, evidence, and improvements | Risk analysis, discussion, limitations |
| `cost_constrained_design.md` | Frames RxCheck as a cost-conscious architecture without claiming cost-effectiveness | Design rationale, implementation context |
| `evaluation_plan.md` | Defines reproducible formative evaluation scenarios | Evaluation methodology |
| `evaluate_rxcheck.py` | Creates synthetic fixtures and evaluates 26 architecture scenarios without external APIs | Evaluation protocol and reproducibility appendix |
| `evaluation_results.json` | Machine-readable output from the formative architecture evaluation | Evaluation results and supplementary material |
| `evaluation_results.md` | Human-readable output from the formative architecture evaluation | Evaluation results |
| `profile_data.py` | Generates a read-only profile of interactions, assertions, drugs, aliases, conflicts, and import support | Artifact/data description, reproducibility appendix |
| `data_profile.json` | Machine-readable database profile at a recorded time | Dataset characterization, supplementary material |
| `data_profile.md` | Human-readable database and source profile with safe-claim boundaries | Artifact description, limitations |
| `explanation_quality_rubric.md` | Scores LLM outputs for structured-evidence boundary adherence, not clinical correctness | Evaluation instrument, human-AI boundary analysis |
| `explanation_eval_template.md` | Provides a 15-explanation scoring worksheet and reporting language | Future formative LLM evaluation appendix |
| `pytest_results.md` | Records the test command, outcome, warnings, and interpretation | Verification and limitations |
| `diagrams/*.mmd` | Mermaid diagrams for architecture and evaluation workflows | Figures and design communication |

## Running The Evaluation Script

The script writes synthetic evaluation rows to the configured database and therefore requires an explicit flag:

```bash
python research/evaluate_rxcheck.py --allow-live-db
```

Expected outputs:

```text
research/evaluation_results.json
research/evaluation_results.md
```

The script does not call Anthropic, OpenFDA, or RxNorm. It evaluates architecture behavior only, not clinical effectiveness.

## Running The Data Profile

The profiler is read-only and uses the configured `DATABASE_URL`:

```bash
python research/profile_data.py
```

It writes:

```text
research/data_profile.json
research/data_profile.md
```

The profile reports identifiable research-fixture rows separately but includes them in current database totals. It does not claim complete DDI coverage or clinical validity.

## LLM Explanation Review

`explanation_quality_rubric.md` and `explanation_eval_template.md` support later review of generated explanations. They assess schema, consistency, grounding, uncertainty, source attribution, and prompt-injection behavior. They explicitly do not assess or establish clinical correctness.

## Environment Requirements

The script imports the main application models and services, so it requires the same Python dependencies as the backend:

```bash
pip install -r requirements.txt
```

The evaluation and profile scripts also require a reachable Postgres database through `DATABASE_URL`.

## Manuscript Use

- Use `claim_evidence_matrix.md` to constrain artifact claims.
- Use `evaluation_plan.md` and `evaluation_results.*` for formative architecture evaluation.
- Use `data_profile.*` for a timestamped description of the configured prototype database.
- Use `explanation_quality_rubric.md` only as an architecture-boundary instrument.
- Use `failure_mode_analysis.md` and `cost_constrained_design.md` for discussion and limitations.

None of these artifacts support claims of clinical validation, FDA clearance, HIPAA compliance, formal cost-effectiveness, or complete interaction coverage.
