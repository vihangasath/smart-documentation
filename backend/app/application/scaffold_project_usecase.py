"""
Scaffold Project Use Case — orchestrates boilerplate generation and ZIP packaging.

Covers Task Plan Phase 3: Tasks 3.1, 3.2, 3.3.
"""

from __future__ import annotations

from pathlib import Path

from app.agents.scaffolder_agent import ScaffolderAgent
from app.domain.entities.events import AgentEvent, EventType
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.project_scaffold import ProjectScaffold
from app.domain.ports.archive_port import ArchivePort
from app.domain.ports.event_publisher_port import EventPublisherPort

AGENT = "ScaffolderAgent"


class ScaffoldProjectUseCase:
    """Generate boilerplate files, then package them as a ZIP."""

    def __init__(
        self,
        scaffolder_agent: ScaffolderAgent,
        archive: ArchivePort,
        output_dir: Path,
        events: EventPublisherPort,
    ) -> None:
        self._scaffolder_agent = scaffolder_agent
        self._archive = archive
        self._output_dir = output_dir
        self._events = events

    async def _emit(
        self, event_type: EventType, document_id: str, message: str, **data
    ) -> None:
        await self._events.publish(
            AgentEvent(
                event_type=event_type,
                agent_name=AGENT,
                document_id=document_id,
                message=message,
                data=data,
            )
        )

    async def execute(self, schema: ExtractedSchema) -> ProjectScaffold:
        doc_id = schema.document_id
        await self._emit(
            EventType.AGENT_START, doc_id, "Generating project boilerplate code..."
        )

        scaffold = await self._scaffolder_agent.scaffold(schema)

        await self._emit(
            EventType.AGENT_PROGRESS,
            doc_id,
            f"Generated {len(scaffold.files)} files. Packaging ZIP...",
        )
        zip_path = await self._archive.build(scaffold, self._output_dir)
        scaffold.zip_path = str(zip_path)

        await self._emit(
            EventType.AGENT_COMPLETE,
            doc_id,
            f"Scaffold complete: {len(scaffold.files)} files packaged.",
            file_count=len(scaffold.files),
            project_name=scaffold.project_name,
        )
        return scaffold
