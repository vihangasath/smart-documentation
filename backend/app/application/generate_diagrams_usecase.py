"""
Generate Diagrams Use Case — orchestrates Mermaid diagram generation.

Covers Task Plan Phase 2: Tasks 2.1, 2.2, 2.3.
"""

from __future__ import annotations

from app.agents.diagrammer_agent import DiagrammerAgent
from app.domain.entities.diagram import DiagramSet
from app.domain.entities.events import AgentEvent, EventType
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.ports.event_publisher_port import EventPublisherPort


class GenerateDiagramsUseCase:
    """Generate and validate ER, class, sequence and architecture diagrams."""

    def __init__(
        self, diagrammer_agent: DiagrammerAgent, events: EventPublisherPort
    ) -> None:
        self._diagrammer_agent = diagrammer_agent
        self._events = events

    async def execute(self, schema: ExtractedSchema) -> DiagramSet:
        await self._events.publish(
            AgentEvent(
                event_type=EventType.AGENT_START,
                agent_name="DiagrammerAgent",
                document_id=schema.document_id,
                message="Starting Mermaid diagram generation...",
            )
        )

        diagram_set = await self._diagrammer_agent.generate_all(schema)

        valid_count = sum(1 for d in diagram_set.diagrams if d.is_valid)
        total_count = len(diagram_set.diagrams)
        await self._events.publish(
            AgentEvent(
                event_type=EventType.AGENT_COMPLETE,
                agent_name="DiagrammerAgent",
                document_id=schema.document_id,
                message=(
                    f"Diagram generation complete. "
                    f"{valid_count}/{total_count} diagrams passed validation."
                ),
                data={
                    "valid_count": valid_count,
                    "total_count": total_count,
                    "diagram_types": [
                        d.diagram_type.value for d in diagram_set.diagrams
                    ],
                },
            )
        )
        return diagram_set
