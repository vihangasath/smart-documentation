"""Jobs Route — GET /api/jobs/{job_id}: status and, once finished, results."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.entities.user import User
from app.infrastructure.api.dependencies import (
    Container,
    get_container,
    get_current_user,
)
from app.infrastructure.api.schemas.api_schemas import ErrorResponse, JobResponse
from app.infrastructure.api.schemas.mappers import to_job_response

router = APIRouter(prefix="/api", tags=["Jobs"])


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get a pipeline job",
)
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
) -> JobResponse:
    job = await container.jobs.get(job_id)
    if not job or job.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found.")
    return to_job_response(
        job,
        schema=await container.results.get_schema(job.document_id),
        diagrams=await container.results.get_diagrams(job.document_id),
        scaffold=await container.results.get_scaffold(job.document_id),
    )
