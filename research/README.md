# Research Artifacts

This folder contains design science research-support artifacts for the current RxCheck prototype. The materials are intentionally conservative: they document what the repository currently supports and explicitly flag unsupported claims.

## Files

| File | Purpose | Manuscript Section Supported |
|---|---|---|
| `claim_evidence_matrix.md` | Maps defensible claims to code evidence and safe wording | Design artifact description, validity boundaries |
| `failure_mode_analysis.md` | Documents likely failure modes, current behavior, evidence, and improvements | Risk analysis, discussion, limitations |
| `cost_constrained_design.md` | Frames RxCheck as a cost-conscious architecture without claiming cost-effectiveness | Design rationale, implementation context |
| `evaluation_plan.md` | Defines reproducible formative evaluation scenarios | Evaluation methodology |
| `evaluate_rxcheck.py` | Creates synthetic fixtures and evaluates architecture behavior | Evaluation protocol and reproducibility appendix |
| `evaluation_results.json` | Machine-readable output from the formative architecture evaluation | Evaluation results and supplementary material |
| `evaluation_results.md` | Human-readable output from the formative architecture evaluation | Evaluation results |
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

## Environment Requirements

The script imports the main application models and services, so it requires the same Python dependencies as the backend:

```bash
pip install -r requirements.txt
```

It also requires a reachable Postgres database through `DATABASE_URL`.
