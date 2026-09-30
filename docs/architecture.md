# CivicFlow Architecture

CivicFlow is a policy-aware case-management prototype designed around a simple principle:

> **A model recommendation is not authorization.**

The system separates model reasoning, policy retrieval, deterministic validation, tool permissions, challenge logic, and human approval into distinct stages.

---

## Production Architecture

```mermaid
flowchart LR
    USER[Recruiter / Caseworker]

    subgraph Vercel
        FE[React + TypeScript<br/>Vite Frontend]
        API[FastAPI API]
    end

    subgraph Orchestration
        GRAPH[LangGraph]
        CLASSIFY[Intent Classification]
        FACTS[Fact Builder]
        RECOMMEND[Grounded Recommendation]
        CITE[Citation Validation]
        POLICY[Deterministic Policy Gate]
        CHALLENGE[Decision Challenge]
        TOOLGATE[Tool Permission Gate]
        APPROVAL[Human Approval]
    end

    subgraph OpenAI
        CHAT[Chat Model]
        EMB[Embedding Model]
    end

    subgraph Neon
        PG[(PostgreSQL)]
        VEC[(pgvector Policy Chunks)]
    end

    USER --> FE
    FE --> API
    API --> GRAPH

    GRAPH --> CLASSIFY
    CLASSIFY --> CHAT

    GRAPH --> FACTS
    GRAPH --> VEC
    VEC --> EMB

    GRAPH --> RECOMMEND
    RECOMMEND --> CHAT

    RECOMMEND --> CITE
    CITE --> POLICY

    POLICY -->|Read-only action| TOOLGATE
    TOOLGATE -->|Read-only| EXEC[Read-only Tool Execution]

    POLICY -->|Consequential action| CHALLENGE
    CHALLENGE --> CHAT

    CHALLENGE -->|Challenge| REVIEW[Human Review]
    CHALLENGE -->|Pass| TOOLGATE

    TOOLGATE -->|Approval required| APPROVAL
    APPROVAL -->|Pending| REVIEW
    APPROVAL -->|Approved| AUTH[Authorization Recorded]

    PG --> GRAPH
    GRAPH --> PG
    VEC --> GRAPH
```

---

## Analysis Workflow

```mermaid
flowchart TD
    START[Citizen Request]
    LOAD[Load Case Context]
    CLASSIFY[Classify Intent]
    RETRIEVE[Retrieve Policy Evidence]
    FACTS[Build Structured Facts]
    RECOMMEND[Recommend Action]
    CITE[Validate Policy Citations]
    POLICY[Deterministic Policy Check]
    ACCESS{Tool Access Mode}
    CHALLENGE[Decision Challenge]
    APPROVAL[Create Pending Approval]
    EXECUTE[Execute Read-only Tool]
    REVIEW[Human Review]
    END[Return Decision Trace]

    START --> LOAD
    LOAD --> CLASSIFY
    CLASSIFY --> RETRIEVE
    RETRIEVE --> FACTS
    FACTS --> RECOMMEND
    RECOMMEND --> CITE

    CITE -->|Invalid citation| REVIEW
    CITE -->|Valid| POLICY

    POLICY -->|Blocked| REVIEW
    POLICY -->|Allowed| ACCESS

    ACCESS -->|Read-only| EXECUTE
    ACCESS -->|Consequential| CHALLENGE

    CHALLENGE -->|Challenge| REVIEW
    CHALLENGE -->|Pass| APPROVAL

    EXECUTE --> END
    APPROVAL --> END
    REVIEW --> END
```

---

## Why the Decision Challenge Is Separate

The primary recommendation model is asked:

```text
What action best addresses the citizen's request,
given the available case facts and retrieved policy?
```

The Decision Challenge is asked a different question:

```text
What could make this consequential recommendation
unsafe, premature, unsupported, or inconsistent
with policy?
```

This separation lets CivicFlow preserve useful recommendations without allowing the first model call to authorize its own action.

The challenge can identify:

- missing timing evidence,
- unsupported assumptions,
- verification requirements,
- contradictory policy language,
- missing case facts,
- or premature state changes.

---

## Fact Separation

CivicFlow intentionally distinguishes between recommendation facts and challenge facts.

### Recommendation facts

The recommendation stage receives structured case facts such as:

