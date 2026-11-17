"""Archive Port — abstract interface for packaging a scaffold for download."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.domain.entities.project_scaffold import ProjectScaffold


class ArchivePort(ABC):
    """Port for building a downloadable archive from a scaffold."""

    @abstractmethod
    async def build(self, scaffold: ProjectScaffold, output_dir: Path) -> Path:
        """Write the archive into ``output_dir`` and return its path."""
        ...
