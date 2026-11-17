# Structify

Structify turns a Software Requirements Specification (SRS) into a structured domain model, Mermaid.js diagrams (ER, class, sequence, architecture) and a downloadable FastAPI project skeleton, using a small swarm of Gemini-powered agents.

## Overview

- **Backend (`backend/`)**: FastAPI, Hexagonal Architecture (ports and adapters). Parser → Diagrammer + Scaffolder agents, run as a background job with live progress over Server-Sent Events. Users, documents, results and jobs are stored in SQL (SQLite locally, Postgres in production).
- **Frontend (`frontend/`)**: Next.js 16 (App Router), React 19, Tailwind CSS 4. Upload a file or type requirements, watch the agent log, explore the extraction and diagrams, export PNG/ZIP.

## Features

- **Input**: upload PDF, DOCX (tables included), Markdown or text, or type requirements. With a file attached, the text box is sent as extra instructions.
- **Accounts**: sign up / sign in; every endpoint except `/health` and `/api/auth/*` requires a bearer token, and users only see their own documents.
- **Background pipeline**: `POST /api/analyze/full` returns `202` with a job id; poll `GET /api/jobs/{id}`; follow `GET /api/events/{document_id}` (SSE, per-document, with replay).
- **Diagrams**: validated Mermaid, rendered with `securityLevel: "strict"`, zoom/pan, fullscreen, PNG export.
- **Scaffold**: one LLM call per file, packaged as a ZIP named after the document id.

## Getting started

Requires **Python 3.11+** and **Node 22+**.

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # then set GEMINI_API_KEY (and JWT_SECRET_KEY)
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs. Tests: `pytest`. Lint/format: `ruff check . && black app tests`.

### Frontend

```bash
cd frontend
cp .env.example .env.local  # NEXT_PUBLIC_API_URL, default http://localhost:8000
npm install
npm run dev                 # http://localhost:3000
```

Checks: `npm run lint`, `npx tsc --noEmit`, `npm test`, `npm run build`.

## Configuration

| Variable | Where | Notes |
|---|---|---|
| `GEMINI_API_KEY` | backend | required in production |
| `JWT_SECRET_KEY` | backend | required (≥ 32 chars) when `APP_ENV=production`; in development a random one is used per process |
| `DATABASE_URL` | backend | empty = local SQLite; use Postgres in production (ephemeral disks lose SQLite data) |
| `CORS_ORIGINS` | backend | comma-separated; set to your frontend URL |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | backend | optional bootstrap account (both required) |
| `NEXT_PUBLIC_API_URL` | frontend | required for production builds |

See `backend/.env.example` for every option (limits, retention, rate limits).

## Deployment

- **Backend**: `render.yaml` (repo root) is a Render Blueprint; `backend/Dockerfile` works anywhere Docker does. Set `GEMINI_API_KEY`, `DATABASE_URL` and `CORS_ORIGINS`; `JWT_SECRET_KEY` is generated for you on Render.
- **Frontend**: Vercel; set `NEXT_PUBLIC_API_URL` to the backend URL.
- Rate limits and the event bus are in-process, so run a single backend worker (or move them to Redis before scaling out).

## Architecture

```
backend/app
├── domain/          entities, ports (abstract interfaces), errors — no outward imports
├── application/     use cases, orchestrator, job service, event bus
├── agents/          Parser, Diagrammer, Scaffolder (prompt + parsing logic)
├── infrastructure/  adapters (Gemini, file parsing, ZIP, validator), SQL persistence, FastAPI routes
└── prompts/         knowledge_anchor.md — reference rules injected per agent
```

Dependencies point inward: agents and use cases depend on ports; `infrastructure/api/dependencies.py` is the single composition root.
