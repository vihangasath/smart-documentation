"""Job Repository Port — persistence for background pipeline runs."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.job import Job


class JobRepositoryPort(ABC):
    """Stores background job state."""

    @abstractmethod
    async def save(self, job: Job) -> None:
        """Insert or update a job."""
        ...

    @abstractmethod
    async def get(self, job_id: str) -> Job | None:
        """Return a job by ID, or None."""
        ...

    @abstractmethod
    async def count_active_for_owner(self, owner_id: str) -> int:
        """Number of queued/running jobs belonging to the user."""
        ...

    @abstractmethod
    async def fail_stale_jobs(self) -> int:
        """Mark jobs left queued/running by a previous process as failed."""
        ...
