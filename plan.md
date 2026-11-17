# Structify: Fix Plan

A review of every tracked file in the repo (backend, frontend, deployment config and docs), done on 2026-11-17.
Each item lists **what is wrong**, **where it is**, and **the fix**. The items are grouped by priority:

- **P0**: security holes or core features that are broken. Fix these first.
- **P1**: correctness bugs that produce wrong or failed output.
- **P2**: robustness, performance and deployment problems.
- **P3**: code quality, architecture drift, docs and tests.

Some findings were checked directly against the code:
- `MermaidValidator().validate()` returns `False` for a valid `erDiagram` (`Unclosed brackets detected`).
- `npx eslint src` reports 6 errors and 1 warning.
- `npx tsc --noEmit` passes.
- `backend/.env` has no `JWT_SECRET_KEY`, so the default secret is in use.

---

## P0: Critical

### 0.1 All pipeline endpoints are unauthenticated
**Where:** `backend/app/infrastructure/api/routes/{upload,analyze,diagrams,scaffold,events}.py`
**Problem:** Only `/api/auth/me` checks a token. Anyone who knows the backend URL can upload files and run the Gemini pipeline, which burns your API quota. They can also read other users' diagrams and scaffolds, or download their ZIPs, by `document_id`. The login screen only guards the UI.
**Fix:**
1. Add a `get_current_user` dependency to `dependencies.py`. It reads `HTTPBearer`, calls `AuthUseCase.get_current_user`, and returns 401 on `AuthError`.
2. Apply it to every router except `auth` and `/health`, using `APIRouter(dependencies=[Depends(get_current_user)])` or per-route parameters.
3. Store `owner_id` on `SRSDocument` (and on the schema, diagram and scaffold records). Return 404 when `owner_id != current_user.id`.
4. Frontend: send `Authorization: Bearer <token>` on every call (upload, analyze, scaffold download). Put this in a shared `apiFetch` helper (see 3.10).
5. SSE (`EventSource`) can't set headers. Either issue a short-lived, document-scoped stream token (`/api/events?token=…`), or replace `EventSource` with `fetch()` plus a `ReadableStream` reader that sends the header.
6. ZIP download: a plain `<a href>` can't send the header. Use `fetch` → `blob` → `URL.createObjectURL` → click, or use a signed one-time URL.

### 0.2 Hardcoded admin account and default JWT secret
**Where:** `backend/app/main.py:31-46`, `backend/app/config.py:56-59`, `backend/render.yaml`, `backend/.env.example`
**Problem:**
- Every deployment seeds an admin account whose email and password are in source, and prints them to the logs.
- `jwt_secret_key` defaults to a public string, and neither `.env` nor `render.yaml` sets it. Anyone can forge a valid JWT for any user id.
**Fix:**
- Remove the admin seeding. If you need a bootstrap user, read `ADMIN_EMAIL` and `ADMIN_PASSWORD` from the environment, only seed when both are set, and never log the password.
- Make `jwt_secret_key` required with no default. Fail at startup when it's missing or shorter than 32 characters while `APP_ENV=production`.
- Add `JWT_SECRET_KEY` to `.env.example` and to `render.yaml` (`generateValue: true`).
- Rotate the secret once this ships, which invalidates all existing tokens.

### 0.3 XSS through Mermaid rendering
**Where:** `frontend/src/components/MermaidDiagram.tsx:28-54`
**Problem:**
- `securityLevel: "loose"` lets diagram code run click handlers and arbitrary HTML labels. The diagram code is LLM output that is steered by an uploaded document, so prompt injection becomes script execution.
- The error fallback is worse. It writes the raw `chart` string into `innerHTML` without escaping, so a diagram containing `<img src=x onerror=…>` runs immediately and can steal the JWT from `localStorage`.
**Fix:**
- Use `securityLevel: "strict"`.
- In the fallback, build a `<pre>` and set `textContent` instead of `innerHTML`.
- Optionally sanitize the rendered SVG with DOMPurify (`USE_PROFILES: { svg: true }`) before inserting it.
- Longer term, consider an httpOnly cookie for the token so that an XSS can't read it.

