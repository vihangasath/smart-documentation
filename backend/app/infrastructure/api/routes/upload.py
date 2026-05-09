"""
Upload Route — POST /api/upload

Handles SRS file uploads (PDF, Markdown, Text).
Saves the file to disk and returns a document ID for subsequent operations.
"""

from __future__ import annotations

from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, status

from app.config import get_settings, UPLOADS_DIR
from app.domain.entities.srs_document import SRSDocument
from app.infrastructure.adapters.file_parser_adapter import FileParserAdapter
from app.infrastructure.api.schemas.api_schemas import UploadResponse, ErrorResponse

router = APIRouter(prefix="/api", tags=["Upload"])

# In-memory document store (for MVP; replace with a database later)
_documents: dict[str, tuple[SRSDocument, Path]] = {}

file_parser = FileParserAdapter()


def get_document_store() -> dict[str, tuple[SRSDocument, Path]]:
    """Access the in-memory document store."""
    return _documents


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
    summary="Upload an SRS document",
    description="Upload a PDF, Markdown, or Text file for analysis.",
)
async def upload_srs(
    file: UploadFile = File(
        ...,
        description="SRS document (PDF, Markdown, or Text)",
    ),
) -> UploadResponse:
    """
    Upload an SRS document for processing.

    Accepts PDF (.pdf), Markdown (.md), and Text (.txt) files.
    Returns a document_id to use in subsequent API calls.
    """
    settings = get_settings()

    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    # Validate file type
    try:
        file_type = file_parser.detect_file_type(file.filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Read and validate file size
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb}MB limit.",
        )

    # Create the document entity
    document = SRSDocument(
        filename=file.filename,
        file_type=file_type,
    )

    # Save file to disk
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOADS_DIR / f"{document.id}_{file.filename}"

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Store document reference
    _documents[document.id] = (document, file_path)

    return UploadResponse(
        document_id=document.id,
        filename=file.filename,
        file_type=file_type.value,
        message=f"File '{file.filename}' uploaded successfully.",
    )
