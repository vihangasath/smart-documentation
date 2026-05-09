"""
Generate Diagrams Use Case — orchestrates Mermaid diagram generation.

Covers Task Plan Phase 2: Tasks 2.1, 2.2, 2.3.
"""

from __future__ import annotations

from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.diagram import DiagramSet
from app.agents.diagrammer_agent import DiagrammerAgent
from app.application.event_bus import event_bus, AgentEvent, EventType


class GenerateDiagramsUseCase:
    """
    Use case for generating Mermaid.js diagrams from an extracted schema.

    Workflow:
    1. Receive the extracted schema from the Parser Agent.
    2. Generate ER, Class, and Sequence diagrams.
    3. Validate each diagram's Mermaid syntax.
    4. Return the validated diagram set.
    """

    def __init__(self, diagrammer_agent: DiagrammerAgent) -> None:
        self._diagrammer_agent = diagrammer_agent

    async def execute(self, schema: ExtractedSchema) -> DiagramSet:
        """
        Generate all diagram types for the given schema.

        Args:
            schema: Extracted schema from the Parser Agent.

        Returns:
            DiagramSet with validated Mermaid diagrams.
        """
        await event_bus.publish(
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

        await event_bus.publish(
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
                    "diagram_types": [d.diagram_type.value for d in diagram_set.diagrams],
                },
            )
        )

        return diagram_set
