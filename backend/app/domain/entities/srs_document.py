"""
SRS Document entity — represents an uploaded Software Requirements Specification.

This is a pure domain object with no infrastructure dependencies.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FileType(StrEnum):
    """Supported SRS file formats."""

    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    DOCX = "docx"


class SRSDocument(BaseModel):
    """
    Core entity representing an uploaded SRS document.

    Attributes:
        id: Unique identifier for this document.
        owner_id: ID of the user who owns this document.
        filename: Original filename as uploaded by the user.
        file_type: Detected file format.
        content: Raw text content extracted from the file.
        uploaded_at: UTC timestamp of upload.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str = ""
    filename: str
    file_type: FileType
    content: str = ""
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