### 0.4 Typed requirements are never sent to the backend
**Where:** `frontend/src/app/page.tsx:25-29`, `frontend/src/components/InputPanel.tsx:168-182`, `backend/app/infrastructure/api/routes/analyze.py`
**Problem:** The textarea says "Or simply explain your requirements here", but `handleGenerate` only works with an uploaded `documentId`. If you type text without uploading, you get "Please upload an SRS document first". If you upload and then edit the text or add "extra instructions", the edits are thrown away, because the backend re-reads the original file from disk.
**Fix:**
- Backend: add `POST /api/documents/text` taking `{ content: str, filename?: str }`. It creates an `SRSDocument` with `file_type=TEXT` and stores `content` directly. Add an optional `instructions: str` to `AnalyzeRequest` and pass it through `Orchestrator` → `ParserAgent._build_prompt(additional_context=…)`.
- `ParseSRSUseCase`: skip file parsing when `document.content` is already set.
- Frontend: on Generate, if there is no document but there is text, create a text document first. If there is a document, send the textarea contents as `instructions`. Disable the Generate button until one of the two exists, instead of calling `alert()`.

### 0.5 Scaffold ZIPs collide across users, and the ZIP path can escape its folder
**Where:** `backend/app/infrastructure/adapters/zip_builder.py:28-47`
**Problem:**
- The ZIP is saved as `OUTPUTS_DIR/{project_name}.zip`, and `project_name` comes from the LLM. Two documents with the same name overwrite each other, so one user downloads another user's project. `backend/outputs/generated-project.zip` already exists: that's the fallback name every failed run shares.
- A `project_name` or file `path` such as `../../x` (reachable through prompt injection in the SRS) writes outside `OUTPUTS_DIR` and produces zip-slip entries.
**Fix:**
- Name the file `OUTPUTS_DIR / f"{scaffold.document_id}.zip"`.
- Slugify `project_name` (`[A-Za-z0-9._-]`, max 64 characters) before using it as the archive root.
- For each `gen_file.path`, normalise with `PurePosixPath`. Reject absolute paths and any path with a `..` part.
- Keep `filename=` in `FileResponse` for the user-facing name only.

---

## P1: Correctness

### 1.1 The Mermaid validator rejects every ER diagram (and other valid ones)
**Where:** `backend/app/infrastructure/adapters/mermaid_validator.py:73-87`
**Problem:**
- The bracket-balance check counts the `{` and `}` in crow's-foot cardinality (`||--o{`, `}o--||`). Every ER diagram is flagged as invalid, triggers an unnecessary retry LLM call, and is still returned with `is_valid=False`.
- Parentheses and brackets inside quoted labels and notes cause false errors too.
- `first_line.startswith("graph")` also matches words like `graphics`.
**Fix:**
- Strip quoted strings, `%%` comments and relationship operators (the regex `[|}o][|o]?(--|\.\.)[|o]?[|{o]`) before the balance check, or drop the balance check for `erDiagram`.
- Match the header with `re.match(r"^(classDiagram|erDiagram|sequenceDiagram|flowchart|graph|stateDiagram(-v2)?|architecture-beta|…)\b", first_line)`.
- Best option: validate for real by running `@mermaid-js/mermaid-cli` (`mmdc`) or `mermaid.parse()` through a small Node sidecar. Keep the heuristic only as a fallback.
- Add unit tests covering one valid diagram of each type (see 3.1).

### 1.2 LLM JSON output is fragile; responses get truncated or come back empty
**Where:** `backend/app/agents/parser_agent.py`, `scaffolder_agent.py`, `infrastructure/adapters/gemini_llm_adapter.py`
**Problem:**
- `gemini-2.5-flash` is a "thinking" model, so thinking tokens can use up `max_output_tokens`. The scaffolder must fit six complete files inside one JSON string within 8,192 tokens, so it often truncates. The JSON parse then fails and the user silently gets a ZIP that holds only a README with the raw text.
- `response.text` can be `None` (for example, on `MAX_TOKENS` or a safety block). `.strip()` then raises `AttributeError`.
- In `ScaffolderAgent._parse_response`, `cleaned.index("\n")` raises `ValueError` when there's no newline. Unlike the parser, it also doesn't handle text before the JSON.
**Fix:**
- Use Gemini structured output by passing `response_mime_type="application/json"` and a `response_schema` built from the Pydantic models (`ExtractedSchema`, `ProjectScaffold`). This removes the hand-written fence stripping and brace hunting.
- Set `thinking_config=types.ThinkingConfig(thinking_budget=…)` explicitly, and raise `max_output_tokens` for the scaffolder. Better still, generate the scaffold **one file per call**, or render deterministic templates (Jinja) from the schema and call the LLM only for the parts that need it.
- In the adapter, treat a `None` or empty `response.text` as an error, and include `finish_reason` in the message.
- When parsing fails, surface it as an `AGENT_ERROR` event and as a response error. Don't return a fake "successful" scaffold.

