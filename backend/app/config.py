"""
Configuration module for Structify.

Uses pydantic-settings for strict, type-safe environment variable loading.
"""

from __future__ import annotations

import logging
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_ANCHOR_PATH = (
    Path(__file__).resolve().parent / "prompts" / "knowledge_anchor.md"
)

MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Gemini ────────────────────────────────────────────────────────────
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key for LLM operations.",
    )
    gemini_model: str = Field(default="gemini-2.5-flash")
    gemini_thinking_budget: int | None = Field(
        default=1024,
        description="Thinking-token budget for thinking models (None = model default).",
    )
    llm_max_retries: int = Field(default=4, ge=1)
    llm_retry_base_seconds: float = Field(default=2.0, ge=0)
    llm_retry_max_seconds: float = Field(default=60.0, ge=0)
    llm_concurrency: int = Field(default=3, ge=1)

    # ── Application ──────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    # ── Storage ──────────────────────────────────────────────────────────
    database_url: str = Field(
        default="",
        description="SQLAlchemy URL. Use Postgres in production; SQLite loses "
        "data when the container filesystem is ephemeral.",
    )
    uploads_dir: Path | None = None
    outputs_dir: Path | None = None
    file_retention_hours: int = Field(default=24, ge=1)
    data_retention_days: int = Field(default=30, ge=1)
    cleanup_interval_minutes: int = Field(default=60, ge=1)

    # ── Upload / SRS limits ──────────────────────────────────────────────
    max_upload_size_mb: int = Field(default=10)
    min_srs_chars: int = Field(default=50, ge=1)
    max_srs_chars: int = Field(default=200_000, ge=1000)

    # ── CORS ─────────────────────────────────────────────────────────────
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
    )

    # ── Auth / JWT ───────────────────────────────────────────────────────
    jwt_secret_key: str = Field(
        default="",
        description="Secret used to sign JWTs. Required (>=32 chars) in production.",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_days: int = Field(default=7)
    admin_email: str = ""
    admin_password: str = ""

    # ── Abuse controls ───────────────────────────────────────────────────
    auth_rate_limit_per_minute: int = Field(default=10, ge=1)
    pipeline_runs_per_hour: int = Field(default=10, ge=1)
    max_active_jobs_per_user: int = Field(default=2, ge=1)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @model_validator(mode="after")
    def _resolve_defaults(self) -> Settings:
        # Secrets ---------------------------------------------------------
        if len(self.jwt_secret_key) < MIN_JWT_SECRET_LENGTH:
            if self.is_production:
                raise ValueError(
                    f"JWT_SECRET_KEY must be set to at least {MIN_JWT_SECRET_LENGTH} "
                    "characters when APP_ENV=production."
                )
            self.jwt_secret_key = secrets.token_urlsafe(48)
            logger.warning(
                "JWT_SECRET_KEY is not set; using a random per-process secret. "
                "Tokens stop working on restart. Set JWT_SECRET_KEY in .env."
            )

        # Directories -----------------------------------------------------
        # Production containers have a read-only app dir; use /tmp there.
        root = Path("/tmp") if self.is_production else BASE_DIR
        if self.uploads_dir is None:
            self.uploads_dir = root / "uploads"
        if self.outputs_dir is None:
            self.outputs_dir = root / "outputs"

        # Database --------------------------------------------------------
        url = self.database_url.strip()
        if not url:
            if self.is_production:
                url = "sqlite:////tmp/structify.db"
                logger.warning(
                    "DATABASE_URL is not set; using ephemeral SQLite in /tmp. "
                    "Accounts and results are lost on restart. Set DATABASE_URL "
                    "to a Postgres database."
                )
            else:
                url = f"sqlite:///{BASE_DIR / 'data' / 'structify.db'}"
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        self.database_url = url
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
