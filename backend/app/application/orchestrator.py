"""
Orchestrator — The "Lead" Agent that coordinates the entire pipeline.

Runs the Parser, then the Diagrammer and Scaffolder concurrently (both only
need the extracted schema), and reports progress through the event publisher.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from app.application.generate_diagrams_usecase import GenerateDiagramsUseCase
from app.application.parse_srs_usecase import ParseSRSUseCase
from app.application.scaffold_project_usecase import ScaffoldProjectUseCase
from app.domain.entities.diagram import DiagramSet
from app.domain.entities.events import AgentEvent, EventType
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.project_scaffold import ProjectScaffold
from app.domain.entities.srs_document import SRSDocument
from app.domain.errors import DomainError
from app.domain.ports.event_publisher_port import EventPublisherPort
from app.domain.ports.result_repository_port import ResultRepositoryPort

logger = logging.getLogger(__name__)
T = TypeVar("T")


@dataclass
class PipelineResult:
    """Result of the full orchestration pipeline."""

    document: SRSDocument
    schema: ExtractedSchema | None = None
    diagrams: DiagramSet | None = None
    scaffold: ProjectScaffold | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0 and self.schema is not None


class Orchestrator:
    """The Lead Agent — coordinates Parser, Diagrammer, and Scaffolder agents."""

    def __init__(
        self,
        parse_usecase: ParseSRSUseCase,
        diagrams_usecase: GenerateDiagramsUseCase,
        scaffold_usecase: ScaffoldProjectUseCase,
        events: EventPublisherPort,
        results: ResultRepositoryPort,
    ) -> None:
        self._parse = parse_usecase
        self._diagrams = diagrams_usecase
        self._scaffold = scaffold_usecase
        self._events = events
        self._results = results

    async def _emit(
        self,
        event_type: EventType,
        document_id: str,
        message: str,
        agent: str = "Lead",
        **data,
    ) -> None:
        await self._events.publish(
            AgentEvent(
                event_type=event_type,
                agent_name=agent,
                document_id=document_id,
                message=message,
                data=data,
            )
        )

    async def _stage(
        self,
        agent: str,
        document_id: str,
        errors: list[str],
        call: Callable[[], Awaitable[T]],
    ) -> T | None:
        """Run one stage; turn any failure into a user-safe error message."""
        try:
            return await call()
        except DomainError as exc:
            message = f"{agent} failed: {exc.user_message}"
            logger.warning("%s failed for document %s: %s", agent, document_id, exc)
        except Exception:  # noqa: BLE001 - never leak internals to the client
            message = f"{agent} failed unexpectedly."
            logger.exception("%s crashed for document %s", agent, document_id)
        errors.append(message)
        await self._emit(EventType.AGENT_ERROR, document_id, message, agent=agent)
        return None

    async def run_full_pipeline(
        self,
        document: SRSDocument,
        file_path: Path | None,
        instructions: str = "",
    ) -> PipelineResult:
        """
        Execute the complete SRS → Architecture pipeline.

        The caller (the job service) is expected to have published
        ``PIPELINE_START``; this method publishes the terminal event.
        """
        result = PipelineResult(document=document)
        doc_id = document.id
        await self._emit(
            EventType.AGENT_PROGRESS,
            doc_id,
            f"Starting full pipeline for '{document.filename}'...",
        )

        # ── Stage 1: Parse SRS ──────────────────────────────────────────
        result.schema = await self._stage(
            "ParserAgent",
            doc_id,
            result.errors,
            lambda: self._parse.execute(document, file_path, instructions),
        )
        if result.schema is not None and not result.schema.entities:
            result.errors.append(
                "No entities could be extracted. The document may not describe a system "
                "to model; try adding more detail."
            )
            result.schema = None

        if result.schema is not None:
            # Stored as soon as it exists so the UI can show it while later stages run.
            await self._results.save_schema(result.schema)

        if result.schema is None:
            await self._emit(
                EventType.PIPELINE_ERROR,
                doc_id,
                "Pipeline stopped: the requirements could not be analyzed.",
                errors=result.errors,
            )
            return result

        # ── Stages 2 & 3: Diagrams and Scaffold run concurrently ────────
        schema = result.schema

        async def diagram_stage() -> DiagramSet | None:
            out = await self._stage(
                "DiagrammerAgent",
                doc_id,
                result.errors,
                lambda: self._diagrams.execute(schema),
            )
            if out is not None:
                await self._results.save_diagrams(out)
            return out

        async def scaffold_stage() -> ProjectScaffold | None:
            out = await self._stage(
                "ScaffolderAgent",
                doc_id,
                result.errors,
                lambda: self._scaffold.execute(schema),
            )
            if out is not None:
                await self._results.save_scaffold(out)
            return out

        diagrams, scaffold = await asyncio.gather(diagram_stage(), scaffold_stage())
        result.diagrams, result.scaffold = diagrams, scaffold
        if diagrams is not None:
            result.errors.extend(diagrams.errors)

        # ── Pipeline Complete ───────────────────────────────────────────
        status = "completed successfully" if result.success else "completed with errors"
        await self._emit(
            EventType.PIPELINE_COMPLETE,
            doc_id,
            f"Pipeline {status}.",
            errors=result.errors,
        )
        return result
