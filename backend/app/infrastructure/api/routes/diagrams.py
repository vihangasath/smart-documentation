"""
Diagrams Route — GET /api/diagrams/{document_id}

Returns the generated Mermaid diagrams for a document.
Also supports generating diagrams on-demand if only analysis has been run.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.infrastructure.api.schemas.api_schemas import (
    DiagramSetResponse,
    DiagramSchema,
    ErrorResponse,
)
from app.infrastructure.api.routes.analyze import (
    get_schema_store,
    get_diagram_store,
)
from app.infrastructure.api.dependencies import get_diagrams_usecase

router = APIRouter(prefix="/api", tags=["Diagrams"])


@router.get(
    "/diagrams/{document_id}",
    response_model=DiagramSetResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Diagrams not found"},
    },
    summary="Get diagrams for a document",
    description="Retrieve generated Mermaid.js diagrams. Generates them on-demand if analysis exists.",
)
async def get_diagrams(document_id: str) -> DiagramSetResponse:
    """
    Get or generate Mermaid diagrams for a document.

    If diagrams have already been generated (via /api/analyze/full),
    returns cached results. Otherwise, generates them on-demand
    from the analysis schema.
    """
    diagram_store = get_diagram_store()
    schema_store = get_schema_store()

    # Return cached diagrams if available
    if document_id in diagram_store:
        ds = diagram_store[document_id]
        return DiagramSetResponse(
            document_id=ds.document_id,
            diagrams=[
                DiagramSchema(
                    id=d.id,
                    diagram_type=d.diagram_type.value,
                    title=d.title,
                    mermaid_code=d.mermaid_code,
                    is_valid=d.is_valid,
                    validation_errors=d.validation_errors,
                )
                for d in ds.diagrams
            ],
            all_valid=ds.all_valid,
        )

    # Generate on-demand if schema exists
    if document_id in schema_store:
        schema = schema_store[document_id]
        diagrams_usecase = get_diagrams_usecase()
        ds = await diagrams_usecase.execute(schema)
        diagram_store[document_id] = ds

        return DiagramSetResponse(
            document_id=ds.document_id,
            diagrams=[
                DiagramSchema(
                    id=d.id,
                    diagram_type=d.diagram_type.value,
                    title=d.title,
                    mermaid_code=d.mermaid_code,
                    is_valid=d.is_valid,
                    validation_errors=d.validation_errors,
                )
                for d in ds.diagrams
            ],
            all_valid=ds.all_valid,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"No diagrams or analysis found for document '{document_id}'. "
            "Run /api/analyze first."
        ),
    )
