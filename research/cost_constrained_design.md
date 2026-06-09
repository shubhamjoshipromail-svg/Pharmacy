# Cost-Constrained Design Analysis

This document analyzes RxCheck as a cost-conscious prototype architecture for budget-constrained pharmacy or healthcare environments. It does not claim formal cost-effectiveness, clinical effectiveness, or operational readiness.

## Design Position

RxCheck is designed around a low-cost principle: keep the core interaction check local and deterministic, and make paid or network-dependent services optional wherever possible.

```text
Core check path:
Patient medications -> Postgres interaction tables -> deterministic findings

Optional explanation path:
Finding -> OpenFDA context -> Anthropic explanation
```

The core interaction check does not require Anthropic, OpenFDA, or RxNorm at check time if medications are already normalized and interaction data is already imported.

## Open-Source Or Public Components

| Component | Role | Cost Profile |
|---|---|---|
| Python | Backend language | Open-source |
| FastAPI | HTTP API framework | Open-source |
| SQLAlchemy | ORM | Open-source |
| Postgres | Database | Open-source software; hosting may cost money |
| Alembic | Migration tooling | Open-source |
| React | Frontend framework | Open-source |
| Vite | Frontend build tool | Open-source |
| Tailwind CSS | Styling | Open-source |
| Axios | Frontend HTTP client | Open-source |
| pandas | CSV import | Open-source |
| psycopg2 | Postgres driver | Open-source |
| NIH RxNorm API | Medication normalization | Public/free API |
| OpenFDA API | Label context | Public/free API |

## Paid Or Proprietary Components

| Component | Role | Notes |
|---|---|---|
| Anthropic Claude | Optional LLM explanations | Paid API usage; not required for core checking |
| Railway | App and database hosting | Paid or free-tier depending on account/usage |
| DDInter data | Interaction source files | Licensing/usage terms should be reviewed separately before publication or deployment |

## Recurring Cost Drivers

| Driver | Why it costs money | Can it be reduced? |
|---|---|---|
| Hosted Postgres | Stores drugs, patients, interactions, check runs, audit data | Self-host Postgres or use lower-cost managed Postgres |
| App hosting | Runs FastAPI and serves frontend | Run on small VPS, institutional server, or container platform |
| Anthropic calls | Per-explanation token usage | Make explanations optional, cache explanations, use only for selected severe findings |
| Build/deploy minutes | Frontend build and Python install during deploy | Cache builds or deploy prebuilt containers |
| Storage growth | Check runs, findings, coverage checks, LLM outputs | Add retention and archival policies |

## What Works Without Anthropic

The following still works:

- Patient creation and listing.
- Medication addition and RxNorm normalization.
- Condition addition/removal.
- Deterministic interaction checks.
- Severity-grouped summaries.
- Hub scores.
- Acknowledgments and suppression.
- Overrides and audit events.
- Check history.

What does not work:

- New AI-generated explanations from `POST /api/v1/findings/{finding_id}/explain`.

Current behavior:

- Missing `ANTHROPIC_API_KEY` returns a clear HTTP 400 from the explanation endpoint.

## What Works Without OpenFDA

The following still works:

- Core interaction checking.
- RxNorm normalization.
- Acknowledgments.
- Overrides.
- Existing deterministic summaries.
- Anthropic explanations if the LLM call succeeds without label context, depending on how OpenFDA failure is handled.

What degrades:

- FDA label excerpts are missing from explanation context.
- SPL set IDs are not discovered/persisted.

Current limitation:

- OpenFDA non-404 HTTP errors may propagate because the fetcher calls `raise_for_status()`.

## What Works Without RxNorm After Aliases Are Loaded

If drugs and aliases are already loaded:

- Existing aliases resolve locally from `drug_aliases`.
- Imported DDInter interactions can be checked.
- Existing patient medications can be checked.

What degrades:

- New medication names not in aliases may fail or require live RxNorm.
- NDC resolution requires live RxNorm.
- Fuzzy typo resolution requires live RxNorm unless the typo was previously learned as an alias.

Cost-conscious implication:

- A low-bandwidth deployment could pre-load common aliases and reduce runtime RxNorm calls.

## Self-Hosting Requirements

Minimum practical self-hosting stack:

- Linux server or container runtime.
- Python 3.11+.
- Node.js 20 for frontend builds, or prebuilt `frontend/dist`.
- Postgres database.
- Environment variables for `DATABASE_URL` and optional Anthropic key.
- Process manager such as systemd, Docker, or a PaaS equivalent.
- HTTPS termination through reverse proxy or hosting platform.

Optional but important for real deployment:

- Backups.
- Monitoring.
- Secret management.
- Access control.
- Audit log storage.
- Network egress controls.

## Low-Bandwidth And Offline Limitations

| Feature | Low-bandwidth/offline behavior |
|---|---|
| Interaction checking | Works if database is local and populated |
| DDInter import | Requires local CSV files and database access |
| RxNorm normalization | Requires network unless aliases already exist |
| OpenFDA citations | Requires network unless labels are mirrored locally |
| Anthropic explanations | Requires network and paid API access |
| Frontend | Works from FastAPI static files after build |

Offline-first requirements:

- Local Postgres instance.
- Preloaded drugs and aliases.
- Imported interaction dataset.
- Local SPL/OpenFDA mirror or disabled citation fetching.
- Local or disabled LLM explanation layer.
- Clear UI warnings when optional services are unavailable.

## Future Improvements For Cost-Constrained Settings

- Add an "explanations disabled" mode that hides LLM buttons cleanly.
- Persist and reuse OpenFDA label documents to reduce API calls.
- Add importable RxNorm alias packs for common medications.
- Add a lightweight Docker Compose deployment.
- Add retention policies for old check runs and coverage rows.
- Add a low-bandwidth mode that avoids live RxNorm unless explicitly requested.
- Add usage metrics for explanation calls and token costs.

## Conservative Manuscript Wording

Safe:

"RxCheck demonstrates a cost-conscious architecture in which the core interaction check is local and deterministic, while paid or network-dependent services are optional explanation and normalization aids."

Avoid:

"RxCheck is cost-effective."

Avoid:

"RxCheck eliminates the need for commercial interaction databases."

Avoid:

"RxCheck can be safely deployed in low-resource clinical settings today."
