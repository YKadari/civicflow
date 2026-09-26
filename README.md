# CivicFlow

CivicFlow is a policy-aware case-management platform designed to assist public-service caseworkers with reviewing cases, retrieving policy, recommending actions, and identifying potentially problematic decisions before they are executed.

## Core Features

### Agentic Case Processing
CivicFlow analyzes incoming case requests, retrieves relevant case information and policy, and recommends structured actions.

### Decision Challenge
Before consequential actions are executed, CivicFlow independently challenges the proposed decision using policy requirements, case evidence, timelines, and similar historical cases.

### Policy Replay
Policy changes can be replayed across synthetic cases to determine which decisions or outcomes may be affected by a new policy version.

### Human-in-the-Loop Review
High-risk, conflicting, or challenged decisions are routed to a human reviewer before execution.

### Auditability
CivicFlow records important workflow events, supporting traceability from the original request through the final action.

## Current Architecture

CivicFlow is being developed incrementally using:

- Python
- FastAPI
- PostgreSQL
- pgvector
- LangGraph
- Next.js
- Local AI models during development
- Amazon Bedrock for optional AWS deployment

All case data used by the project is synthetic.

## Development Status

CivicFlow is currently under active development.

### Part 1 — Foundation
- [x] Repository structure
- [x] Python virtual environment
- [x] Core domain models
- [x] Basic automated tests
- [ ] GitHub repository

### Planned
- Synthetic case database
- FastAPI backend
- Policy retrieval/RAG
- Agent workflow
- Tool execution
- Policy validation
- Human approval workflow
- Decision Challenge
- Policy Replay
- Web interface
- Evaluation
- AWS deployment

## Project Structure

```text
civicflow/
├── backend/
│   └── app/
│       └── domain/
├── data/
├── docs/
├── frontend/
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```