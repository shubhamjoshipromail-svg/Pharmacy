# RxCheck

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![Postgres](https://img.shields.io/badge/Postgres-15+-4169E1?logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-CSS-38B2AC?logo=tailwindcss&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-Claude-D97706)

RxCheck is a pharmacist-facing drug interaction review prototype. It lets a user create a synthetic patient, add medications and conditions, run an interaction check, review findings grouped by severity, acknowledge alerts, override findings with a note, and optionally request an AI-generated explanation for a deterministic database finding.

The most important design boundary is this:

```text
The database decides whether an interaction exists.
The LLM only explains an interaction that was already found.
```

Interaction detection is deterministic and database-backed. RxCheck does not ask an LLM, OpenFDA, or a live third-party API whether a drug interaction exists at check time. It checks locally stored Postgres rows imported from DDInter and then optionally uses OpenFDA and Anthropic to explain the already-identified result.

> Prototype only. RxCheck is not FDA-cleared, not HIPAA-compliant, and not intended for real patient care. It currently has no authentication or authorization, limited automated tests, and incomplete clinical validation.

---

## Table Of Contents

- [What Exists Today](#what-exists-today)
- [Visual Architecture](#visual-architecture)
- [Frontend User Journey](#frontend-user-journey)
- [Backend Module Map](#backend-module-map)
- [Database](#database)
- [Data Model](#data-model)
- [Interaction Check Flow](#interaction-check-flow)
- [RxNorm Normalization](#rxnorm-normalization)
- [DDInter Import](#ddinter-import)
- [LLM Explanation Layer](#llm-explanation-layer)
- [OpenFDA Citation Fetching](#openfda-citation-fetching)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Deployment](#deployment)
- [Local Development](#local-development)
- [Testing](#testing)
- [Security And Compliance Limitations](#security-and-compliance-limitations)
- [Roadmap](#roadmap)

---

## What Exists Today

### Implemented

| Area | Current behavior | Main files |
|---|---|---|
| Backend API | FastAPI app with patient, medication, condition, check, explanation, acknowledgment, and override routes | `app/main.py`, `app/api/patients.py`, `app/api/interactions.py` |
| Database | Postgres via SQLAlchemy ORM | `app/core/config.py`, `app/db/session.py`, `app/models/` |
| Schema setup | Script enables Postgres extensions and creates expected tables | `scripts/init_db.py` |
| Medication normalization | RxNorm exact/fuzzy/NDC lookup with alias write-back and unresolved placeholder fallback | `app/services/normalization.py` |
| Placeholder handling | Unresolved drugs are stored but excluded from interaction checks | `app/models/drug.py`, `app/services/orchestrator.py` |
| DDInter import | Bulk Postgres upsert importer for real DDInter DDI flat files | `scripts/import_ddinter.py` |
| Interaction checking | Deterministic DDI/DFI/DDSI check orchestration with ranking and snapshots | `app/services/orchestrator.py` |
| DDSI condition filtering | Drug-disease interactions only fire when patient has the active matching condition | `app/services/orchestrator.py` |
| Hub score | Counts each medication's interaction burden and uses it for ranking/context | `app/services/checks.py` |
| Summaries | Pydantic summary shape for severity, short mechanism/action/effect, hub score, conflict flag | `app/schemas/interaction.py` |
| LLM explanation | Anthropic call with structured RAG context and JSON validation | `app/services/llm.py`, `app/api/interactions.py` |
| OpenFDA context | Fetches label text for explanation context, with in-memory cache | `app/services/openfda.py` |
| Review workflow | Per-patient acknowledgments suppress future findings without deleting them | `app/models/audit.py`, `app/services/orchestrator.py` |
| Override workflow | Overrides are persisted and audit events are written | `app/api/interactions.py`, `app/models/audit.py` |
| Frontend | React/Vite/Tailwind patient workflow and result review UI | `frontend/src/` |
| Deployment | Railway single-service deployment, including frontend build and FastAPI static serving | `railway.toml`, `app/main.py` |

### Partially Implemented

| Area | What exists | What is missing |
|---|---|---|
| Users and roles | `users` table has `role` values: `pharmacist`, `admin`, `readonly` | No login, sessions, JWT, route guards, or permission checks |
| Audit trail | Check runs, findings, acknowledgments, overrides, selected audit events, LLM outputs | No read-access audit, immutable event store, audit UI, or compliance-grade logging |
| LLM validation | JSON parse checks and drug-name cross-checking | No full schema validator, clinical factuality evaluator, prompt-injection sanitizer, or citation-level verification |
| OpenFDA citations | Label snippets can be fetched and placed in LLM context | No persistent SPL document table and no frontend citation panel |
| DDInter source support | Real DDI CSV importer exists | Current real-file importer does not import DFI/DDSI files or rich mechanism/management text |
| Test coverage | `/health` endpoint test exists | Clinical logic, import, frontend, LLM, and audit flows are not covered |

### Not Implemented

- Authentication.
- Authorization or role-based access control.
- HIPAA-grade encryption and access controls.
- FDA-cleared or clinically validated decision support.
- EHR, FHIR, or SMART-on-FHIR integration.
- Production-grade secret management.
- Formal source-versioning for imported interaction datasets.
- Comprehensive frontend or backend automated tests.

---

## Visual Architecture

### System Overview

```mermaid
flowchart LR
    Pharmacist["Pharmacist / Demo User"] --> UI["React + Vite Frontend"]
    UI -->|Axios /api/v1| API["FastAPI Backend"]
    API --> DB[("Postgres")]

    API -->|Medication normalization| RxNorm["NIH RxNorm REST API"]
    API -->|Label context for explanations| OpenFDA["OpenFDA Drug Label API"]
    API -->|Structured explanation request| Claude["Anthropic Claude"]

    DDInter["DDInter CSV files"] --> Importer["scripts/import_ddinter.py"]
    Importer --> DB

    API --> Static["Serves frontend/dist in production"]
```

### Runtime Decision Boundary

```mermaid
flowchart TD
    A["Patient medications + conditions"] --> B["Normalize drugs to RxCUIs"]
    B --> C["Query imported Postgres interaction tables"]
    C --> D{"Interaction found?"}
    D -->|No| E["Return no finding"]
    D -->|Yes| F["Create InteractionCheckFinding"]
    F --> G["Build deterministic summary"]
    G --> H{"User asks for AI explanation?"}
    H -->|No| I["Show structured summary only"]
    H -->|Yes| J["Fetch optional OpenFDA label excerpts"]
    J --> K["Send structured context to Claude"]
    K --> L["Parse and validate JSON"]
    L --> M["Store LLM explanation and show if usable"]
```

The LLM is downstream of deterministic detection. It cannot create a new interaction finding, change the canonical interaction row, or change the severity stored by the check run.

### Deployment Shape

```mermaid
flowchart TB
    Repo["GitHub repo"] --> Railway["Railway build"]
    Railway --> Build1["pip install -r requirements.txt"]
    Railway --> Build2["Install Node.js 20"]
    Railway --> Build3["cd frontend && npm install && npm run build"]
    Build1 --> Start["uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
    Build3 --> Start
    Start --> Health["/health"]
    Start --> API["/api/v1/*"]
    Start --> SPA["React SPA at /"]
```

---

## Frontend User Journey

```mermaid
sequenceDiagram
    actor User as Pharmacist / Demo User
    participant UI as React UI
    participant API as FastAPI
    participant DB as Postgres
    participant Rx as RxNorm
    participant LLM as Anthropic

    User->>UI: Click Load Demo
    UI->>API: POST /api/v1/dev/seed
    API->>Rx: Normalize seed medications if not aliased
    API->>DB: Create patient, meds, conditions, check run
    API-->>UI: InteractionCheckResult
    UI-->>User: Show grouped findings

    User->>UI: Expand finding
    User->>UI: Click Get AI Explanation
    UI->>API: POST /api/v1/findings/{finding_id}/explain
    API->>DB: Load finding + source assertions
    API->>LLM: Send structured context
    LLM-->>API: JSON explanation
    API->>DB: Store llm_explanation
    API-->>UI: LlmExplanationResult
    UI-->>User: Show explanation

    User->>UI: Mark as Reviewed
    UI->>API: POST /patients/{id}/interactions/{id}/acknowledge
    API->>DB: Store acknowledgment + audit event
    UI->>API: POST /patients/{id}/check
    API-->>UI: Same interaction now suppressed=true
```

Primary screens:

| Screen | Route | Purpose |
|---|---|---|
| Patient list | `/` | Load demo patient, create patient, list existing patients |
| Patient detail | `/patients/:patientId` | Manage conditions, manage medications, run checks, review findings |

Key UI behaviors:

- Resolved medication badges show a green checkmark.
- Unresolved placeholder medications show an amber exclamation badge.
- Conditions are displayed as removable pills.
- Results are grouped by severity.
- Suppressed/reviewed interactions appear in a collapsible reviewed section.
- Interaction cards expand to show explanation, review, and override actions.

---

## Backend Module Map

```text
app/
├── api/
│   ├── patients.py       # Patient, medication, condition, check, seed routes
│   └── interactions.py   # Explain, override, acknowledge routes
├── core/
│   └── config.py         # Pydantic settings and env vars
├── db/
│   └── session.py        # SQLAlchemy engine, SessionLocal, Base, get_db
├── models/
│   ├── drug.py           # Drug, aliases, external IDs, unresolved queue
│   ├── interaction.py    # Food, condition, interactions, assertions, coverage checks
│   ├── patient.py        # Users, patients, identifiers, conditions, medications
│   ├── check.py          # Check runs, findings, LLM explanations
│   ├── audit.py          # Acknowledgments, overrides, audit events
│   └── enums.py          # Severity, type, source, normalization, override enums
├── schemas/
│   ├── interaction.py    # Summaries, LLM result, ack/override schemas
│   └── patient.py        # Patient, medication, condition, check history schemas
├── services/
│   ├── normalization.py  # RxNorm normalization
│   ├── orchestrator.py   # Main interaction check logic
│   ├── checks.py         # Hub score helper
│   ├── openfda.py        # FDA label retrieval
│   └── llm.py            # Anthropic explanation generation
└── main.py               # App creation, CORS, routers, health, static frontend
```

---

## Database

RxCheck currently uses Postgres, not SQLite.

Evidence in the codebase:

| Evidence | Meaning |
|---|---|
| `app/core/config.py` | `DATABASE_URL` defaults to a Postgres URL and reads env vars |
| `app/db/session.py` | SQLAlchemy engine uses `settings.DATABASE_URL` with pooling |
| `requirements.txt` | Includes `psycopg2-binary` and `asyncpg` |
| `scripts/init_db.py` | Enables `pgcrypto`, `pg_trgm`, and `citext` |
| `app/models/check.py` | Uses Postgres `ARRAY`, `JSONB`, and `UUID` |
| `app/models/interaction.py` | Uses Postgres `JSONB` and `UUID` |
| `scripts/import_ddinter.py` | Uses psycopg2 bulk insert and Postgres `ON CONFLICT` |

SQLite is not currently interchangeable by only changing `DATABASE_URL`. The project originally started with SQLite, and a stale local `drug_checker.db` may still exist, but the active code path is Postgres-oriented.

To make SQLite interchangeable again, the project would need:

- Conditional SQLAlchemy column types for `JSONB`, `ARRAY`, and `UUID`.
- SQLite-compatible alternatives to Postgres-specific `ON CONFLICT` statements in scripts.
- A separate import path that does not require psycopg2.
- Config defaults that do not hardcode a Postgres host.
- Test coverage proving both database backends behave the same.

---

## Data Model

### Entity Relationship Overview

```mermaid
erDiagram
    DRUGS ||--o{ DRUG_ALIASES : has
    DRUGS ||--o{ DRUG_EXTERNAL_IDS : has
    DRUGS ||--o{ PATIENT_MEDICATIONS : referenced_by
    PATIENTS ||--o{ PATIENT_MEDICATIONS : has
    PATIENTS ||--o{ PATIENT_CONDITIONS : has
    CONDITIONS ||--o{ PATIENT_CONDITIONS : referenced_by
    DRUGS ||--o{ INTERACTIONS : drug_a
    DRUGS ||--o{ INTERACTIONS : drug_b
    FOODS ||--o{ INTERACTIONS : food
    CONDITIONS ||--o{ INTERACTIONS : condition
    INTERACTIONS ||--o{ INTERACTION_SOURCE_ASSERTIONS : has
    PATIENTS ||--o{ INTERACTION_CHECK_RUNS : has
    INTERACTION_CHECK_RUNS ||--o{ INTERACTION_CHECK_FINDINGS : has
    INTERACTIONS ||--o{ INTERACTION_CHECK_FINDINGS : found_as
    INTERACTIONS ||--o{ LLM_EXPLANATIONS : explained_by
    LLM_EXPLANATIONS ||--o{ INTERACTION_CHECK_FINDINGS : linked_to
    INTERACTIONS ||--o{ INTERACTION_ACKNOWLEDGMENTS : acknowledged_as
    INTERACTION_CHECK_FINDINGS ||--o{ INTERACTION_OVERRIDES : overridden_by
```

### Table Inventory

| Table | Model | Purpose |
|---|---|---|
| `drugs` | `Drug` | Canonical drug concepts keyed by RxCUI |
| `drug_aliases` | `DrugAlias` | Local alias lookup for typed names, brands, synonyms, misspellings |
| `drug_external_ids` | `DrugExternalId` | External identifiers such as SPL set IDs |
| `unresolved_drug_entries` | `UnresolvedDrugEntry` | Queue/history for medication names that could not be normalized |
| `foods` | `Food` | Food concepts for DFI interactions |
| `conditions` | `Condition` | Condition concepts for DDSI interactions |
| `interactions` | `Interaction` | Canonical interaction row for DDI, DFI, DDSI, or duplication |
| `interaction_source_assertions` | `InteractionSourceAssertion` | Source-level assertion, raw severity, normalized severity, raw payload |
| `source_coverage_checks` | `SourceCoverageCheck` | Records that a source was checked for a pair |
| `users` | `User` | Placeholder user/role records; not authentication |
| `patients` | `Patient` | Patient shell record, currently synthetic by default |
| `patient_identifiers` | `PatientIdentifier` | Optional patient name/MRN/external ID fields |
| `patient_conditions` | `PatientCondition` | Patient-condition links with onset/resolution dates |
| `patient_medications` | `PatientMedication` | Medication list entries and normalization status |
| `interaction_check_runs` | `InteractionCheckRun` | One persisted interaction-check event |
| `interaction_check_findings` | `InteractionCheckFinding` | One finding per interaction in a run |
| `llm_explanations` | `LlmExplanation` | Stored LLM explanation, structured input, validation result, token usage |
| `interaction_acknowledgments` | `InteractionAcknowledgment` | Per-patient interaction review/suppression records |
| `interaction_overrides` | `InteractionOverride` | Override actions attached to findings |
| `audit_events` | `AuditEvent` | Selected audit events for acknowledgments and overrides |

### Important Constraints

| Constraint or index | Why it matters |
|---|---|
| DDI ordering check: `drug_a_rxcui < drug_b_rxcui` | Prevents duplicate `(A, B)` vs `(B, A)` interactions |
| Unique DDI index on type + drug pair | Prevents duplicate DDI canonical rows |
| Unique DFI index on type + drug + food | Prevents duplicate drug-food rows |
| Unique DDSI index on type + drug + condition | Prevents duplicate drug-disease rows |
| Unique assertion key `(interaction_id, source, source_record_id)` | Keeps repeated imports idempotent for assertions |
| Unique patient condition key | Avoids duplicate condition links for same patient/onset |
| Unique finding key `(run_id, interaction_id)` | Prevents duplicate findings within one check run |
| `is_placeholder` on `drugs` | Allows unresolved medication records while excluding them from checks |

---

## Interaction Check Flow

The main orchestrator is `run_interaction_check()` in `app/services/orchestrator.py`.

### Step-by-Step Logic

| Step | What happens | Why it exists |
|---|---|---|
| 1 | Load active patient medications joined to `drugs` | Gets current medication list |
| 2 | Exclude `Drug.is_placeholder = true` | Prevents unverified drugs from creating misleading checks |
| 3 | Return early if fewer than 2 meds | DDI pair checking requires at least two drugs |
| 4 | Generate canonical RxCUI pairs | Matches DB ordering and avoids pair duplication |
| 5 | Batch query DDI interactions | Avoids one query per pair |
| 6 | Query DFI interactions for active drugs | Food interactions can apply broadly |
| 7 | Query DDSI interactions for active drugs plus active patient conditions | Prevents false disease alerts |
| 8 | Load source assertions | Needed for severity and summary construction |
| 9 | Build summaries | Creates frontend-friendly clinical snapshot |
| 10 | Rank summaries | Severe, conflicting, hub-drug findings appear first |
| 11 | Apply acknowledgment suppression | Reviewed findings remain visible but collapsible |
| 12 | Persist run and findings | Creates audit trail and enables LLM explanations |
| 13 | Return `InteractionCheckResult` | Frontend renders grouped result panel |

### DDI, DFI, DDSI Behavior

| Type | Database representation | When it appears |
|---|---|---|
| DDI | `interaction_type='DDI'`, `drug_a_rxcui`, `drug_b_rxcui` | When both drugs are active patient medications |
| DFI | `interaction_type='DFI'`, `drug_a_rxcui`, `food_id` | When the drug is active; does not require patient profile food entry |
| DDSI | `interaction_type='DDSI'`, `drug_a_rxcui`, `condition_id` | Only when the patient has matching active `patient_conditions` row |

### Result Shape

The API returns an `InteractionCheckResult`:

```json
{
  "run_id": "uuid",
  "patient_id": "uuid",
  "total_medications": 6,
  "total_pairs_checked": 15,
  "total_interactions_found": 4,
  "critical_count": 0,
  "major_count": 2,
  "moderate_count": 2,
  "minor_count": 0,
  "suppressed_count": 0,
  "warning": null,
  "summaries": [],
  "checked_at": "2026-06-09T00:00:00",
  "duration_ms": 123
}
```

Each summary includes:

- Severity and severity label/color.
- Drug A name and drug B/food/condition name.
- Interaction type.
- Brief mechanism, effect, and action strings.
- Source conflict flag.
- Max severity.
- Hub scores.
- LLM explanation presence.
- Suppression state.
- Finding ID and interaction ID.

---

## RxNorm Normalization

Implemented in `app/services/normalization.py`.

### Normalization Flow

```mermaid
flowchart TD
    A["Raw input: Tylenol, warfaron, NDC"] --> B["Clean input"]
    B --> C{"Local alias match?"}
    C -->|Yes| D["Return matched_exact or matched_brand"]
    C -->|No| E["RxNorm exact /rxcui.json search=2"]
    E --> F{"Exact hit?"}
    F -->|Yes| G["Resolve to ingredient RxCUI"]
    F -->|No| H["RxNorm approximateTerm fuzzy search"]
    H --> I{"Top score > 8?"}
    I -->|Yes| J["Auto-resolve matched_fuzzy"]
    I -->|No| K{"Score 4-8?"}
    K -->|Yes| L["Return candidates for confirmation"]
    K -->|No| M{"Looks like NDC?"}
    M -->|Yes| N["RxNorm NDC lookup"]
    M -->|No| O["Create unresolved entry + placeholder drug"]
    N --> P{"NDC hit?"}
    P -->|Yes| Q["Return matched_ndc"]
    P -->|No| O
```

### Normalization Status Values

| Status | Meaning |
|---|---|
| `matched_exact` | Local alias or RxNorm exact match |
| `matched_brand` | Brand/tradename resolved to ingredient |
| `matched_fuzzy` | RxNorm approximate-term match |
| `matched_ndc` | NDC resolved through RxNorm |
| `unmatched` | Placeholder drug created |
| `manual_override` | Enum exists, but no complete manual override flow is implemented |

### Placeholder Convention

If a drug cannot be resolved, RxCheck creates:

- A row in `unresolved_drug_entries`.
- A synthetic `drugs` row with `is_placeholder = true`.
- A `patient_medications` row pointing to that placeholder.

Placeholder drugs stay visible in the UI but are excluded from interaction checks at the orchestrator level. This avoids silently dropping a medication from the patient profile while also avoiding false confidence in interaction results involving an unverified drug.

---

## DDInter Import

The current importer is `scripts/import_ddinter.py`.

### Input Files

The importer expects real DDInter files at:

```text
/Users/shubhamjoshi/Desktop/pharmacy/ddinter/
```

Files:

| File | Imported by current script |
|---|---|
| `ddinter_downloads_code_A.csv` | Yes |
| `ddinter_downloads_code_B.csv` | Yes |
| `ddinter_downloads_code_D.csv` | Yes |
| `ddinter_downloads_code_H.csv` | Yes |
| `ddinter_downloads_code_L.csv` | Yes |
| `ddinter_downloads_code_P.csv` | Yes |
| `ddinter_downloads_code_R.csv` | Yes |
| `ddinter_downloads_code_V.csv` | Yes |

Expected columns:

```text
DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level
```

### Import Pipeline

```mermaid
flowchart TD
    A["Load all CSV files with pandas"] --> B["Load drug_aliases + drugs into alias_map"]
    B --> C["Resolve Drug_A and Drug_B in memory"]
    C --> D{"Both drugs resolved?"}
    D -->|No| E["Quarantine row"]
    D -->|Yes| F["Canonicalize RxCUI pair"]
    F --> G["Map severity"]
    G --> H["Bulk upsert interactions"]
    H --> I["Fetch pair -> interaction_id map"]
    I --> J["Bulk upsert interaction_source_assertions"]
    J --> K["Bulk insert source_coverage_checks"]
    K --> L["Print counts, severity distribution, hub score table"]
```

### Severity Mapping

| Raw DDInter level | Stored severity |
|---|---|
| `Major` | `major` |
| `Moderate` | `moderate` |
| `Minor` | `minor` |
| Anything else | `unknown` |

### Idempotency

The importer is safe to rerun for interactions and assertions:

- `interactions` uses `ON CONFLICT (interaction_type, drug_a_rxcui, drug_b_rxcui) DO NOTHING`.
- `interaction_source_assertions` uses `ON CONFLICT (interaction_id, source, source_record_id) DO NOTHING`.

Coverage checks are currently appended rather than deduplicated. That is useful for recording repeated coverage checks, but it means the table can grow across repeated imports.

### Current Import Limitations

- The current real DDInter importer imports DDI files only.
- It does not currently import DFI or DDSI from real DDInter files.
- It does not currently import rich mechanism or management text from those real files because the inspected CSV structure only provides severity level columns.
- If a drug name is missing from local aliases/preferred names, the row is quarantined rather than live-normalized.

---

## LLM Explanation Layer

Implemented in `app/services/llm.py` and exposed by:

```text
POST /api/v1/findings/{finding_id}/explain
```

### Explanation Flow

```mermaid
flowchart TD
    A["Finding ID"] --> B["Load InteractionCheckFinding"]
    B --> C{"Already has llm_explanation_id?"}
    C -->|Yes| D["Return existing explanation"]
    C -->|No| E["Load interaction + assertions"]
    E --> F["Fetch OpenFDA labels for both drugs if available"]
    F --> G["Build structured RAG context"]
    G --> H["Call Anthropic Claude"]
    H --> I["Parse JSON"]
    I --> J["Validate required keys"]
    J --> K["Cross-check drug mentions"]
    K --> L["Persist LlmExplanation"]
    L --> M["Link finding.llm_explanation_id"]
    M --> N["Return LlmExplanationResult"]
```

### Data Sent To The LLM

The LLM receives structured text built from:

- Drug A name.
- Drug B, food, or condition name.
- Interaction type.
- Severity and source list.
- Mechanism text from source assertion, if available.
- Management text from source assertion, if available.
- First 500 characters of OpenFDA drug interaction label text for each drug, if available.

It does not receive:

- The full patient chart.
- Full condition history.
- Full medication history.
- Arbitrary database access.
- Instructions to decide whether an interaction exists.

### Expected LLM JSON

```json
{
  "summary": "One sentence overview of the interaction",
  "mechanism": "Plain English mechanism explanation",
  "clinical_effect": "What actually happens to the patient",
  "management": "What the pharmacist should do",
  "severity_rationale": "Why this severity rating is appropriate",
  "sources_used": ["DDInter", "FDA label"],
  "confidence": "high"
}
```

### Validation And Storage

The service:

- Parses the model output as JSON.
- Checks required fields.
- Ensures `sources_used` is a list.
- Cross-checks drug mentions against the interaction drugs.
- Stores raw model output even if validation fails.
- Stores prompt version, structured input, latency, token usage, and validation errors.

### LLM Safety Limitations

The implementation is intentionally constrained, but not clinically sufficient:

- Prompt-injection defenses are limited.
- FDA label text is not sanitized beyond being placed in context.
- Citation verification is not sentence-by-sentence.
- The schema parser is custom, not a formal clinical evaluator.
- Failed Anthropic network calls are not queued or persisted as failed jobs.

---

## OpenFDA Citation Fetching

Implemented in `app/services/openfda.py`.

### Lookup Order

```mermaid
flowchart TD
    A["RxCUI"] --> B{"Stored SPL_SET_ID?"}
    B -->|Yes| C["Search OpenFDA by spl_set_id"]
    B -->|No| D["Search OpenFDA by openfda.rxcui"]
    D --> E{"Found?"}
    E -->|No| F["Search OpenFDA by generic_name"]
    E -->|Yes| G["Extract label sections"]
    C --> G
    F --> G
    G --> H["Persist SPL_SET_ID if found"]
    H --> I["Cache in memory for server session"]
```

### Extracted Label Fields

| Field | Purpose |
|---|---|
| `drug_interactions` | Primary label section for interaction explanation context |
| `warnings` | Additional safety context |
| `warnings_and_precautions` | Additional safety context |
| `boxed_warning` | High-risk label warning context |
| `contraindications` | Contraindication context |

OpenFDA does not determine interaction existence. It is context for explanation only.

---

## API Reference

Base path: `/api/v1`

### System

| Method | Endpoint | Response |
|---|---|---|
| `GET` | `/health` | `{"status": "ok", "app": "Drug Interaction Tracker"}` |

### Patients

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/patients` | List all patients with active medication count and latest check timestamp |
| `POST` | `/api/v1/patients` | Create a synthetic patient |
| `GET` | `/api/v1/patients/{patient_id}` | Fetch one patient with medications |

### Conditions

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/patients/{patient_id}/conditions` | List active conditions |
| `POST` | `/api/v1/patients/{patient_id}/conditions` | Add or reactivate condition |
| `DELETE` | `/api/v1/patients/{patient_id}/conditions/{condition_id}` | Set `resolved_date`; does not hard delete |

### Medications

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/patients/{patient_id}/medications` | Add medication, normalize with RxNorm |
| `DELETE` | `/api/v1/patients/{patient_id}/medications/{med_id}` | Set `is_active=false`; does not hard delete |

### Checks

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/patients/{patient_id}/check` | Run interaction check and persist run/findings |
| `GET` | `/api/v1/patients/{patient_id}/checks` | List past check runs newest first |

### Demo

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/dev/seed` | Create synthetic patient with demo meds/conditions and immediately run check |

Seed medications:

- warfarin
- aspirin
- amiodarone
- fluoxetine
- simvastatin
- clarithromycin

Seed conditions:

- renal impairment
- pregnancy
- QT prolongation

### Interaction Review

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/findings/{finding_id}/explain` | Generate or return existing LLM explanation |
| `POST` | `/api/v1/findings/{finding_id}/override` | Create override and audit event |
| `POST` | `/api/v1/patients/{patient_id}/interactions/{interaction_id}/acknowledge` | Create acknowledgment and audit event |
| `DELETE` | `/api/v1/patients/{patient_id}/interactions/{interaction_id}/acknowledge` | Deactivate most recent active acknowledgment |

---

## Frontend

The frontend lives in `frontend/`.

### Component Map

| Component | Responsibility |
|---|---|
| `App.jsx` | Defines React Router routes |
| `Layout.jsx` | Fixed sidebar and main content outlet |
| `PatientList.jsx` | Demo seed button, create patient form, patient cards |
| `PatientDetail.jsx` | Two-column patient workspace, conditions, medications, check runner |
| `MedicationList.jsx` | Medication rows, resolved/unverified badges, remove button |
| `AddMedicationForm.jsx` | Medication input, candidate picker, warning/error display |
| `InteractionResults.jsx` | Result counts, severity grouping, suppressed section |
| `InteractionCard.jsx` | Expandable card, explanation call, review call, override form |
| `SeverityBadge.jsx` | Severity label styling |
| `api.js` | Axios client with `baseURL: '/api/v1'` |

### UI Layout

```text
┌──────────────────────┬───────────────────────────────────────────────────────┐
│ Sidebar              │ Main content                                           │
│                      │                                                       │
│ RxCheck              │ Patient list OR patient detail                         │
│ Drug tracker         │                                                       │
│                      │ Patient detail:                                       │
│ Patients             │ ┌──────────────────────┬────────────────────────────┐ │
│                      │ │ Left column          │ Right column               │ │
│ Prototype warning    │ │ Patient header       │ Interaction results        │ │
│                      │ │ Conditions           │ Severity groups            │ │
│                      │ │ Medications          │ Expandable cards           │ │
│                      │ │ Add med/check button │ AI explanation/review      │ │
│                      │ └──────────────────────┴────────────────────────────┘ │
└──────────────────────┴───────────────────────────────────────────────────────┘
```

### Badge Semantics

| Badge | Meaning |
|---|---|
| Green checkmark | Drug verified against NIH RxNorm database |
| Amber exclamation | Drug could not be verified; interactions may be incomplete |

### Severity Colors

| Severity | UI treatment |
|---|---|
| `contraindicated` | Red badge/card border |
| `major` | Orange badge/card border |
| `moderate` | Yellow badge/card border |
| `minor` | Blue badge/card border |
| `unknown` | Gray badge/card border |

---

## Deployment

Railway deployment is configured in `railway.toml`.

```toml
[build]
buildCommand = "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs && pip install -r requirements.txt && cd frontend && npm install && npm run build && cd .."

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
```

FastAPI serves the frontend with this behavior:

- If `frontend/dist` exists, `/` returns `index.html`.
- `/assets/*` serves built static assets.
- Non-API unknown paths fall back to `index.html` for React Router.
- API, docs, health, redoc, and OpenAPI paths are not intercepted by the SPA fallback.

Production environment variables:

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string |
| `APP_NAME` | Optional | FastAPI app title and health response |
| `DEBUG` | Optional | FastAPI debug flag |
| `ANTHROPIC_API_KEY` | Only for explanations | Enables LLM explanation endpoint |
| `ANTHROPIC_MODEL` | Optional | Anthropic model name |

Important deployment note:

Database credentials were hardcoded during prototyping in some config/script files. Rotate those credentials before any public or production use, and rely only on environment variables.

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20 recommended
- Postgres database
- Optional Anthropic API key

### Install Backend Dependencies

```bash
cd drug-checker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Example `.env`:

```dotenv
DATABASE_URL=postgresql://postgres:password@host:5432/railway
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
DEBUG=True
APP_NAME=Drug Interaction Tracker
```

Initialize database:

```bash
python scripts/init_db.py
```

Run backend:

```bash
uvicorn app.main:app --reload --port 8000
```

### Run Frontend Separately

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

### Run Single-Domain Local Build

```bash
cd frontend
npm install
npm run build
cd ..
uvicorn app.main:app --reload --port 8000
```

Open:

```text
http://localhost:8000
```

---

## Testing

Run:

```bash
pytest
```

Current committed pytest coverage is minimal. The existing test verifies only the `/health` endpoint.

Manual verification scripts:

| Script | Purpose |
|---|---|
| `scripts/init_db.py` | Enable Postgres extensions, create tables, verify expected table list |
| `scripts/import_ddinter.py` | Import DDInter files and print import summary |
| `scripts/test_llm.py` | Start a seed/explain workflow against a running local server |

Recommended next tests:

- RxNorm normalization fixtures.
- Placeholder-drug exclusion from checks.
- DDI canonical pair ordering.
- DDSI condition filtering.
- DFI behavior independent of patient conditions.
- Acknowledgment suppression and severity escalation.
- Override creation and audit event creation.
- DDInter import idempotency.
- OpenFDA fetch failure handling.
- LLM JSON validation and failed-output handling.
- Frontend smoke tests for demo seed, add/remove medication, add/remove condition, explanation, review, and override.

---

## Security And Compliance Limitations

RxCheck currently does not implement:

- Login.
- Session management.
- Authorization or route-level role checks.
- Encryption of patient identifiers.
- Row-level security.
- Read-access audit logs.
- Immutable audit log protections.
- Secret rotation.
- HIPAA policies or BAA-backed controls.
- CSRF protection strategy.
- Strict production CORS policy.

The schema has some compliance-friendly shape, especially separate `patient_identifiers` and audit-related tables, but the application is not HIPAA-ready.

### Sensitive Data Fields

The current schema can store sensitive data if real patient data is entered:

| Table | Sensitive fields |
|---|---|
| `patient_identifiers` | `given_name`, `family_name`, `mrn`, `external_patient_id` |
| `patients` | `date_of_birth`, `sex_at_birth`, `weight_kg` |
| `patient_medications` | Medication list, dose, route, frequency, notes |
| `patient_conditions` | Conditions, onset/resolution dates, notes |
| `audit_events` | User actions and payloads |

Do not enter real patient data into this prototype.

---

## What Claims Are Safe To Make

Safe claims:

- RxCheck is a working pharmacist-facing prototype.
- It uses Postgres as the current database.
- It deterministically checks imported interaction rows.
- It excludes placeholder drugs from interaction checks.
- It filters DDSI interactions by active patient conditions.
- It stores check runs and findings as snapshots.
- It supports acknowledgment suppression and override logging.
- It can generate LLM explanations for existing findings when Anthropic is configured.
- It serves a React frontend from FastAPI for single-domain Railway deployment.

Do not claim:

- HIPAA compliance.
- FDA clearance.
- Complete interaction coverage.
- Clinical validation.
- Authenticated pharmacist workflow.
- Production-ready audit compliance.
- That SQLite is the current backend.
- That the LLM detects interactions.

---

## Roadmap

### Near-Term Engineering

- Rotate/remove committed database secrets and rely only on environment variables.
- Add authentication and route-level authorization.
- Add tests around the orchestrator, DDSI filtering, normalization, and audit flows.
- Add frontend audit-history views.
- Persist OpenFDA label documents in a dedicated table.
- Add better error handling and retries around RxNorm, OpenFDA, and Anthropic calls.

### Data And Clinical Quality

- Add source-version metadata for DDInter imports.
- Add richer mechanism/management import if source files provide it.
- Add DFI/DDSI real-data import support.
- Add a second interaction source to exercise conflict handling.
- Add source/evidence display in the frontend.
- Add formal validation against a reference interaction dataset.

### Deployment And Compliance

- Add production-grade secret management.
- Add encrypted patient identifiers.
- Add access logs and monitoring.
- Add backup/restore documentation.
- Harden CORS and CSRF behavior.
- Add EHR/FHIR integration only after core safety and auth work is complete.

---

## Repository Layout

```text
drug-checker/
├── app/
│   ├── api/
│   │   ├── interactions.py
│   │   └── patients.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   └── session.py
│   ├── models/
│   │   ├── audit.py
│   │   ├── check.py
│   │   ├── drug.py
│   │   ├── enums.py
│   │   ├── interaction.py
│   │   └── patient.py
│   ├── schemas/
│   │   ├── interaction.py
│   │   └── patient.py
│   ├── services/
│   │   ├── checks.py
│   │   ├── llm.py
│   │   ├── normalization.py
│   │   ├── openfda.py
│   │   └── orchestrator.py
│   └── main.py
├── frontend/
│   ├── src/
│   └── dist/
├── scripts/
│   ├── import_ddinter.py
│   ├── init_db.py
│   └── test_llm.py
├── tests/
│   └── test_health.py
├── requirements.txt
├── railway.toml
├── Procfile
└── README.md
```

---

## License

No explicit license file is currently committed in the project root. Add one before publishing or distributing the project.
