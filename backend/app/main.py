"""
Smart Documentation Architect — FastAPI Application Entrypoint.

This is the primary adapter (entry point) in the Hexagonal Architecture.
It wires together all routes, middleware, and startup logic.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, UPLOADS_DIR, OUTPUTS_DIR
from app.infrastructure.api.routes import upload, analyze, diagrams, scaffold, events, auth
from app.infrastructure.api.schemas.api_schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # ── Startup ─────────────────────────────────────────────────────────
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    print("🚀 Smart Documentation Architect is starting up...")
    print(f"   Uploads dir: {UPLOADS_DIR}")
    print(f"   Outputs dir: {OUTPUTS_DIR}")

    # ── Seed hardcoded admin account ─────────────────────────────────────
    # This admin account is always available regardless of in-memory state.
    # Credentials: admin@smartdoc.ai / Admin@1234
    from app.infrastructure.api.dependencies import get_auth_usecase
    auth_uc = get_auth_usecase()
    try:
        await auth_uc.register(
            name="Admin",
            email="admin@smartdoc.ai",
            password="Admin@1234",
        )
        print("✅ Admin account seeded: admin@smartdoc.ai / Admin@1234")
    except Exception:
        # Already exists (shouldn't happen with in-memory store on fresh start,
        # but guard against any edge case)
        print("ℹ️  Admin account already seeded.")

    yield

    # ── Shutdown ────────────────────────────────────────────────────────
    print("👋 Smart Documentation Architect is shutting down...")


def create_app() -> FastAPI:
    """
    Application factory.

    Creates and configures the FastAPI application with all routes,
    middleware, and OpenAPI documentation.
    """
    settings = get_settings()

    app = FastAPI(
        title="Smart Documentation Architect",
        description=(
            "Transform unstructured SRS documents into structured system "
            "architectures, Mermaid.js diagrams, and deployable boilerplate code. "
            "Powered by a multi-agent AI orchestrator with Google Gemini."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS Middleware ─────────────────────────────────────────────────
    # Always include localhost origins so local dev works without an .env file.
    cors_origins = list(set([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        *settings.cors_origins_list,
    ]))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ──────────────────────────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(upload.router)
    app.include_router(analyze.router)
    app.include_router(diagrams.router)
    app.include_router(scaffold.router)
    app.include_router(events.router)

    # ── Health Check ────────────────────────────────────────────────────
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="Health check",
    )
    async def health_check() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            timestamp=datetime.now(timezone.utc),
        )

    @app.get(
        "/",
        tags=["System"],
        summary="Root",
    )
    async def root():
        return {
            "name": "Smart Documentation Architect",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
