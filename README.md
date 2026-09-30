# CivicFlow

**Policy-aware decision intelligence for public-service case operations.**

CivicFlow is a full-stack case-management prototype that combines retrieval-augmented generation, deterministic policy checks, tool permissions, an independent **Decision Challenge**, human approval gates, and policy-version replay.

**Live demo:** https://civicflow-wkvj.vercel.app  
**API:** https://civicflow-api.vercel.app  
**API docs:** https://civicflow-api.vercel.app/docs

> CivicFlow uses fully synthetic case data and synthetic policy content. It is a portfolio/demo system, not a production public-benefits system.

---

## Why CivicFlow

Public-service case workflows often involve a mix of:

- structured case records,
- policy text,
- ambiguous citizen requests,
- actions with very different risk levels,
- and decisions that should not be delegated to an LLM alone.

CivicFlow separates those responsibilities.

The model can classify a request and propose an action, but that proposal must still pass:

1. policy retrieval and citation validation,
2. deterministic policy rules,
3. tool-permission checks,
4. an independent Decision Challenge for consequential actions,
5. and human approval when required.

Read-only actions can execute without unnecessary approval, while consequential actions are stopped when evidence is incomplete or routed to a human before execution.

---

## Recruiter Demo

The live site contains three curated cases, each designed to demonstrate a different workflow.

| Case | Scenario | Expected behavior |
|---|---|---|
| `CF-10001` | Safe payment-status check | Policy allowed → read-only tool executes |
| `CF-10002` | Investigation with insufficient evidence | Policy consideration allowed → Decision Challenge blocks → human review |
| `CF-10003` | Investigation with required evidence established | Decision Challenge passes → pending human approval |

### Demo 1 — Safe read-only automation

Use `CF-10001` and submit:

```text
My housing assistance payment has not arrived. Can you check what happened?
```

Expected path:

```text
Payment Issue
→ Check Payment
→ Deterministic Policy Gate: Allowed
→ Read-only tool
→ No human approval required
→ Check Payment executes
```

### Demo 2 — Decision Challenge blocks a consequential action

Use `CF-10002` and submit:

```text
My housing assistance payment is missing. Please open a formal investigation into why I have not received it.
```

Expected path:

```text
Payment Issue
→ Open Investigation
→ Deterministic Policy Gate: Allowed for consideration
→ Decision Challenge: Challenge
→ Missing evidence surfaced
→ Human review
→ No approval or state-changing execution
```

### Demo 3 — Human approval gate

Use `CF-10003` and submit the same investigation request:

```text
My housing assistance payment is missing. Please open a formal investigation into why I have not received it.
```

Expected path:

```text
Payment Issue
→ Open Investigation
→ Deterministic Policy Gate: Allowed
→ Decision Challenge: Pass
→ State-changing action
→ Human approval required
→ Pending approval created
```

The **Approvals** page can then be used to approve or reject the pending action.

> Current scope: CivicFlow records approval decisions, but the state-changing `open_investigation` handler itself is not executed after approval in this prototype.

---

## Core Features

### Policy-aware RAG

Policy text is chunked, embedded, stored in PostgreSQL with `pgvector`, and retrieved for each request.

CivicFlow validates that model citations refer only to retrieved policy chunks before allowing the workflow to continue.

### Deterministic policy gate

Policy-sensitive actions are checked by deterministic rules rather than relying only on model reasoning.

Examples include:

- active-case requirements,
- payment-state requirements,
- policy-section requirements,
- and action-specific eligibility.

### Decision Challenge

Consequential recommendations are independently challenged before they can reach an approval or state-changing tool.

The challenge receives:

- case facts,
- relevant case-history events,
- the proposed action,
- and retrieved policy evidence.

It can surface missing evidence, policy conflicts, timing requirements, or unsupported assumptions.

### Human-in-the-loop approvals

Consequential actions that pass safety checks can create pending approvals.

A reviewer can approve or reject them from the live dashboard.

### Tool permissions

CivicFlow distinguishes between:

- **read-only tools**, which can execute without unnecessary approval, and
- **state-changing actions**, which require additional safeguards.

### Policy Replay

Policy Replay evaluates the same case facts under different deterministic policy versions without rerunning the LLM.

