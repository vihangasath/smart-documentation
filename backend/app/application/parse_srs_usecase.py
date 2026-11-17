"""
Parse SRS Use Case — turns an uploaded/typed document into an ExtractedSchema.

Covers Task Plan Phase 1: Tasks 1.1, 1.2, 1.3.
"""

from __future__ import annotations

from pathlib import Path

from app.agents.parser_agent import ParserAgent
from app.domain.entities.events import AgentEvent, EventType
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.srs_document import SRSDocument
from app.domain.errors import DocumentError
from app.domain.ports.event_publisher_port import EventPublisherPort
from app.domain.ports.file_parser_port import FileParserPort

AGENT = "ParserAgent"


class ParseSRSUseCase:
    """
    Workflow:
    1. Use the document's text, or extract it from the saved file.
    2. Reject empty/unreadable documents; truncate oversized ones.
    3. Run the Parser Agent to extract structured entities.
    """

    def __init__(
        self,
        file_parser: FileParserPort,
        parser_agent: ParserAgent,
        events: EventPublisherPort,
        min_chars: int = 50,
        max_chars: int = 200_000,
    ) -> None:
        self._file_parser = file_parser
        self._parser_agent = parser_agent
        self._events = events
        self._min_chars = min_chars
        self._max_chars = max_chars

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

    async def execute(
        self,
        document: SRSDocument,
        file_path: Path | None,
        instructions: str = "",
    ) -> ExtractedSchema:
        """Execute the SRS parsing pipeline."""
        await self._emit(
            EventType.AGENT_START,
            document.id,
            f"Starting analysis of '{document.filename}'...",
        )

        if not document.content:
            if file_path is None:
                raise DocumentError("This document has no content to analyze.")
            await self._emit(
                EventType.AGENT_PROGRESS,
                document.id,
                "Extracting text content from file...",
            )
            document.content = await self._file_parser.parse(
                file_path, document.file_type
            )

        content = document.content.strip()
        if len(content) < self._min_chars:
            raise DocumentError(
                "No extractable text was found in the document (it may be a scanned image). "
                "Upload a text-based file or type the requirements instead."
            )
        if len(content) > self._max_chars:
            content = content[: self._max_chars]
            await self._emit(
                EventType.AGENT_PROGRESS,
                document.id,
                f"Document is very long; only the first {self._max_chars:,} characters "
                "will be analyzed.",
            )

        await self._emit(
            EventType.AGENT_PROGRESS,
            document.id,
            "Analyzing entities, relationships, and actions with Gemini...",
        )
        schema = await self._parser_agent.analyze(
            document_id=document.id, srs_content=content, instructions=instructions
        )

        await self._emit(
            EventType.AGENT_COMPLETE,
            document.id,
            f"Analysis complete. Found {len(schema.entities)} entities, "
            f"{len(schema.relationships)} relationships, and {len(schema.actions)} actions.",
            entity_count=len(schema.entities),
            relationship_count=len(schema.relationships),
            action_count=len(schema.actions),
        )
        return schema
