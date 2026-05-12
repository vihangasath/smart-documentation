"""
Configuration module for Smart Documentation Architect.

Uses pydantic-settings for strict, type-safe environment variable loading.
"""

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# In serverless environments (e.g., Render, Railway, AWS Lambda), the project
# directory is read-only.  Use /tmp for ephemeral storage in production.
_is_serverless = os.getenv("APP_ENV", "development") == "production"
UPLOADS_DIR = Path("/tmp/uploads") if _is_serverless else BASE_DIR / "uploads"
OUTPUTS_DIR = Path("/tmp/outputs") if _is_serverless else BASE_DIR / "outputs"
KNOWLEDGE_ANCHOR_PATH = BASE_DIR.parent / "knowledge_anchor.md"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Gemini ────────────────────────────────────────────────────────────
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key for LLM operations.",
    )

    # ── Application ──────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    app_debug: bool = Field(default=True)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    # ── Upload ───────────────────────────────────────────────────────────
    max_upload_size_mb: int = Field(default=10)

    # ── CORS ─────────────────────────────────────────────────────────────
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
    )

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
