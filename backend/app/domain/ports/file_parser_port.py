"""
File Parser Port — abstract interface for parsing uploaded SRS files.

Outer-layer adapters implement this to provide PDF, Markdown, and Text parsing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.domain.entities.srs_document import SRSDocument, FileType


class FileParserPort(ABC):
    """
    Port for file parsing operations.

    The domain layer depends on this abstraction; the infrastructure layer
    provides a concrete adapter.
    """

    @abstractmethod
    async def parse(self, file_path: Path, file_type: FileType) -> str:
        """
        Extract raw text content from a file.

        Args:
            file_path: Path to the uploaded file on disk.
            file_type: Detected format of the file.

        Returns:
            Extracted text content as a string.
        """
        ...

    @abstractmethod
    def detect_file_type(self, filename: str) -> FileType:
        """
        Detect the file type from its filename/extension.

        Args:
            filename: Original filename.

        Returns:
            Detected FileType enum value.

        Raises:
            ValueError: If the file type is unsupported.
        """
        ...
