"""
Parse SRS Use Case — orchestrates the file upload and entity extraction pipeline.

Covers Task Plan Phase 1: Tasks 1.1, 1.2, 1.3.
"""

from __future__ import annotations

from pathlib import Path

from app.domain.entities.srs_document import SRSDocument, FileType
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.ports.file_parser_port import FileParserPort
from app.agents.parser_agent import ParserAgent
from app.application.event_bus import event_bus, AgentEvent, EventType


class ParseSRSUseCase:
    """
    Use case for uploading and analyzing an SRS document.

    Workflow:
    1. Save the uploaded file to disk.
    2. Detect file type and extract text content.
    3. Run the Parser Agent to extract structured entities.
    4. Return the extracted schema.
    """

    def __init__(
        self,
        file_parser: FileParserPort,
        parser_agent: ParserAgent,
    ) -> None:
        self._file_parser = file_parser
        self._parser_agent = parser_agent

    async def execute(
        self,
        document: SRSDocument,
        file_path: Path,
    ) -> ExtractedSchema:
        """
        Execute the SRS parsing pipeline.

        Args:
            document: The SRS document entity (with metadata).
            file_path: Path to the saved file on disk.

        Returns:
            Extracted schema with entities, relationships, and actions.
        """
        # Emit start event
        await event_bus.publish(
            AgentEvent(
                event_type=EventType.AGENT_START,
                agent_name="ParserAgent",
                document_id=document.id,
                message=f"Starting analysis of '{document.filename}'...",
            )
        )

        # Step 1: Extract text content
        await event_bus.publish(
            AgentEvent(
                event_type=EventType.AGENT_PROGRESS,
                agent_name="ParserAgent",
                document_id=document.id,
                message="Extracting text content from file...",
            )
        )

        content = await self._file_parser.parse(file_path, document.file_type)
        document.content = content

        # Step 2: Run the Parser Agent
        await event_bus.publish(
            AgentEvent(
                event_type=EventType.AGENT_PROGRESS,
                agent_name="ParserAgent",
                document_id=document.id,
                message="Analyzing entities, relationships, and actions with Gemini...",
            )
        )

        schema = await self._parser_agent.analyze(
            document_id=document.id,
            srs_content=content,
        )

        # Emit completion
        entity_count = len(schema.entities)
        action_count = len(schema.actions)
        await event_bus.publish(
            AgentEvent(
                event_type=EventType.AGENT_COMPLETE,
                agent_name="ParserAgent",
                document_id=document.id,
                message=(
                    f"Analysis complete. Found {entity_count} entities, "
                    f"{len(schema.relationships)} relationships, "
                    f"and {action_count} actions."
                ),
                data={
                    "entity_count": entity_count,
                    "relationship_count": len(schema.relationships),
                    "action_count": action_count,
                },
            )
        )

        return schema
