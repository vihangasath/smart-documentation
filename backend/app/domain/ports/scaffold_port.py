"""
Scaffold Port — abstract interface for project scaffolding and ZIP generation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.project_scaffold import ProjectScaffold


class ScaffoldPort(ABC):
    """Port for project scaffolding operations."""

    @abstractmethod
    async def generate_scaffold(
        self,
        schema: ExtractedSchema,
    ) -> ProjectScaffold:
        """
        Generate a complete project scaffold from the extracted schema.

        Args:
            schema: Structured schema from the Parser Agent.

        Returns:
            A ProjectScaffold entity with all generated files.
        """
        ...

    @abstractmethod
    async def build_zip(
        self,
        scaffold: ProjectScaffold,
        output_dir: Path,
    ) -> Path:
        """
        Package the scaffold into a downloadable ZIP file.

        Args:
            scaffold: The project scaffold to package.
            output_dir: Directory to write the ZIP file to.

        Returns:
            Path to the generated ZIP file.
        """
        ...