The live demo compares `HA-PAY v1` with `HA-PAY v2`, making policy-driven outcome changes visible without model drift.

### Synthetic evaluation suite

CivicFlow includes a deterministic synthetic evaluation suite separate from the three live recruiter cases.

Current evaluation dataset:

- **24 synthetic cases**
- **6 policy-replay outcome changes**
- **18 unchanged replay outcomes**

Control checks:

| Control | Result |
|---|---:|
| Invalid citation blocking | 16 / 16 |
| Decision Challenge enforcement | 12 / 12 |
| Human approval gating | 12 / 12 |
| Read-only execution | 16 / 16 |
| **Total** | **56 / 56** |

These metrics measure **designed deterministic control-flow behavior**, not LLM accuracy or real-world policy correctness.

---

## Architecture

```mermaid
flowchart TD
    U[Recruiter / Caseworker] --> FE[React + TypeScript<br/>Vercel]

    FE --> API[FastAPI<br/>Vercel]

    API --> GRAPH[LangGraph Workflow]

    GRAPH --> CLASSIFY[Intent Classification<br/>OpenAI]
    GRAPH --> RAG[Policy Retrieval]
    GRAPH --> FACTS[Structured Case Facts]

    RAG --> EMB[OpenAI Embeddings]
    EMB --> DB[(Neon PostgreSQL<br/>pgvector)]
    DB --> RAG

    GRAPH --> RECOMMEND[Grounded Recommendation<br/>OpenAI]

    RECOMMEND --> CITATION[Citation Validation]
    CITATION --> POLICY[Deterministic Policy Gate]

    POLICY -->|Read-only| TOOL[Tool Permission Gate]
    TOOL --> READONLY[Read-only Tool Execution]

    POLICY -->|Consequential| CHALLENGE[Decision Challenge<br/>OpenAI]

    CHALLENGE -->|Challenge| REVIEW[Human Review]
    CHALLENGE -->|Pass| APPROVAL[Human Approval Gate]

    APPROVAL -->|Pending| REVIEW
    APPROVAL -->|Approved| AUTH[Authorization Recorded]

    DB --> GRAPH

    REPLAY[Policy Replay Engine<br/>Deterministic] --> DB
    EVAL[Synthetic Evaluation Suite<br/>Deterministic] --> GRAPH
```

A more detailed architecture note is available in [`docs/architecture.md`](docs/architecture.md).

---

## Request Flow

For a typical case-analysis request:

```text
Citizen request
→ Load case context
→ Classify intent
→ Retrieve relevant policy
→ Build structured facts
→ Generate grounded recommendation
→ Validate citations
→ Deterministic policy check
→ Tool permission check
→ Decision Challenge if consequential
→ Human approval if required
→ Audit / response
```

The key design principle is that **recommendation is not authorization**.

---

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Vercel

### Backend

- Python 3.12
- FastAPI
- Pydantic
- LangGraph
- SQLAlchemy

### AI

- OpenAI for live classification, recommendation, challenge, and embeddings
- structured model outputs
- policy-grounded prompts

### Data

- Neon serverless PostgreSQL
- `pgvector`
- synthetic case, payment, document, approval, event, and policy data

### Testing & Evaluation

- pytest
- deterministic stub providers
- synthetic evaluation dataset
- policy-version replay

---

## Data Model

CivicFlow uses synthetic records for:

- citizens,
- cases,
- payments,
- documents,
- case events,
- approvals,
- audit logs,
- and policy chunks.

Representative case context:

```text
Citizen
└── Case
    ├── Payments
    ├── Documents
    ├── Case Events
    ├── Approvals
    └── Audit Events
```

Policy chunks contain versioned policy text plus vector embeddings for semantic retrieval.

---

## Policy Replay

The replay engine currently includes synthetic `HA-PAY` policy versions.

### HA-PAY v1

An active case with a missing payment can be considered for investigation.

### HA-PAY v2

The candidate version adds an approved address-verification requirement.

Replay keeps the underlying case facts fixed and evaluates both policy versions deterministically.

This makes changed outcomes attributable to **policy**, not model randomness.

---

## Evaluation Design

The evaluation suite intentionally uses deterministic providers for control-flow testing.

