"""Job entity — a background run of the full analysis pipeline."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Tracks the state of one pipeline run for one document."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    owner_id: str
    status: JobStatus = JobStatus.QUEUED
    errors: list[str] = Field(default_factory=list)
    instructions: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.status in (JobStatus.QUEUED, JobStatus.RUNNING)