- case status,
- payment state,
- payment scheduled date,
- document review status,
- and retrieved policy evidence.

### Challenge facts

The challenge stage receives those facts plus relevant case-history events.

That allows the challenge to use richer timing and verification history without changing the recommendation behavior.

---

## Tool Safety Model

CivicFlow tools are registered with metadata such as:

```text
action
access_mode
requires_approval
handler
```

### Read-only example

`check_payment`

```text
access_mode = read_only
requires_approval = false
```

Eligible read-only actions can execute without the Decision Challenge or human approval.

### Consequential example

`open_investigation`

```text
access_mode = state_changing
requires_approval = true
```

Consequential actions must pass the Decision Challenge and stop at a human approval gate.

---

## Policy Retrieval

Policy documents are:

1. loaded,
2. split into policy chunks,
3. embedded,
4. stored in PostgreSQL with `pgvector`,
5. retrieved semantically for a citizen request,
6. passed to the recommendation model,
7. and citation-validated before execution can continue.

Representative policy evidence:

```text
HA-PAY v1
├── 4.1 Payment Schedule
├── 4.2 Missing Payments
└── 4.4 Payment Investigation
```

The model may cite only chunk IDs returned by the retriever.

---

## Policy Replay

Policy Replay intentionally does not use the LLM.

It takes:

```text
same case facts
+
baseline policy version
+
candidate policy version
```

and evaluates both versions deterministically.

```mermaid
flowchart LR
    CASE[Fixed Case Facts]
    BASE[HA-PAY v1]
    CAND[HA-PAY v2]
    OUT1[Baseline Outcome]
    OUT2[Candidate Outcome]
    DIFF[Change Classification]

    CASE --> BASE
    CASE --> CAND
    BASE --> OUT1
    CAND --> OUT2
    OUT1 --> DIFF
    OUT2 --> DIFF
```

Current change classifications include:

- unchanged,
- newly blocked,
- newly allowed.

This helps distinguish **policy impact** from model drift.

---

## Evaluation Architecture

The evaluation suite is deliberately deterministic.

It uses synthetic cases and controlled providers to test CivicFlow's control flow independently of live-model randomness.

```mermaid
flowchart TD
    DATA[24 Synthetic Cases]
    STUBS[Deterministic Providers]
    GRAPH[CivicFlow Workflow]
    METRICS[Safety / Workflow Metrics]

    DATA --> GRAPH
    STUBS --> GRAPH
    GRAPH --> METRICS

    METRICS --> CITE[Invalid Citation Blocking<br/>16/16]
    METRICS --> CHAL[Challenge Enforcement<br/>12/12]
    METRICS --> APP[Approval Gating<br/>12/12]
    METRICS --> READ[Read-only Execution<br/>16/16]
```

Total deterministic control checks:

```text
56 / 56
```

These results do not claim that the live LLM is 100% accurate.

---

## Data Layer

Core synthetic entities:

```mermaid
erDiagram
    CITIZEN ||--o{ CASE : owns
    CASE ||--o{ PAYMENT : has
    CASE ||--o{ DOCUMENT : has
    CASE ||--o{ CASE_EVENT : has
    CASE ||--o{ APPROVAL : has
    CASE ||--o{ AUDIT_LOG : has

    POLICY_CHUNK {
        string chunk_id
        string policy_id
        int version
        string section
        text content
        vector embedding
    }
```

Neon hosts:

- structured case data,
- approvals,
- events,
- audit records,
- and vectorized policy chunks.

---

## Live Deployment

```text
Browser
  ↓
Vercel — React / Vite
  ↓
Vercel — FastAPI
  ├── OpenAI — classification / recommendation / challenge
  ├── OpenAI — embeddings
  └── Neon — PostgreSQL + pgvector
```

Public endpoints:

- Frontend: https://civicflow-wkvj.vercel.app
- API: https://civicflow-api.vercel.app
- Swagger: https://civicflow-api.vercel.app/docs

---

## Current Scope Boundary

The current prototype records human authorization for consequential actions but does not implement the post-approval state-changing `open_investigation` tool handler.

That boundary is deliberate in the current portfolio version: the project demonstrates policy-aware recommendation, safety controls, and authorization without presenting an unimplemented downstream operational workflow as complete.