### 1.3 The knowledge anchor pollutes every prompt
**Where:** `knowledge_anchor.md`, `backend/app/agents/base_agent.py`, `backend/app/config.py:23`
**Problem:**
- The anchor file is a meta-prompt ("Here is a comprehensive system design prompt that you can copy and paste…", "[INSERT YOUR SPECIFIC SYSTEM REQUIREMENTS…]", "Please provide a detailed architectural breakdown…"). It's prepended to every call, including the "return ONLY JSON" calls, and its instructions conflict with theirs.
- It's resolved as `BASE_DIR.parent / "knowledge_anchor.md"`, which is outside `backend/`. The Docker build context is `backend/`, so in the container the file is missing and silently replaced with `""`.
**Fix:**
- Rewrite it as a plain reference of rules with no "you"-instructions and no placeholders.
- Move it into `backend/app/prompts/knowledge_anchor.md` so it ships with the backend.
- Only inject the sections each agent needs: the Mermaid rules for the Diagrammer, the architecture rules for the Parser and Scaffolder.
- Log a warning at startup if the file is missing.

### 1.4 SSE logs show every user's events and can miss the first ones
**Where:** `backend/app/application/event_bus.py`, `routes/events.py`, `frontend/src/components/AgentLogs.tsx`, `frontend/src/app/page.tsx:34-35`
**Problem:**
- The event bus is global, and `/api/events` streams **all** events from all users. The `documentId` prop is accepted but ignored (`AgentLogs({ isProcessing })`).
- The frontend opens the stream only when `isProcessing` becomes true, and uses a `setTimeout(1000)` to "hope" it connects first.
- `onerror` calls `eventSource.close()`, which turns off the browser's automatic reconnect.
- The timestamp on each log line is `new Date()` at render time, not the event's time.
- The subscriber queues are unbounded.
**Fix:**
- Add `GET /api/events/{document_id}`. It checks ownership, then filters `event.document_id == document_id`.
- Keep a short per-document replay buffer (a `deque(maxlen=200)`) so a late subscriber gets the earlier events.
- Use `asyncio.Queue(maxsize=…)` and drop the oldest event when full.
- Frontend: connect when a `documentId` exists (not after a delay), let `EventSource` reconnect, close it after `pipeline_complete` or `pipeline_error`, and display `data.timestamp`.
- Remove the 1-second sleep.

### 1.5 The full pipeline runs inside a single HTTP request
**Where:** `routes/analyze.py:/analyze/full`, `orchestrator.py`, `gemini_llm_adapter.py:67-71`
**Problem:**
- Parse, then 3 diagrams (up to 6 calls with retries), then the scaffold all run sequentially in one request. On a 429, the adapter sleeps 30 s and then 60 s per call.
- A request can easily take several minutes. Hosting proxies (Render, Vercel, Cloudflare) cut the connection, the frontend shows "Pipeline failed", and the work completes server-side with nobody waiting for it.
**Fix:**
- Make `/analyze/full` return `202 { job_id }` right away and run the pipeline with `asyncio.create_task` (or a real queue such as RQ, Celery or Arq once storage is shared).
- Add `GET /api/jobs/{id}` for status and results. The SSE stream drives the UI, and the final result is fetched when `pipeline_complete` arrives.
- Generate the 3 diagrams concurrently with `asyncio.gather`, behind a semaphore to respect rate limits.
- Make the retry policy configurable. Use exponential backoff with jitter, honour `retry-after` when it's present, and also retry 500, 503 and timeout errors (right now only 429 is retried).

