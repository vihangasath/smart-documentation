"""
Analyze Routes — POST /api/analyze and POST /api/analyze/full

``/analyze`` runs only the Parser Agent and answers inline. ``/analyze/full``
starts the whole pipeline as a background job and returns ``202`` with a job id;
poll ``GET /api/jobs/{job_id}`` and follow progress on ``/api/events/{id}``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.domain.entities.user import User
from app.infrastructure.api.dependencies import (
    Container,
    OwnedDocument,
    get_container,
    get_current_user,
    get_owned_document,
    rate_limit_pipeline,
)
from app.infrastructure.api.schemas.api_schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    ErrorResponse,
    JobResponse,
)
from app.infrastructure.api.schemas.mappers import to_analysis_response, to_job_response

router = APIRouter(prefix="/api", tags=["Analysis"])


async def _owned(
    request: AnalyzeRequest,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
) -> OwnedDocument:
    # Body-based variant of get_owned_document (the id is not in the path).
    return await get_owned_document(request.document_id, user, container)


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    dependencies=[Depends(rate_limit_pipeline)],
    summary="Analyze a document (parser only)",
)
async def analyze_document(
    request: AnalyzeRequest,
    owned: OwnedDocument = Depends(_owned),
    container: Container = Depends(get_container),
) -> AnalysisResponse:
    """Run the Parser Agent to extract entities, relationships, and actions."""
    document, file_path = owned
    schema = await container.parse_usecase.execute(
        document, file_path, request.instructions
    )
    await container.documents.save(document, file_path)  # keeps extracted text
    await container.results.save_schema(schema)
    return to_analysis_response(schema)


@router.post(
    "/analyze/full",
    response_model=JobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
    dependencies=[Depends(rate_limit_pipeline)],
    summary="Start the full analysis pipeline",
    description="Parser → Diagrammer + Scaffolder, run as a background job.",
)
async def analyze_full_pipeline(
    request: AnalyzeRequest,
    owned: OwnedDocument = Depends(_owned),
    container: Container = Depends(get_container),
) -> JobResponse:
    document, file_path = owned
    job = await container.job_service.submit(document, file_path, request.instructions)
    return to_job_response(job)
