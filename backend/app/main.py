"""
Structify — FastAPI Application Entrypoint.

This is the primary adapter (entry point) in the Hexagonal Architecture.
It wires together routes, middleware and startup/shutdown logic.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.domain.errors import DomainError
from app.infrastructure.api.dependencies import Container, build_container
from app.infrastructure.api.routes import (
    analyze,
    auth,
    diagrams,
    events,
    jobs,
    scaffold,
    upload,
)
from app.infrastructure.api.schemas.api_schemas import HealthResponse
from app.infrastructure.maintenance import run_cleanup
from app.logging_config import configure_logging, request_id_var

logger = logging.getLogger(__name__)

VERSION = "0.1.0"

_STATUS_BY_CODE = {
    "AUTH_ERROR": 401,
    "LLM_ERROR": 502,
    "DOCUMENT_ERROR": 422,
    "TOO_MANY_JOBS": 429,
}


class RequestIdMiddleware:
    """Pure-ASGI middleware: tags each request with an id (and echoes it back)."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        rid = headers.get(b"x-request-id", b"").decode()[:64] or uuid.uuid4().hex[:12]
        token = request_id_var.set(rid)

        async def send_with_id(message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append(
                    (b"x-request-id", rid.encode())
                )
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            request_id_var.reset(token)


async def _seed_admin(container: Container) -> None:
    """Create a bootstrap user only when ADMIN_EMAIL and ADMIN_PASSWORD are both set."""
    settings = container.settings
    if not (settings.admin_email and settings.admin_password):
        return
    try:
        await container.auth.register(
            "Admin", settings.admin_email.lower(), settings.admin_password
        )
        logger.info("Seeded bootstrap account %s", settings.admin_email)
    except DomainError:
        logger.info("Bootstrap account %s already exists", settings.admin_email)


async def _cleanup_loop(container: Container) -> None:
    s = container.settings
    while True:
        try:
            await run_cleanup(
                s.uploads_dir,
                s.outputs_dir,
                container.documents,
                s.file_retention_hours,
                s.data_retention_days,
            )
        except Exception:  # noqa: BLE001
            logger.exception("Cleanup run failed")
        await asyncio.sleep(s.cleanup_interval_minutes * 60)


def create_app(
    container: Container | None = None, settings: Settings | None = None
) -> FastAPI:
    """
    Application factory.

    ``container`` lets tests inject a fully wired container (for example one
    using a fake LLM). When omitted, it is built from the environment at startup.
    """
    settings = settings or (container.settings if container else get_settings())
    configure_logging(settings.is_production)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        c: Container = app.state.container or build_container(settings)
        app.state.container = c
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        settings.outputs_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Structify starting (env=%s)", settings.app_env)

        stale = await c.jobs.fail_stale_jobs()
        if stale:
            logger.warning("Marked %d interrupted jobs as failed", stale)
        await _seed_admin(c)
        cleanup = asyncio.create_task(_cleanup_loop(c))

        yield

        cleanup.cancel()
        await c.job_service.shutdown()
        c.db.dispose()
        logger.info("Structify shut down")

    app = FastAPI(
        title="Structify",
        description=(
            "Transform unstructured SRS documents into structured system "
            "architectures, Mermaid.js diagrams, and deployable boilerplate code. "
            "Powered by a multi-agent AI orchestrator with Google Gemini."
        ),
        version=VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.state.container = container

    # ── Middleware ──────────────────────────────────────────────────────
    cors_origins = list(settings.cors_origins_list)
    if not settings.is_production:
        cors_origins += ["http://127.0.0.1:3000", "http://127.0.0.1:5173"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(set(cors_origins)),
        allow_credentials=False,  # bearer tokens, not cookies
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Content-Disposition"],
    )
    app.add_middleware(RequestIdMiddleware)

    # ── Error handlers ──────────────────────────────────────────────────
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=_STATUS_BY_CODE.get(exc.code, 400),
            content={
                "detail": exc.user_message,
                "error_code": exc.code,
                "request_id": request_id_var.get(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Something went wrong on our side. Please try again.",
                "error_code": "INTERNAL_ERROR",
                "request_id": request_id_var.get(),
            },
        )

    # ── Routes ──────────────────────────────────────────────────────────
    for module in (auth, upload, analyze, jobs, diagrams, scaffold, events):
        app.include_router(module.router)

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="Health check",
    )
    async def health_check() -> HealthResponse:
        return HealthResponse(
            status="healthy", version=VERSION, timestamp=datetime.now(UTC)
        )

    @app.get("/", tags=["System"], summary="Root")
    async def root():
        return {
            "name": "Structify",
            "version": VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Create the application instance (the container is built on startup)
app = create_app()


if __name__ == "__main__":
    import uvicorn

    s = get_settings()
    uvicorn.run("app.main:app", host=s.app_host, port=s.app_port, reload=s.app_debug)
