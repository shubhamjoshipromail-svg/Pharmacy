[README.md](https://github.com/user-attachments/files/26776988/README.md)
# RxCheck

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-Claude-D97706)
![License](https://img.shields.io/badge/License-MIT-green)

A pharmacist-facing drug interaction tracker. Interaction checks run against a locally-imported clinical database — no external API is on the critical path for clinical decisions. An LLM layer produces plain-English explanations using strict RAG: structured interaction rows and FDA label excerpts are injected as context, the model is schema-validated on output, and cross-checks ensure it references only drugs present in the source data. The interesting part of the system isn't the AI — it's the data model and the boundary drawn around what the AI is allowed to do.

> ⚠️ **Prototype — not for clinical use.** This is a portfolio project running against a synthetic 50-row subset of DDInter, with no authentication and no real patient data. Do not use for actual patient care.

---

## Screenshots

*(screenshots coming soon)*

---

## Features

### Core clinical features

- **Deterministic interaction detection** across all drug pairs in a patient's active medication list, typed as DDI (drug-drug), DFI (drug-food), and DDSI (drug-disease).
- **Tiered severity display** across a 5-level internal scale: contraindicated, major, moderate, minor, unknown. Source-native severity strings preserved verbatim alongside the mapped value.
- **DDSI condition matching** — drug-disease interactions surface only when the patient has the matching active condition recorded. A patient with no conditions gets zero DDSI findings.
- **Hub drug scoring** — each drug is scored by how many interactions it participates in across the current medication list, used to rank results and identify which single drug change would reduce interaction burden most for polypharmacy patients.
- **Per-patient acknowledgment** with optional expiry. Acknowledgments snapshot the severity at the time they were granted; if the underlying severity later escalates, the ack is invalidated and the alert resurfaces.
- **Plain-English explanations** from Claude (`claude-sonnet-4-6`), grounded in the structured interaction row and optional FDA label excerpts.

### Technical architecture features

- **Offline-capable interaction checks.** The DDInter dataset is imported into SQLite at setup time. Interaction queries never hit the network.
- **Two-table interaction model.** One canonical `interactions` row per pair, N `interaction_source_assertions` rows per interaction. Findings, overrides, and acknowledgments FK to the canonical row, not to a specific source.
- **Per-source severity preservation** — never averaged. A `sources_conflict` flag surfaces when sources disagree, computed in an aggregate view.
- **Lexicographic DDI ordering** enforced by CHECK constraint (`drug_a_rxcui < drug_b_rxcui`). Eliminates duplicate (A,B)/(B,A) records at the database level.
- **RxNorm normalization pipeline** with exact match → brand lookup → trigram fuzzy match → NDC resolution → unresolved-queue fallback. Confirmed fuzzy matches are written back as aliases so repeat typos resolve instantly.
- **Source coverage logging.** A separate table records which sources were queried for which pairs and whether anything was found. Distinguishes "no interaction in our data" from "we never checked."
- **Schema designed for Postgres migration** — SQLite is the prototype substrate, but types, constraints, and extensions targets (pgcrypto, pg_trgm, citext) assume Postgres as the production target.

### Safety and audit features

- **Frozen run snapshots.** Each check run stores a JSON snapshot of the medications considered. Medications get edited and discontinued; the snapshot means the audit trail reflects what the pharmacist saw, not what the data says now.
- **Schema validation on every LLM response.** Invalid outputs are stored for failure analysis and never shown to users. 5 of 7 generated explanations passed validation in the current dataset.
- **Cross-validation** that the LLM only references drugs actually present in the structured input.
- **Append-only override log** capturing user, finding, severity-at-override, action, and optional justification.
- **Prompt template versioning** so any past explanation can be reproduced exactly.
- **HIPAA-ready schema shape.** Patient identifiers live in a 1:1 child table (`patient_identifiers`) so column-level encryption or physical separation can be added without touching any other table.

---

## Architecture

Three layers, each with a clearly delimited responsibility.

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHARMACIST (React UI)                       │
│                                                                 │
│  types drug name → reviews findings → acknowledges / overrides  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              1. NORMALIZATION LAYER (network-bound)             │
│                                                                 │
│   RxNorm REST API ─────► ingredient-level RxCUI                 │
│   exact → brand → fuzzy → NDC → unresolved queue                │
│   confirmed matches written back as aliases                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │ RxCUI
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│           2. LOCAL DATA LAYER (offline, deterministic)          │
│                                                                 │
│   SQLite ─── interactions (canonical pair)                      │
│           └─ interaction_source_assertions (per source)         │
│                    ▲                                            │
│           DDInter ─┘ (imported once, queried locally)           │
│                                                                 │
│   → returns: severity, mechanism, management, conflict flag     │
└──────────────────────────────┬──────────────────────────────────┘
                               │ structured findings
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│           3. LLM EXPLANATION LAYER (RAG-only)                   │
│                                                                 │
│   Structured finding + optional OpenFDA SPL excerpt             │
│        │                                                        │
│        ▼                                                        │
│   Claude (sonnet-4-6) ─ strict system prompt, no training-      │
│                         data answers, schema-validated output,  │
│                         drug-reference cross-check              │
│        │                                                        │
│        ▼                                                        │
│   explanation_text (shown) │ validation_errors (logged only)    │
└─────────────────────────────────────────────────────────────────┘
```

The boundary between layers 2 and 3 is the important one. Layer 2 is the source of truth and is fully deterministic; layer 3 is non-deterministic but is structurally prevented from generating clinical content that isn't already present in layer 2's output. If the LLM is offline or returns a validation failure, the pharmacist still sees the structured finding — the explanation is additive, not required.

---

## Tech stack

| Category | Technology | Purpose |
|---|---|---|
| Backend language | Python 3.12 | API server |
| API framework | FastAPI | HTTP routing, request/response validation |
| ORM | SQLAlchemy 2.x | Database access, relationship mapping |
| Validation | Pydantic v2 | Request/response schemas, LLM output validation |
| Migrations | Alembic | Schema versioning (Postgres target) |
| Database | SQLite | Prototype storage — Postgres-ready schema |
| Frontend framework | React 18 | UI |
| Build tool | Vite | Dev server, production bundling |
| Styling | Tailwind CSS | Utility-first styling |
| Routing | React Router | Client-side navigation |
| HTTP client | Axios | API calls from the frontend |
| LLM | Claude `claude-sonnet-4-6` | Plain-English explanations (RAG only) |
| Drug normalization | NIH RxNorm REST API | Name → RxCUI resolution |
| Label citations | OpenFDA REST API | SPL excerpt fetching |
| Interaction data | DDInter 2.0 (local import) | Structured drug-drug/food/disease interactions |
| Testing | pytest, httpx | Backend unit & integration tests |

---

## Getting started

### Prerequisites
- Python 3.12+
- Node 18+
- An Anthropic API key (explanations won't generate without one; the rest of the app works)

### Setup

```bash
# Clone
git clone https://github.com/<your-user>/rxcheck.git
cd rxcheck

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env — add your Anthropic API key

# Import DDInter subset and seed reference data
python -m app.scripts.import_ddinter data/ddinter_sample.csv
python -m app.scripts.seed_reference

# Run the API
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
# Frontend
cd frontend
npm install
npm run dev         # starts Vite on :5173
```

Open `http://localhost:5173`. The API is at `http://localhost:8000` with OpenAPI docs at `/docs`.

### `.env.example`

```dotenv
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6

# Database
DATABASE_URL=sqlite:///./drug_checker.db

# External APIs
RXNORM_BASE_URL=https://rxnav.nlm.nih.gov/REST
OPENFDA_BASE_URL=https://api.fda.gov

# App
APP_ENV=development
LOG_LEVEL=INFO
PROMPT_TEMPLATE_VERSION=v1

# Feature flags
ENABLE_DEV_SEED_ROUTE=true
```

---

## API reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe |
| `POST` | `/api/v1/dev/seed` | Load synthetic patients and medications (dev only; gate behind `ENABLE_DEV_SEED_ROUTE`) |
| `GET` | `/api/v1/patients` | List patients |
| `POST` | `/api/v1/patients` | Create a patient |
| `GET` | `/api/v1/patients/{patient_id}` | Fetch a patient with active medications and conditions |
| `POST` | `/api/v1/patients/{patient_id}/medications` | Add a medication; triggers RxNorm normalization |
| `DELETE` | `/api/v1/patients/{patient_id}/medications/{med_id}` | Mark a medication inactive (soft delete via `is_active`) |
| `POST` | `/api/v1/patients/{patient_id}/conditions` | Record an active condition for DDSI matching |
| `GET` | `/api/v1/patients/{patient_id}/conditions` | List a patient's conditions |
| `DELETE` | `/api/v1/patients/{patient_id}/conditions/{condition_id}` | Resolve or remove a condition |
| `POST` | `/api/v1/patients/{patient_id}/check` | Run an interaction check across all active med pairs; returns findings grouped by severity |
| `GET` | `/api/v1/patients/{patient_id}/checks` | List historical check runs for the patient |
| `POST` | `/api/v1/findings/{finding_id}/explain` | Generate (or retrieve cached) LLM explanation for a finding |
| `POST` | `/api/v1/findings/{finding_id}/override` | Record a pharmacist override with justification |
| `POST` | `/api/v1/patients/{patient_id}/interactions/{interaction_id}/acknowledge` | Acknowledge a (patient, interaction) pair; accepts optional `expires_at` |
| `DELETE` | `/api/v1/patients/{patient_id}/interactions/{interaction_id}/acknowledge` | Revoke an acknowledgment |

---

## Data sources

### NIH RxNorm
**What it is.** RxNorm is the NIH's normalized naming system for clinical drugs. It assigns a stable RxCUI (RxNorm Concept Unique Identifier) to every ingredient, brand, and clinical drug concept, and maps between them.

**What it provides.** Ingredient-level RxCUI resolution from brand names, generic names, NDCs, and fuzzy matches. Current database has 27 drugs with real RxCUIs — warfarin (11289), aspirin (1191), amiodarone (703), fluoxetine (4493), simvastatin (36567), clarithromycin (21212), and 21 others.

**How it's used.** Normalization only. Every drug entering the system is resolved to an ingredient-level RxCUI before it hits the interaction layer. RxNorm is never the interaction source.

**Limitations.** Retires concepts on a monthly cycle; our `rxnorm_synced_at` column supports staleness checks but no scheduled refresh job is implemented yet. Misses compounded medications, investigational drugs, and non-US products — those fall through to the `unresolved_drug_entries` queue.

### DDInter 2.0
**What it is.** A publicly-available database of drug interactions with structured severity, mechanism, and management guidance across DDI, DFI, and DDSI categories.

**What it provides.** 302k interaction records in the full release. The current prototype has 50 synthetic rows covering warfarin, aspirin, amiodarone, fluoxetine, simvastatin, clarithromycin, and their clinically-relevant pairs — sufficient to exercise every code path but not a real clinical dataset.

**How it's used.** Imported once into SQLite via `app.scripts.import_ddinter`. Every interaction query is answered from the local database. DDInter drug IDs are crosswalked to RxCUIs during import and stored in `drug_external_ids`.

**Limitations.** Synthetic subset currently loaded. Production deployment needs the full dataset and a re-import cadence tied to DDInter's release schedule. DDInter's severity vocabulary is mapped onto our 5-level internal scale at import time; the mapping is versioned so any change is a migration.

### OpenFDA
**What it is.** The FDA's public API for structured drug label data (Structured Product Labeling, SPL).

**What it provides.** Boxed warnings, drug interaction sections, and adverse reaction sections from approved US drug labels. Used as citation-grade evidence surfaced alongside interaction findings.

**How it's used.** Fetched on demand when a finding is explained. The SPL excerpt is included in the LLM context as evidence the model can cite. One `SPL_SET_ID` is currently persisted.

**Limitations.** Not persisted between server restarts — fetches are in-memory cached only. Production needs a local mirror table (`spl_documents` with `set_id`, `version`, `fetched_at`, JSONB blob) both to reduce API load and to keep the audit trail reproducible. Label text is not a substitute for a dedicated interaction database; OpenFDA is for citation, not classification.

---

## Key design decisions

Engineering choices and the alternatives that were rejected.

### 1. DDInter imported locally, not queried remotely
**Chosen.** Import the DDInter flat files into SQLite at setup time. All interaction queries are local.
**Alternative.** Call a drug-interaction API (First Databank, Lexicomp, or a public HTTP wrapper around DDInter) on every check.
**Why.** Clinical decision support should not depend on a third-party API being reachable, rate-limit-free, and responding in a predictable latency window. Local import makes interaction checks deterministic, offline-capable, and p99-bounded by SQLite's query planner instead of by a network. Re-imports are a controlled operation on a schedule, not an uncontrolled dependency on every check.

### 2. Two-table interaction model
**Chosen.** One canonical `interactions` row per pair, N `interaction_source_assertions` rows per source.
**Alternative.** One row per (pair, source) with no parent.
**Why.** Findings, overrides, and acknowledgments need to reference an interaction without being aware of which sources happened to assert it. With the parent row in place, those references are stable even as sources are added or removed. The per-source children make the conflict-detection view trivial: `MAX(severity)` on the enum gives worst severity, `COUNT(DISTINCT severity) > 1` gives the conflict flag.

### 3. Lexicographic pair ordering for DDIs
**Chosen.** Store DDI pairs with `drug_a_rxcui < drug_b_rxcui`, enforced by CHECK constraint.
**Alternative.** Accept both orderings, dedupe on read with `WHERE (a=X AND b=Y) OR (a=Y AND b=X)`.
**Why.** Accepting both orderings pushes complexity into every query and makes the unique index on the pair impossible. Canonicalizing on write means one index, one constraint, and callers can't accidentally create dupes. The application layer has to remember to canonicalize inputs, which is a small cost paid once at insertion.

### 4. Source coverage as a separate audit table
**Chosen.** A `source_coverage_checks` table records which sources were queried for which pairs and whether anything was found.
**Alternative.** Infer coverage from `interaction_source_assertions.imported_at`.
**Why.** Assertion timestamps only tell us when we last saw an assertion — they don't distinguish "asked DDInter today, got nothing" from "never asked DDInter about this pair." That distinction is clinically meaningful: the UI should say "checked and clear as of date X," not imply safety from the absence of a record. An explicit append-only table closes the gap.

### 5. RxNorm normalization with learning-back aliases
**Chosen.** Exact alias → brand lookup → trigram fuzzy match → NDC → unresolved queue. Confirmed fuzzy matches are written back to `drug_aliases` as `alias_kind='misspelling'` so repeat typos resolve in O(log n) instead of O(fuzzy).
**Alternative.** Call RxNorm's approximateTerm endpoint on every input.
**Why.** Pharmacist typing patterns are repetitive; the same misspellings recur. Writing them back turns a network round-trip into an index lookup after the first confirmation, and builds institutional memory of the local vocabulary. The placeholder system for unmatched drugs — inserting a synthetic `is_active=FALSE` drug row so the FK constraint holds — ensures we never silently drop an unrecognized medication from a patient's profile.

### 6. RAG-only LLM layer with schema-validated output
**Chosen.** Structured interaction rows and optional SPL excerpts are injected into the LLM context. A strict system prompt forbids answers from training data. Every response is validated against a JSON schema and cross-checked to confirm it references only drugs in the source data. Failed validations are stored but never surfaced.
**Alternative.** Ask the LLM to answer drug interaction questions directly from its training data.
**Why.** A model's training data is an unversioned, unauditable source of clinical claims. Restricting the LLM to summarizing structured rows that came from a named source with a traceable severity mapping turns the model into a presentation layer rather than a knowledge layer. If the model is wrong, the wrongness is bounded: it's either a bad paraphrase of a known source (catchable) or it mentions something not in the source data (caught by the cross-check). The 5-of-7 validation pass rate in the current dataset is itself useful signal — two rejections were worth examining, not hiding.

### 7. Hub drug scoring
**Chosen.** Score each drug by its interaction count across the patient's active medication list. Rank findings by the highest-score drug involved.
**Alternative.** Flat severity-only ranking.
**Why.** Clinical literature on polypharmacy identifies a small set of "hub" drugs (warfarin, amiodarone, certain antibiotics) that drive most of the interaction burden. Surfacing these helps the pharmacist answer "which single drug change reduces the most risk?" — a question pure severity ranking can't answer because it doesn't account for the multiplicative effect of a hub drug interacting with many others in the list.

### 8. Alert fatigue mitigation via tiered display + per-patient acknowledgments
**Chosen.** Findings are displayed in severity tiers. Pharmacists can acknowledge a specific (patient, interaction) pair to suppress it from the prominent alert tier, with optional expiry. Acknowledgments snapshot the severity-at-ack; if the underlying severity later escalates, the ack is invalidated.
**Alternative.** Show everything every time. Or: allow global suppression of interaction types.
**Why.** Pharmacists who see the same minor warning thirty times for the same patient start tuning out all warnings, which is worse than not showing the warning. Per-patient, per-pair acknowledgment with severity-escalation detection preserves the audit trail (the acknowledgment is a record, not a deletion) while reducing the noise floor. Global suppression was rejected because it removes the interaction from all patients' views — a minor interaction for one patient can be clinically significant for another.

### 9. Frozen run snapshots
**Chosen.** Each `interaction_check_runs` row stores a JSON snapshot of the medications considered. Findings snapshot the severity and source set at run time.
**Alternative.** Join back by time from current data.
**Why.** Medications are edited and discontinued. Reconstructing "what was checked on that day" by temporal joins is complex and easy to get wrong. A JSON snapshot is denormalized but unambiguous, and the audit trail is the primary consumer — it must reflect what the pharmacist actually saw, not what the data says now.

### 10. HIPAA-ready schema shape
**Chosen.** Patient identifiers (name, MRN, DOB in the future) live in a 1:1 child table `patient_identifiers`. The main `patients` table holds only clinical attributes and a UUID.
**Alternative.** One flat patient table.
**Why.** The shape lets production add column-level encryption via pgcrypto, restrict SELECT permissions on identifiers separately, or move the identifier table to a different database — all without touching any other table or query. The cost is a JOIN when full patient details are needed; most clinical screens don't need them.

### 11. DDSI condition matching as a correctness constraint
**Chosen.** Drug-disease interactions surface only when the patient has the matching active condition recorded in `patient_conditions`. Patients with no conditions get zero DDSI findings.
**Alternative.** Surface all DDSI interactions for any drug on the list, leaving the pharmacist to filter.
**Why.** This was identified as a clinical correctness bug during audit. A DDSI warning without a confirmed diagnosis is a false positive — it tells the pharmacist "this drug interacts with renal impairment" whether or not the patient has renal impairment, which is noise. Gating DDSI on recorded conditions turns the warning into a signal. This is the kind of correctness question that applies throughout the design: a warning system that cries wolf is worse than one that's silent, because it erodes trust in every other alert.

---

## Safety and compliance

### What the system does
- **Tiered severity alerts** across a 5-level scale, with the most severe tier displayed prominently and lower tiers collapsible.
- **Complete audit trail.** Every check run, finding, acknowledgment, override, and LLM explanation is persisted with user, timestamp, and context.
- **RAG grounding.** LLM explanations reference only the structured interaction data injected into context; no clinical claims from training data.
- **Schema validation.** Every LLM response is validated before display. Failed responses are logged but never shown.
- **DDSI condition matching.** Drug-disease warnings require a recorded active condition — no false positives from phantom diagnoses.
- **Soft advisory, not workflow block.** The system surfaces findings and lets the pharmacist make the decision. No prescription is prevented or auto-modified.

### What the system does not claim
- **Not a medical device.** Not FDA-cleared or FDA-registered.
- **Not a substitute for clinical judgment.** The system informs a pharmacist; it does not replace one.
- **Not a complete interaction database.** The current prototype uses a 50-row synthetic subset. Even a full DDInter import would not cover every interaction in clinical literature.
- **Not validated against a gold-standard interaction set.** No published sensitivity/specificity numbers.

### FDA Non-Device CDS orientation
The 21st Century Cures Act carves out certain clinical decision support functions from FDA device regulation when four criteria are met: the software (1) is not intended to acquire, process, or analyze medical images/signals/patterns, (2) displays, analyzes, or prints medical information normally communicated between professionals, (3) supports or provides recommendations about prevention/diagnosis/treatment, and (4) enables the provider to independently review the basis of the recommendation. RxCheck is designed with criterion 4 in mind: every recommendation surfaces the source database, the source-native severity, the mechanism, and (where available) an FDA label excerpt — the pharmacist can see the basis of every alert. This is orientation, not certification; actual Non-Device CDS classification requires legal review this project has not undergone.

### Disclaimer
> ⚠️ **Prototype — not for clinical use.** Synthetic data, no authentication, incomplete interaction dataset. Do not use for actual patient care.

---

## Production roadmap

Prioritized. Top items are closer to a real deployment; bottom items are longer-horizon.

1. **Postgres migration.** SQLite was chosen for prototype velocity. Schema is designed for Postgres — enums, CHECK constraints, and pgcrypto/pg_trgm/citext extension targets are already specified. Migration is a connection-string change plus Alembic stamping.
2. **Full DDInter dataset.** Load the full 302k-row release instead of the 50-row synthetic subset. Import pipeline already handles idempotency and quarantining.
3. **Authentication and authorization.** Users table exists but auth is unenforced. Production needs SSO or credential storage, session management, role-permission mapping, and row-level security on `patients` / `patient_identifiers`.
4. **Column-level encryption** on `patient_identifiers` via pgcrypto, with KMS-backed key management and rotation.
5. **OpenFDA persistence.** Local `spl_documents` mirror table to reduce API load and make the audit trail reproducible across server restarts.
6. **Second interaction source** to exercise the `sources_conflict` flag. DrugBank or Lexicomp, with severity-mapping versioning. The aggregate view is untested under conflict until a second source exists.
7. **Pharmacogenomics layer.** CYP enzyme polymorphisms modulate many interactions; requires patient genotype tables and per-interaction enzyme-of-interest fields.
8. **EHR integration.** FHIR endpoints for patient and medication ingestion. SMART-on-FHIR launch flow for in-EHR use.
9. **Scheduled RxNorm refresh job** to catch retired concepts on a monthly cadence.
10. **Migration-tracking cleanup.** `alembic stamp head` before any schema change lands in a deployed environment.

---

## Contributing

This is a portfolio project, but PRs are welcome — especially around the normalization layer, the LLM validation harness, and the DDInter import pipeline. Open an issue first for anything larger than a bug fix or small refactor so we can talk through the design before code lands. Tests must pass (`pytest` in `backend/`) and new behavior should come with test coverage.

---

## License

MIT. See [LICENSE](./LICENSE).
