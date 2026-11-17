"""
Job Service — runs the full pipeline in the background.

``submit`` returns immediately with a job; the pipeline continues on the event
loop and persists its results, so slow runs are not tied to one HTTP request
(which hosting proxies would cut off).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.application.orchestrator import Orchestrator
from app.domain.entities.events import AgentEvent, EventType
from app.domain.entities.job import Job, JobStatus
from app.domain.entities.srs_document import SRSDocument
from app.domain.errors import DomainError
from app.domain.ports.event_publisher_port import EventPublisherPort
from app.domain.ports.job_repository_port import JobRepositoryPort
from app.domain.ports.result_repository_port import ResultRepositoryPort

logger = logging.getLogger(__name__)


class JobService:
    def __init__(
        self,
        jobs: JobRepositoryPort,
        results: ResultRepositoryPort,
        orchestrator: Orchestrator,
        events: EventPublisherPort,
        max_active_per_user: int = 2,
    ) -> None:
        self._jobs = jobs
        self._results = results
        self._orchestrator = orchestrator
        self._events = events
        self._max_active = max_active_per_user
        self._tasks: set[asyncio.Task] = set()

    async def submit(
        self,
        document: SRSDocument,
        file_path: Path | None,
        instructions: str = "",
    ) -> Job:
        """Create a job and start it in the background."""
        if (
            await self._jobs.count_active_for_owner(document.owner_id)
            >= self._max_active
        ):
            raise DomainError(
                "You already have analyses running. Wait for them to finish and try again.",
                code="TOO_MANY_JOBS",
            )

        job = Job(
            document_id=document.id,
            owner_id=document.owner_id,
            instructions=instructions,
        )
        await self._jobs.save(job)
        # A new run starts from nothing, so a poller never sees the previous run's output.
        await self._results.clear(document.id)
        # Resets the document's event replay buffer so streams never mix runs.
        await self._events.publish(
            AgentEvent(
                event_type=EventType.PIPELINE_START,
                agent_name="Lead",
                document_id=document.id,
                message=f"Queued analysis of '{document.filename}'.",
            )
        )

        task = asyncio.create_task(self._run(job, document, file_path))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return job

    async def _run(
        self, job: Job, document: SRSDocument, file_path: Path | None
    ) -> None:
        job.status = JobStatus.RUNNING
        await self._jobs.save(job)
        try:
            result = await self._orchestrator.run_full_pipeline(
                document, file_path, job.instructions
            )
            if result.schema:
                await self._results.save_schema(result.schema)
            if result.diagrams:
                await self._results.save_diagrams(result.diagrams)
            if result.scaffold:
                await self._results.save_scaffold(result.scaffold)
            job.errors = result.errors
            job.status = JobStatus.COMPLETED if result.schema else JobStatus.FAILED
        except asyncio.CancelledError:
            job.status = JobStatus.FAILED
            job.errors = ["The server is shutting down; please run the analysis again."]
            raise
        except Exception:  # noqa: BLE001
            logger.exception("Job %s crashed", job.id)
            job.status = JobStatus.FAILED
            job.errors = [f"The analysis failed unexpectedly. Reference: {job.id}"]
            await self._events.publish(
                AgentEvent(
                    event_type=EventType.PIPELINE_ERROR,
                    agent_name="Lead",
                    document_id=document.id,
                    message=job.errors[0],
                )
            )
        finally:
            job.finished_at = datetime.now(UTC)
            await asyncio.shield(self._jobs.save(job))

    async def shutdown(self) -> None:
        """Cancel running jobs (called on application shutdown)."""
        for task in list(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
