"""
Composition root — wires domain ports to concrete adapters.

``build_container`` is the only place where concrete classes are chosen.
FastAPI dependencies below read the container from ``app.state`` so tests can
build an app with fakes (for example a fake LLM) without touching globals.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.agents.diagrammer_agent import DiagrammerAgent
from app.agents.parser_agent import ParserAgent
from app.agents.scaffolder_agent import ScaffolderAgent
from app.application.auth_usecase import AuthUseCase
from app.application.event_bus import EventBus
from app.application.generate_diagrams_usecase import GenerateDiagramsUseCase
from app.application.job_service import JobService
from app.application.orchestrator import Orchestrator
from app.application.parse_srs_usecase import ParseSRSUseCase
from app.application.scaffold_project_usecase import ScaffoldProjectUseCase
from app.config import KNOWLEDGE_ANCHOR_PATH, Settings
from app.domain.entities.srs_document import SRSDocument
from app.domain.entities.user import User
from app.domain.errors import AuthError
from app.domain.ports.llm_port import LLMPort
from app.infrastructure.adapters.file_parser_adapter import FileParserAdapter
from app.infrastructure.adapters.gemini_llm_adapter import GeminiLLMAdapter
from app.infrastructure.adapters.mermaid_validator import MermaidValidator
from app.infrastructure.adapters.unavailable_llm import UnavailableLLM
from app.infrastructure.adapters.zip_builder import ZipBuilder
from app.infrastructure.api.rate_limit import SlidingWindowLimiter
from app.infrastructure.knowledge import load_knowledge_anchor
from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.sql_repositories import (
    SqlDocumentRepository,
    SqlJobRepository,
    SqlResultRepository,
    SqlUserStore,
)

logger = logging.getLogger(__name__)


@dataclass
class Container:
    settings: Settings
    db: Database
    llm: LLMPort
    events: EventBus
    file_parser: FileParserAdapter
    users: SqlUserStore
    documents: SqlDocumentRepository
    results: SqlResultRepository
    jobs: SqlJobRepository
    auth: AuthUseCase
    parse_usecase: ParseSRSUseCase
    diagrams_usecase: GenerateDiagramsUseCase
    scaffold_usecase: ScaffoldProjectUseCase
    orchestrator: Orchestrator
    job_service: JobService
    auth_limiter: SlidingWindowLimiter
    pipeline_limiter: SlidingWindowLimiter


def _build_llm(settings: Settings) -> LLMPort:
    if not settings.gemini_api_key:
        if settings.is_production:
            raise RuntimeError("GEMINI_API_KEY must be set when APP_ENV=production.")
        logger.warning(
            "GEMINI_API_KEY is not set; analysis requests will fail until it is."
        )
        return UnavailableLLM()
    return GeminiLLMAdapter(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model,
        thinking_budget=settings.gemini_thinking_budget,
        max_retries=settings.llm_max_retries,
        retry_base_seconds=settings.llm_retry_base_seconds,
        retry_max_seconds=settings.llm_retry_max_seconds,
        max_concurrency=settings.llm_concurrency,
    )


def build_container(settings: Settings, llm: LLMPort | None = None) -> Container:
    """Create every adapter, agent and use case. ``llm`` overrides Gemini (tests)."""
    db = Database(settings.database_url)
    db.create_all()

    llm = llm or _build_llm(settings)
    knowledge = load_knowledge_anchor(KNOWLEDGE_ANCHOR_PATH)
    events = EventBus()
    file_parser = FileParserAdapter()

    users = SqlUserStore(db)
    documents = SqlDocumentRepository(db)
    results = SqlResultRepository(db)
    jobs = SqlJobRepository(db)

    auth = AuthUseCase(
        users,
        jwt_secret=settings.jwt_secret_key,
        jwt_algorithm=settings.jwt_algorithm,
        expire_days=settings.jwt_expire_days,
    )

    parse_usecase = ParseSRSUseCase(
        file_parser,
        ParserAgent(llm, knowledge),
        events,
        min_chars=settings.min_srs_chars,
        max_chars=settings.max_srs_chars,
    )
    diagrams_usecase = GenerateDiagramsUseCase(
        DiagrammerAgent(llm, MermaidValidator(), knowledge), events
    )
    scaffold_usecase = ScaffoldProjectUseCase(
        ScaffolderAgent(llm, knowledge), ZipBuilder(), settings.outputs_dir, events
    )
    orchestrator = Orchestrator(
        parse_usecase, diagrams_usecase, scaffold_usecase, events, results
    )
    job_service = JobService(
        jobs,
        results,
        orchestrator,
        events,
        max_active_per_user=settings.max_active_jobs_per_user,
    )

    return Container(
        settings=settings,
        db=db,
        llm=llm,
        events=events,
        file_parser=file_parser,
        users=users,
        documents=documents,
        results=results,
        jobs=jobs,
        auth=auth,
        parse_usecase=parse_usecase,
        diagrams_usecase=diagrams_usecase,
        scaffold_usecase=scaffold_usecase,
        orchestrator=orchestrator,
        job_service=job_service,
        auth_limiter=SlidingWindowLimiter(settings.auth_rate_limit_per_minute, 60),
        pipeline_limiter=SlidingWindowLimiter(settings.pipeline_runs_per_hour, 3600),
    )


# ─── FastAPI dependencies ───────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    container: Container = Depends(get_container),
) -> User:
    """Require a valid Bearer token; respond 401 otherwise."""
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await container.auth.get_current_user(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            exc.user_message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


class OwnedDocument(NamedTuple):
    document: SRSDocument
    file_path: Path | None


async def get_owned_document(
    document_id: str,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
) -> OwnedDocument:
    """Load a document, answering 404 unless it belongs to the caller."""
    found = await container.documents.get(document_id)
    if not found or found[0].owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found.")
    return OwnedDocument(*found)


def _too_many(retry_after: float) -> HTTPException:
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Too many requests. Please slow down and try again shortly.",
        headers={"Retry-After": str(int(retry_after) + 1)},
    )


async def rate_limit_auth(
    request: Request, container: Container = Depends(get_container)
) -> None:
    """Throttle login/signup per client IP."""
    ip = request.client.host if request.client else "unknown"
    retry = container.auth_limiter.hit(ip)
    if retry is not None:
        raise _too_many(retry)


async def rate_limit_pipeline(
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
) -> None:
    """Throttle LLM-backed operations per user."""
    retry = container.pipeline_limiter.hit(user.id)
    if retry is not None:
        raise _too_many(retry)
