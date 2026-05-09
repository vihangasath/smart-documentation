"""
Diagram Port — abstract interface for Mermaid diagram generation and validation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.diagram import Diagram, DiagramType


class DiagramPort(ABC):
    """Port for diagram generation and validation."""

    @abstractmethod
    async def generate_diagram(
        self,
        schema: ExtractedSchema,
        diagram_type: DiagramType,
    ) -> Diagram:
        """
        Generate a Mermaid.js diagram from an extracted schema.

        Args:
            schema: The structured schema from the Parser Agent.
            diagram_type: Which type of diagram to generate.

        Returns:
            A Diagram entity with Mermaid code.
        """
        ...

    @abstractmethod
    async def validate_mermaid(self, mermaid_code: str) -> tuple[bool, list[str]]:
        """
        Validate Mermaid.js syntax.

        Args:
            mermaid_code: Raw Mermaid syntax string.

        Returns:
            Tuple of (is_valid, list_of_errors).
        """
        ...