### 1.6 File parsing problems
**Where:** `backend/app/infrastructure/adapters/file_parser_adapter.py`, `routes/upload.py`
**Problem:**
- `.txt` and `.md` files are read as strict UTF-8, so a Windows-1252 file crashes with `UnicodeDecodeError` (shown as a 422).
- DOCX parsing ignores **tables**, and SRS documents often keep requirements in tables.
- PyMuPDF and python-docx are synchronous and block the event loop.
- Scanned PDFs produce empty text, and nothing stops the LLM from receiving an empty SRS.
- The whole upload is read into memory before the size check.
- `file.filename` is used in the on-disk path without sanitising it.
**Fix:**
- Decode with `errors="replace"`, or detect the encoding with `charset-normalizer`.
- Iterate `document.tables` and emit rows as `cell | cell` lines.
- Wrap the parsers in `await asyncio.to_thread(...)`.
- After parsing, if the content is under about 50 characters, fail with a clear message ("No extractable text, the file may be a scan").
- Stream the upload in chunks and abort once the limit is exceeded.
- Save the file as `UPLOADS_DIR / f"{document.id}{suffix}"` and keep the original name only in the entity.
- Truncate or chunk very long SRS text to the model's context budget, and warn the user when you do.

### 1.7 Frontend: the diagram panel re-mounts on every render
**Where:** `frontend/src/components/MermaidPanel.tsx:62-158` (ESLint `react-hooks/static-components` errors at lines 173, 176 and 208)
**Problem:** `HeaderControls` and `DiagramArea` are components defined inside the render function. Every state change (for example `isDownloading`) creates new component types, so React unmounts `MermaidDiagram` and mounts it again. Zoom and pan reset, the diagram re-renders, and for a moment the SVG the PNG export needs is gone.
**Fix:** Move both components to module scope and pass props, or inline them as JSX variables. In the same pass:
- Reset `selectedDiagramIndex` to 0 when `data` changes.
- Show `is_valid=false` diagrams with a warning badge and the `validation_errors`.

### 1.8 Frontend: Mermaid render race and PNG export bugs
**Where:** `frontend/src/components/MermaidDiagram.tsx`
**Problem:**
- `render()` is async with no cancellation. When you switch diagrams or themes quickly, a slower earlier render can overwrite a newer one.
- `mermaid.initialize` runs on every render.
- In the PNG export:
  - `downloadPng` resolves before `img.onload` runs, so the "Saving…" state means nothing.
  - There's no `img.onerror`.
  - The PNG object URL is never revoked.
  - `style.height = "none"` is invalid CSS.
  - SVGs with `<foreignObject>` (HTML labels) taint the canvas, so `toBlob` throws in Safari and Firefox.
- Unused import `Maximize` (lint warning).
**Fix:**
- Use a `let cancelled = false` flag in the effect's cleanup.
- Call `initialize` once per theme change.
- Wrap the export in a `Promise` that resolves or rejects on `onload` and `onerror`.
- Revoke both URLs.
- Use `htmlLabels: false` in the Mermaid config (or offer an SVG download as well) so canvas export works everywhere.

