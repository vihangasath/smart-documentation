"""Document Repository Port — persistence for uploaded SRS documents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.domain.entities.srs_document import SRSDocument


class DocumentRepositoryPort(ABC):
    """Stores SRS documents together with the location of the original file."""

    @abstractmethod
    async def save(self, document: SRSDocument, file_path: Path | None) -> None:
        """Insert or update a document. ``file_path`` is None for typed text."""
        ...

    @abstractmethod
    async def get(self, document_id: str) -> tuple[SRSDocument, Path | None] | None:
        """Return the document and its file path, or None."""
        ...

    @abstractmethod
    async def delete_older_than(self, cutoff_iso: str) -> int:
        """Delete documents (and dependent results/jobs) older than the cutoff."""
        ...
