"""
Orchestrator — The "Lead" Agent that coordinates the entire pipeline.

Decomposes an SRS upload into sub-tasks, routes them to specialized agents,
and manages the full analysis → diagrams → scaffold workflow.
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field

from app.domain.entities.srs_document import SRSDocument
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.diagram import DiagramSet
from app.domain.entities.project_scaffold import ProjectScaffold
from app.application.parse_srs_usecase import ParseSRSUseCase
from app.application.generate_diagrams_usecase import GenerateDiagramsUseCase
from app.application.scaffold_project_usecase import ScaffoldProjectUseCase
from app.application.event_bus import event_bus, AgentEvent, EventType


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
    """
    The Lead Agent — coordinates Parser, Diagrammer, and Scaffolder agents.

    This is the central brain described in the system architecture:
    'A FastAPI backend acts as the brain. It doesn't just process data;
    it manages the Swarm.'
    """

    def __init__(
        self,
        parse_usecase: ParseSRSUseCase,
        diagrams_usecase: GenerateDiagramsUseCase,
        scaffold_usecase: ScaffoldProjectUseCase,
    ) -> None:
        self._parse = parse_usecase
        self._diagrams = diagrams_usecase
        self._scaffold = scaffold_usecase

    async def run_full_pipeline(
        self,
        document: SRSDocument,
        file_path: Path,
    ) -> PipelineResult:
        """
        Execute the complete SRS → Architecture pipeline.

        Stages:
        1. Parse & extract entities (Parser Agent)
        2. Generate Mermaid diagrams (Diagrammer Agent)
        3. Scaffold project boilerplate (Scaffolder Agent)

        Args:
            document: The uploaded SRS document entity.
            file_path: Path to the file on disk.

        Returns:
            PipelineResult with all outputs and any errors.
        """
        result = PipelineResult(document=document)

        await event_bus.publish(
            AgentEvent(
                event_type=EventType.PIPELINE_START,
                document_id=document.id,
                message=f"Starting full pipeline for '{document.filename}'...",
            )
        )

        # ── Stage 1: Parse SRS ──────────────────────────────────────────
        try:
            result.schema = await self._parse.execute(document, file_path)
        except Exception as e:
            error_msg = f"Parser Agent failed: {str(e)}"
            result.errors.append(error_msg)
            await event_bus.publish(
                AgentEvent(
                    event_type=EventType.AGENT_ERROR,
                    agent_name="ParserAgent",
                    document_id=document.id,
                    message=error_msg,
                )
            )
            return result

        if not result.schema or not result.schema.entities:
            result.errors.append(
                "Warning: Parser extracted 0 entities. "
                "The document may not contain enough structured content, "
                "or the LLM response could not be parsed. Continuing pipeline with available data."
            )
            # Only abort fully if we have no schema at all
            if not result.schema:
                return result


        # ── Stage 2: Generate Diagrams ──────────────────────────────────
        try:
            result.diagrams = await self._diagrams.execute(result.schema)
        except Exception as e:
            error_msg = f"Diagrammer Agent failed: {str(e)}"
            result.errors.append(error_msg)
            await event_bus.publish(
                AgentEvent(
                    event_type=EventType.AGENT_ERROR,
                    agent_name="DiagrammerAgent",
                    document_id=document.id,
                    message=error_msg,
                )
            )
            # Continue — diagrams are not blocking for scaffold

        # ── Stage 3: Scaffold Project ───────────────────────────────────
        try:
            result.scaffold = await self._scaffold.execute(result.schema)
        except Exception as e:
            error_msg = f"Scaffolder Agent failed: {str(e)}"
            result.errors.append(error_msg)
            await event_bus.publish(
                AgentEvent(
                    event_type=EventType.AGENT_ERROR,
                    agent_name="ScaffolderAgent",
                    document_id=document.id,
                    message=error_msg,
                )
            )

        # ── Pipeline Complete ───────────────────────────────────────────
        status = "completed successfully" if result.success else "completed with errors"
        await event_bus.publish(
            AgentEvent(
                event_type=EventType.PIPELINE_COMPLETE,
                document_id=document.id,
                message=f"Pipeline {status}.",
                data={"errors": result.errors},
            )
        )

        return result

    async def run_parse_only(
        self,
        document: SRSDocument,
        file_path: Path,
    ) -> ExtractedSchema:
        """Run only the parsing stage."""
        return await self._parse.execute(document, file_path)

    async def run_diagrams_only(
        self, schema: ExtractedSchema
    ) -> DiagramSet:
        """Run only the diagram generation stage."""
        return await self._diagrams.execute(schema)

    async def run_scaffold_only(
        self, schema: ExtractedSchema
    ) -> ProjectScaffold:
        """Run only the scaffolding stage."""
        return await self._scaffold.execute(schema)