### 1.9 Frontend: smaller UI bugs
- `InputPanel.tsx:78`: `accept` includes `.doc`/`application/msword`, which the backend always rejects. Remove them.
- `InputPanel.tsx:116`: the "uploaded successfully" card shows only for PDF and DOCX. Uploads of `.md` and `.txt` show no confirmation. Show the card for every type.
- `InputPanel.tsx:98-106`: a long error message overflows the header badge. Show errors below the upload zone instead.
- `login/page.tsx`, `signup/page.tsx`: `await res.json()` throws on non-JSON error pages (for example a 502 while Render cold-starts), and the user sees a confusing parse error. Use `res.json().catch(() => ({}))` and a friendly message. Also redirect to `/` when the user is already logged in.
- `page.tsx`: `alert()` for errors. Replace it with an inline error or toast.
- `pipelineData` is typed as `any`. Define a `PipelineResponse` type (see 3.10).
- `ExtractionPanel.tsx`: uses `key={e.name}`/`key={attr.name}`, but the LLM can return duplicate names. Use `${name}-${i}`.
- `ThemeContext.tsx`: the page flashes the wrong theme on load because the `dark` class is only applied after hydration. Add a tiny inline script in `layout.tsx` that sets the class before paint (the same thing `next-themes` does). This also fixes the two ESLint errors in that file (`set-state-in-effect` and `applyTheme` used before it's declared).
- `AuthContext.tsx:46`: ESLint `set-state-in-effect`. Initialise `isLoading` from whether a token exists in a lazy `useState` initialiser.

---

## P2: Robustness, scalability, deployment

### 2.1 All state is in memory
**Where:** `in_memory_user_store.py`, `routes/upload.py:_documents`, `routes/analyze.py:_schemas/_diagram_sets/_scaffolds`, `event_bus.py`
**Problem:**
- Every restart wipes all users, documents and results. Render's free plan restarts on every idle spin-down, so users have to sign up again and their old tokens return 401 ("User not found").
- The stores grow without limit, which is a memory leak.
- It breaks completely with more than one worker (`gunicorn` is already in requirements.txt).
**Fix:**
- Add a persistence adapter behind the existing ports, for example a `SqlUserStore` (SQLite locally, Postgres on Render or Neon) using SQLModel or SQLAlchemy.
- Add `DocumentRepositoryPort` and `ResultRepositoryPort` to replace the module-level dicts.
- Put a TTL on results, or a "my projects" list per user.
- Move the event bus to Redis pub/sub once there's more than one process.

### 2.2 Uploaded and generated files are never cleaned up
**Where:** `backend/uploads/` (18 files locally), `backend/outputs/`
**Fix:** Add a periodic cleanup task in `lifespan` that deletes files older than N hours, or delete the upload once parsing succeeds. Note: `project_constitution.md` says agents must never delete user-uploaded SRS files. Decide whether that rule is about agents only (keep it) or about retention too (update the constitution).

### 2.3 Rate limiting and abuse controls
**Problem:** Nothing limits signup, login brute-force attempts or pipeline runs.
**Fix:** Add `slowapi` (or a middleware) with limits per IP on `/api/auth/*`, and per user on `/api/analyze*` (for example 5 per hour). Add a cap on concurrent pipelines per user.

### 2.4 Auth hardening
- `python-jose` is effectively unmaintained and has had CVEs. Switch to `PyJWT`.
- `bcrypt` handles at most 72 bytes; newer versions raise an error on longer passwords and older ones silently truncate. Add `max_length=72` (in bytes) to `SignupRequest.password`.
- Email validation is a hand-written `"@" in v` check. Use `pydantic.EmailStr` (`email-validator`).
- `signup` checks password length twice (in the schema and in the route). Keep only the schema check.
- Signup returns `409 "An account with '<email>' already exists"`, which lets anyone check whether an email is registered. Decide whether that's acceptable for this product.
- 7-day tokens with no revocation. Consider a shorter access token plus a refresh token, or at least a server-side `token_version` on the user.

### 2.5 Error messages leak internal details
**Where:** `routes/analyze.py:65`, `orchestrator.py` (`str(e)` in errors and events), `gemini_llm_adapter.py`
**Fix:** Log the full exception server-side with `logging` (not `print`). Return a generic message and an error code to the client, and add a request id so the user can report it.

### 2.6 Deployment config problems
- **Python version mismatch:** `pyproject.toml` says `>=3.10`, but the code uses `enum.StrEnum`, which is 3.11+. Set `requires-python = ">=3.11"` and black `target-version = ["py311"]`.
- **Two dependency lists that disagree:** `pyproject.toml` lacks `python-docx`, `python-jose` and `bcrypt`. `requirements.txt` ships dev tools (`black`, `pytest`, `httpx`) to production and leaves everything unpinned (`>=`). Make `pyproject.toml` the source of truth, generate a pinned `requirements.txt` with `uv pip compile` or `pip-tools`, and move dev tools to `requirements-dev.txt`.
- **`render.yaml` location:** Render Blueprints are read from the repo root, and this one is in `backend/` while also declaring `rootDir: backend`. Move it to the repo root. Also add `JWT_SECRET_KEY` and a `healthCheckPath: /health`.
- **Dockerfile:**
  - It installs `build-essential` without needing it (PyMuPDF ships wheels).
  - It runs as root.
  - It has no `HEALTHCHECK`.
  - It can't see `knowledge_anchor.md` (see 1.3).
  Use a slim multi-stage build with a non-root user, and add a `.dockerignore` (`venv/`, `uploads/`, `outputs/`, `.env`).
- **CORS:** `allow_credentials=True` isn't needed with bearer tokens. Set it to `False` unless you move to cookies. Restrict `allow_methods` and `allow_headers` to what's actually used.
- **`next.config.ts`:** the `env: { NEXT_PUBLIC_API_URL }` block is redundant (Next inlines `NEXT_PUBLIC_*` automatically), and it hides a missing production value by falling back to localhost. Remove it and fail the build when the variable is missing in production.
- **Model name is hardcoded** (`gemini-2.5-flash`). Move it to `Settings.gemini_model`.
- `GeminiLLMAdapter()` is created lazily through `lru_cache`, so a missing `GEMINI_API_KEY` only surfaces on the first request. Validate it at startup so the service fails fast.

### 2.7 Repo hygiene
- `.DS_Store` is committed at the root. Remove it with `git rm --cached` and add it to the root `.gitignore`.
- The root `.gitignore` pattern `.env*` also ignores `.env.example`. Add `!.env.example` in both the root and `frontend/.gitignore`.
- There's no `frontend/.env.example` documenting `NEXT_PUBLIC_API_URL`. Add one.
- `.vscode/settings.json` is `{}`. Delete it or put real settings in it.

---

## P3: Code quality, architecture, tests, docs

### 3.1 No tests at all
**Fix:** Add `backend/tests/` with pytest and pytest-asyncio:
- **Validator:** one valid and one invalid diagram per type. This catches 1.1.
- **Parser and scaffolder `_parse_response`:** fenced output, text before the JSON, invalid JSON, `None` input.
- **`ZipBuilder`:** path traversal attempts are rejected, and names are unique per document.
- **`AuthUseCase`:** register, login, wrong password, expired or forged token.
- **API:** use `httpx.AsyncClient` with a `FakeLLM` that implements `LLMPort` and returns canned JSON. Cover upload → analyze → diagrams → scaffold, the 401s without a token, and the 404 for another user's document.

On the frontend, add Vitest and Testing Library for `InputPanel` and `MermaidPanel`, plus one Playwright smoke test (login → upload → generate with a mocked API).
Then add a GitHub Actions workflow that runs `black --check`, `ruff`, `pytest`, `npm run lint`, `tsc --noEmit` and `next build`.

### 3.2 Hexagonal architecture violations (the project says it follows the Dependency Rule)
- `agents/diagrammer_agent.py` imports `infrastructure.adapters.mermaid_validator`, so an inner layer depends on an outer one. Add a `MermaidValidatorPort` in `domain/ports` and inject the validator.
- `agents/base_agent.py` and `application/auth_usecase.py` import `app.config`. Pass the settings or values in through constructors.
- The use cases import the concrete `ZipBuilder` and the global `event_bus` singleton. Add `ArchivePort` and `EventPublisherPort` and inject them.
- `DiagramPort` and `ScaffoldPort` are defined but never implemented or used. Either make the agents implement them or delete them.
- `routes/analyze.py` reaches into `routes/upload.py` for the document store, and the diagrams and scaffold routes reach into `analyze.py`. Move the stores behind repositories in `dependencies.py` (see 2.1).
- `routes/upload.py` creates its own `FileParserAdapter()` instead of using `get_file_parser()`.

### 3.3 Duplicated mapping code
**Where:** `routes/analyze.py` builds `AnalysisResponse` by hand twice, and `diagrams.py` and `scaffold.py` each build their responses twice.
**Fix:** Add `to_analysis_response(schema)`, `to_diagram_set_response(ds)` and `to_scaffold_response(sc, include_files)` helpers, or use `model_validate(entity, from_attributes=True)`, since the API schemas mirror the entities field for field.

### 3.4 Dead code and leftovers
- `analyze.py`: unused imports (`asyncio`, `BackgroundTasks`, `GeneratedFileSchema`), and imports placed at the bottom of the module.
- `LLMPort.generate_stream` is implemented but never used.
- `DiagramType.STATE`, `FLOWCHART` and `ARCHITECTURE` have prompts but are never generated, even though the knowledge anchor emphasises `architecture-beta`. Either add an architecture diagram to `generate_all` or drop the unused types.
- `Orchestrator.run_*_only` methods are unused.
- `print` is used throughout. Switch to the `logging` module with a JSON formatter in production.
- `GET /api/diagrams/{id}` and `GET /api/scaffold/{id}` call the LLM as a side effect of a GET and have no error handling, so a Gemini failure becomes a bare 500. Make generation an explicit `POST` and keep the GETs read-only.

### 3.5 Frontend structure
- `API_URL` is duplicated in 6 files. Create `src/lib/api.ts` with `API_URL`, an `apiFetch(path, init)` helper that adds the auth header, parses errors and logs out on 401, and typed request functions.
- Create `src/types/api.ts` mirroring the backend schemas (`PipelineResponse`, `AnalysisResponse`, `DiagramSchema`, …) and remove the `any` types.
- `page.tsx` duplicates the same hover colour logic through `onMouseEnter`/`onMouseLeave` style mutation. Replace it with Tailwind `hover:` classes.

### 3.6 Docs are out of date
- `README.md` says the frontend is **React + Vite** when it's Next.js 16. Its setup steps also skip `.env.example` → `.env` for both apps and don't mention `NEXT_PUBLIC_API_URL`, `JWT_SECRET_KEY` or the Python version.
- `frontend/README.md` is still the create-next-app boilerplate. Replace it or delete it.
- `task_plan.md` has every task unchecked, even though most are implemented. Update it, or replace it with this plan.
- The project is named in three ways: "Smart Documentation Architect" in the docs, ZIP README and pyproject, "Structify" in the UI and API title, and `smart-doc-backend` on Render. Pick one name.
- `system_architecture.md` describes parallel agents, a Validator agent and Modal serverless workers, none of which exist. Mark them as future work, or implement the parallel part (see 1.5).

---

## Suggested order of work

| Phase | Items | Outcome |
|---|---|---|
| **1. Lock it down** (½–1 day) | 0.2, 0.3, 0.5, 2.6 (Python version, `JWT_SECRET_KEY` in render.yaml) | No forgeable tokens, XSS or path traversal |
| **2. Auth everywhere** (1 day) | 0.1, 1.4 (per-document SSE), 3.5 (`apiFetch`) | Users only see their own data, and quota is protected |
| **3. Make it work** (1–2 days) | 0.4, 1.1, 1.2, 1.3, 1.6 | Text input works, diagrams validate correctly, scaffolds stop truncating |
| **4. Survive production** (2–3 days) | 1.5 (background jobs), 2.1 (database), 2.2, 2.3, 2.5 | Long runs don't time out, and data survives restarts |
| **5. Polish** (1–2 days) | 1.7, 1.8, 1.9, 2.4, 2.7 | Clean UI behaviour, ESLint clean |
| **6. Sustain** (ongoing) | 3.1 (tests + CI), 3.2–3.4, 3.6 | Regressions caught automatically |

## How to verify when done
- `cd backend && pytest` passes, including the validator, ZIP traversal and auth tests.
- `cd frontend && npm run lint && npx tsc --noEmit && npm run build` passes with 0 errors (today: 6 lint errors).
- Manual checks:
  - Calling `/api/upload` or `/api/analyze/full` without a token returns 401.
  - User B gets a 404 for user A's `document_id`.
  - A typed-only SRS generates results.
  - An ER diagram shows `is_valid: true`.
  - A pipeline that takes more than 2 minutes still completes in the UI.
  - Restarting the backend doesn't log users out.

---

## Status (updated after the fixes)

Everything above was implemented except the items below. Verified: backend `pytest` (81 tests), `ruff`, `black --check`; frontend `eslint` (0 problems, was 6 errors + 1 warning), `tsc --noEmit`, `vitest` (18 tests), `next build`; plus a manual end-to-end run in the browser (signup → typed requirements → live logs → diagrams → ZIP) against the real backend with a fake LLM.

**Deliberately different from the plan**
- 1.2: used Gemini JSON mode (`response_mime_type`) plus tolerant parsing instead of `response_schema`, and generated the scaffold one file per call. `response_schema` could not be tested without calling Gemini.
- 0.3: no extra DOMPurify pass. Mermaid's `strict` mode already sanitises, and the fallback now uses `textContent`.
- 2.4: the `409 "email already exists"` on signup is kept (it makes sign-up usable); token revocation is done via `token_version` + `POST /api/auth/logout-all` rather than refresh tokens.
- 2.6: the Render service name `smart-doc-backend` is kept, because renaming it would create a new service with a new URL.
- 1.5: background jobs run in-process (`asyncio` tasks), not in an external queue.
- Diagrams: an architecture diagram was added to the generated set (4 instead of 3).

**Not done**
- 1.1 (best option): real Mermaid validation through `mermaid-cli` or a Node sidecar. The heuristic validator was fixed and tested instead.
- 3.1: Playwright smoke test (needs browser downloads); CI runs lint, types, unit tests and build.
- 2.1: Postgres support is configured (`DATABASE_URL`, `psycopg`) but untested; only SQLite was exercised. The event bus and rate limiter are still per-process (run one worker, or move them to Redis).
- 0.3 (long term): moving the token to an httpOnly cookie.
