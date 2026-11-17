"""
Diagrams Routes — GET/POST /api/diagrams/{document_id}

GET only reads stored diagrams. POST (re)generates them from the stored analysis.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.infrastructure.api.dependencies import (
    Container,
    OwnedDocument,
    get_container,
    get_owned_document,
    rate_limit_pipeline,
)
from app.infrastructure.api.schemas.api_schemas import DiagramSetResponse, ErrorResponse
from app.infrastructure.api.schemas.mappers import to_diagram_set_response

router = APIRouter(prefix="/api", tags=["Diagrams"])


@router.get(
    "/diagrams/{document_id}",
    response_model=DiagramSetResponse,
    responses={404: {"model": ErrorResponse, "description": "Diagrams not found"}},
    summary="Get stored diagrams for a document",
)
async def get_diagrams(
    owned: OwnedDocument = Depends(get_owned_document),
    container: Container = Depends(get_container),
) -> DiagramSetResponse:
    diagrams = await container.results.get_diagrams(owned.document.id)
    if diagrams is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No diagrams yet. Run the analysis or POST to this endpoint to generate them.",
        )
    return to_diagram_set_response(diagrams)


@router.post(
    "/diagrams/{document_id}",
    response_model=DiagramSetResponse,
    responses={
        409: {"model": ErrorResponse, "description": "No analysis to draw from"}
    },
    dependencies=[Depends(rate_limit_pipeline)],
    summary="Generate diagrams from the stored analysis",
)
async def generate_diagrams(
    owned: OwnedDocument = Depends(get_owned_document),
    container: Container = Depends(get_container),
) -> DiagramSetResponse:
    schema = await container.results.get_schema(owned.document.id)
    if schema is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Analyze the document first (POST /api/analyze)."
        )
    diagrams = await container.diagrams_usecase.execute(schema)
    await container.results.save_diagrams(diagrams)
    return to_diagram_set_response(diagrams)
