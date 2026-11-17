"""
Scaffold Routes — GET/POST /api/scaffold/{document_id} and the ZIP download.

GET only reads stored results. POST (re)generates the scaffold from the stored
analysis.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.domain.paths import slugify
from app.infrastructure.api.dependencies import (
    Container,
    OwnedDocument,
    get_container,
    get_owned_document,
    rate_limit_pipeline,
)
from app.infrastructure.api.schemas.api_schemas import ErrorResponse, ScaffoldResponse
from app.infrastructure.api.schemas.mappers import to_scaffold_response

router = APIRouter(prefix="/api", tags=["Scaffold"])


@router.get(
    "/scaffold/{document_id}",
    response_model=ScaffoldResponse,
    responses={404: {"model": ErrorResponse, "description": "Scaffold not found"}},
    summary="Get stored scaffold details and file listing",
)
async def get_scaffold(
    owned: OwnedDocument = Depends(get_owned_document),
    container: Container = Depends(get_container),
) -> ScaffoldResponse:
    scaffold = await container.results.get_scaffold(owned.document.id)
    if scaffold is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No scaffold yet. Run the analysis or POST to this endpoint to generate one.",
        )
    return to_scaffold_response(scaffold)


@router.post(
    "/scaffold/{document_id}",
    response_model=ScaffoldResponse,
    responses={
        409: {"model": ErrorResponse, "description": "No analysis to build from"}
    },
    dependencies=[Depends(rate_limit_pipeline)],
    summary="Generate the scaffold from the stored analysis",
)
async def generate_scaffold(
    owned: OwnedDocument = Depends(get_owned_document),
    container: Container = Depends(get_container),
) -> ScaffoldResponse:
    schema = await container.results.get_schema(owned.document.id)
    if schema is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Analyze the document first (POST /api/analyze)."
        )
    scaffold = await container.scaffold_usecase.execute(schema)
    await container.results.save_scaffold(scaffold)
    return to_scaffold_response(scaffold)


@router.get(
    "/scaffold/{document_id}/download",
    response_class=FileResponse,
    responses={404: {"model": ErrorResponse, "description": "ZIP not found"}},
    summary="Download scaffold as ZIP",
)
async def download_scaffold(
    owned: OwnedDocument = Depends(get_owned_document),
    container: Container = Depends(get_container),
) -> FileResponse:
    scaffold = await container.results.get_scaffold(owned.document.id)
    if scaffold is None or not scaffold.zip_path:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "No scaffold ZIP for this document."
        )

    zip_path = Path(scaffold.zip_path).resolve()
    outputs_dir = container.settings.outputs_dir.resolve()
    if outputs_dir not in zip_path.parents or not zip_path.is_file():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "The ZIP is no longer available. Regenerate the scaffold.",
        )

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"{slugify(scaffold.project_name, default='project')}.zip",
    )
