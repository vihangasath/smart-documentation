# Task Plan: Development Milestones

## Phase 1: The Brain (Parser Agent)
- [x] Task 1.1: Build an upload endpoint for PDF/DOCX/Markdown/Text files (plus typed text).
- [x] Task 1.2: Integrate Gemini to extract entities.
- [x] Task 1.3: Map extracted entities to a JSON Schema (`ExtractedSchema`).

## Phase 2: The Architect (Diagrammer Agent)
- [x] Task 2.1: Convert the schema into Mermaid.js ER and Class diagrams.
- [x] Task 2.2: Convert functional flow into Mermaid.js Sequence (and Architecture) diagrams.
- [x] Task 2.3: Validate Mermaid syntax before output (heuristic validator; the browser renderer is the final check).

## Phase 3: The Builder (Scaffolder Agent)
- [x] Task 3.1: Generate a project directory tree (deterministic, per-file LLM calls).
- [x] Task 3.2: Boilerplate for `main.py`, `models.py`, `routes.py`, `config.py`, `requirements.txt`, `.env.example`.
- [x] Task 3.3: ZIP download.

## Phase 4: The Skin (UI/UX)
- [x] Task 4.1: Bento-grid dashboard.
- [ ] Task 4.2: "Border Beam" glow for active processing states.
- [ ] Task 4.3: Live-preview split screen for generated code next to diagrams (the API already returns file contents via `GET /api/scaffold/{id}`).

## Phase 5: Hardening (see plan.md)
- [x] Auth on every endpoint, per-user data, rate limits, secrets required in production.
- [x] Background jobs, per-document SSE with replay, SQL persistence, retention cleanup.
- [x] Tests (backend pytest, frontend Vitest) and CI.
- [ ] Redis-backed event bus / rate limiter for multi-worker deployments.
- [ ] Real Mermaid validation via `mermaid-cli` or a Node sidecar.
