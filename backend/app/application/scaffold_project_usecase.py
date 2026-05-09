"""
Scaffold Project Use Case — orchestrates boilerplate code generation and ZIP packaging.

Covers Task Plan Phase 3: Tasks 3.1, 3.2, 3.3.
"""

from __future__ import annotations

from pathlib import Path

from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.project_scaffold import ProjectScaffold
from app.agents.scaffolder_agent import ScaffolderAgent
from app.infrastructure.adapters.zip_builder import ZipBuilder
from app.application.event_bus import event_bus, AgentEvent, EventType


class ScaffoldProjectUseCase:
    """
    Use case for generating a project scaffold and packaging it as a ZIP.

    Workflow:
    1. Run the Scaffolder Agent to generate boilerplate files.
    2. Package everything into a downloadable ZIP archive.
    3. Return the scaffold with the ZIP path.
    """

    def __init__(
        self,
        scaffolder_agent: ScaffolderAgent,
        zip_builder: ZipBuilder,
        output_dir: Path,
    ) -> None:
        self._scaffolder_agent = scaffolder_agent
        self._zip_builder = zip_builder
        self._output_dir = output_dir

    async def execute(self, schema: ExtractedSchema) -> ProjectScaffold:
        """
        Generate scaffold and package as ZIP.

        Args:
            schema: Extracted schema from the Parser Agent.

        Returns:
            ProjectScaffold with zip_path populated.
        """
        await event_bus.publish(
            AgentEvent(
                event_type=EventType.AGENT_START,
                agent_name="ScaffolderAgent",
                document_id=schema.document_id,
                message="Generating project boilerplate code...",
            )
        )

        scaffold = await self._scaffolder_agent.scaffold(schema)

        await event_bus.publish(
            AgentEvent(
                event_type=EventType.AGENT_PROGRESS,
                agent_name="ScaffolderAgent",
                document_id=schema.document_id,
                message=f"Generated {len(scaffold.files)} files. Packaging ZIP...",
            )
        )

        zip_path = await self._zip_builder.build(scaffold, self._output_dir)
        scaffold.zip_path = str(zip_path)

        await event_bus.publish(
            AgentEvent(
                event_type=EventType.AGENT_COMPLETE,
                agent_name="ScaffolderAgent",
                document_id=schema.document_id,
                message=f"Scaffold complete: {len(scaffold.files)} files packaged.",
                data={
                    "file_count": len(scaffold.files),
                    "project_name": scaffold.project_name,
                },
            )
        )

        return scaffold