It verifies that CivicFlow:

- blocks recommendations containing invalid policy citations,
- prevents challenged consequential actions from creating approvals or executing tools,
- stops approval-requiring actions at a pending human approval,
- allows eligible read-only actions to execute without unnecessary approval,
- and produces repeatable policy-replay results.

This is intentionally separate from model-quality evaluation.

---

## Local Development

### 1. Clone the repository

```bash
git clone https://github.com/YKadari/civicflow.git
cd civicflow
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```powershell
pip install -r requirements-dev.txt
```

### 4. Start local PostgreSQL

```powershell
docker compose up -d
```

### 5. Configure environment variables

Create a local `.env` based on `.env.example`.

For the original local stack:

```env
AI_PROVIDER=local
DATABASE_URL=postgresql+psycopg://civicflow:civicflow_dev@localhost:5432/civicflow
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
AI_CONFIDENCE_THRESHOLD=0.70
POLICY_SIMILARITY_THRESHOLD=0.50
```

For the hosted OpenAI configuration, set the appropriate OpenAI provider variables and a PostgreSQL connection string.

Never commit real API keys or database credentials.

### 6. Seed local data

From `backend/`:

```powershell
python -m scripts.seed_database
```

### 7. Start FastAPI

From `backend/`:

```powershell
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### 8. Start the frontend

From `frontend/`:

```powershell
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## Tests

Run from the repository root:

```powershell
python -m pytest
```

Frontend production build:

```powershell
cd frontend
npm run build
```

> Do not run the destructive test/seed workflow while `DATABASE_URL` points at the live Neon demo database.

---

## Deployment

The live project uses:

```text
Frontend   → Vercel
Backend    → Vercel FastAPI
Database   → Neon PostgreSQL + pgvector
AI         → OpenAI
```

Public endpoints:

- Frontend: https://civicflow-wkvj.vercel.app
- API: https://civicflow-api.vercel.app
- Swagger: https://civicflow-api.vercel.app/docs

Secrets such as the OpenAI API key and Neon database URL are stored as Vercel environment variables and are not exposed to the frontend.

---

## Repository Structure

```text
civicflow/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── ai/
│   │   ├── api/
│   │   ├── approvals/
│   │   ├── database/
│   │   ├── domain/
│   │   ├── evaluation/
│   │   ├── policies/
│   │   ├── replay/
│   │   ├── tools/
│   │   └── main.py
│   ├── scripts/
│   ├── index.py
│   └── requirements.txt
├── frontend/
│   └── src/
├── data/
├── docs/
├── tests/
├── docker-compose.yml
├── pyproject.toml
├── requirements-dev.txt
└── README.md
```

---

## Safety and Scope

CivicFlow is designed around several explicit constraints:

- synthetic data only,
- policy-grounded recommendations,
- retrieved-citation validation,
- deterministic checks for policy-sensitive actions,
- independent challenge of consequential recommendations,
- human approval before consequential state changes,
- and clear separation between recommendation and authorization.

The current prototype is not intended for real benefits adjudication or production government use.

---

## Project Status

Implemented:

- [x] Synthetic case-management database
- [x] FastAPI API
- [x] OpenAI integration
- [x] Policy RAG with `pgvector`
- [x] LangGraph workflow
- [x] Deterministic policy engine
- [x] Read-only tool execution
- [x] Human approval workflow
- [x] Decision Challenge
- [x] Policy Replay
- [x] 24-case synthetic evaluation dataset
- [x] 56 deterministic safety/workflow checks
- [x] React dashboard
- [x] Neon deployment
- [x] Vercel frontend and API deployment

Current prototype limitation:

- state-changing investigation authorization is recorded after approval, but a production state-changing investigation handler is not implemented.

---

## What I Learned

CivicFlow was built to explore how agentic systems can safely operate around policy-sensitive workflows.

The project reinforced several design lessons:

- retrieval quality is only one part of grounded decision-making,
- model recommendations should not directly authorize consequential actions,
- deterministic controls are useful for invariants that should not depend on model behavior,
- independent challenge steps can catch missing evidence that a primary recommendation overlooks,
- human approval is most useful when applied selectively rather than to every action,
- and policy replay can separate policy-driven decision changes from model variability.
