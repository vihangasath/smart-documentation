"""
Scaffold Route — GET /api/scaffold/{document_id}/download

Serves the generated project scaffold as a downloadable ZIP file.
Also supports generating scaffold on-demand.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.infrastructure.api.schemas.api_schemas import (
    ScaffoldResponse,
    GeneratedFileSchema,
    ErrorResponse,
)
from app.infrastructure.api.routes.analyze import (
    get_schema_store,
    get_scaffold_store,
)
from app.infrastructure.api.dependencies import get_scaffold_usecase

router = APIRouter(prefix="/api", tags=["Scaffold"])


@router.get(
    "/scaffold/{document_id}",
    response_model=ScaffoldResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Scaffold not found"},
    },
    summary="Get scaffold metadata",
    description="Get the project scaffold details and file listing.",
)
async def get_scaffold(document_id: str) -> ScaffoldResponse:
    """
    Get scaffold metadata and file listing for a document.

    If scaffold hasn't been generated, generates it on-demand from the schema.
    """
    scaffold_store = get_scaffold_store()
    schema_store = get_schema_store()

    # Return cached scaffold if available
    if document_id in scaffold_store:
        scaffold = scaffold_store[document_id]
        return ScaffoldResponse(
            document_id=scaffold.document_id,
            project_name=scaffold.project_name,
            directory_tree=scaffold.directory_tree,
            file_count=len(scaffold.files),
            files=[
                GeneratedFileSchema(
                    path=f.path,
                    content=f.content,
                    language=f.language,
                )
                for f in scaffold.files
            ],
            download_url=f"/api/scaffold/{document_id}/download",
        )

    # Generate on-demand if schema exists
    if document_id in schema_store:
        schema = schema_store[document_id]
        scaffold_usecase = get_scaffold_usecase()
        scaffold = await scaffold_usecase.execute(schema)
        scaffold_store[document_id] = scaffold

        return ScaffoldResponse(
            document_id=scaffold.document_id,
            project_name=scaffold.project_name,
            directory_tree=scaffold.directory_tree,
            file_count=len(scaffold.files),
            files=[
                GeneratedFileSchema(
                    path=f.path,
                    content=f.content,
                    language=f.language,
                )
                for f in scaffold.files
            ],
            download_url=f"/api/scaffold/{document_id}/download",
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"No scaffold or analysis found for document '{document_id}'. "
            "Run /api/analyze first."
        ),
    )


@router.get(
    "/scaffold/{document_id}/download",
    response_class=FileResponse,
    responses={
        404: {"model": ErrorResponse, "description": "ZIP not found"},
    },
    summary="Download scaffold as ZIP",
    description="Download the generated project scaffold as a ZIP archive.",
)
async def download_scaffold(document_id: str) -> FileResponse:
    """
    Download the generated project scaffold as a ZIP file.

    The ZIP must have been previously generated via /api/analyze/full
    or /api/scaffold/{document_id}.
    """
    scaffold_store = get_scaffold_store()

    if document_id not in scaffold_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scaffold found for document '{document_id}'.",
        )

    scaffold = scaffold_store[document_id]

    if not scaffold.zip_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ZIP file has not been generated yet.",
        )

    zip_path = Path(scaffold.zip_path)
    if not zip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ZIP file not found on disk.",
        )

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=f"{scaffold.project_name}.zip",
    )
