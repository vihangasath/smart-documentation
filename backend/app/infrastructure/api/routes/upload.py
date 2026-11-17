"""
Upload Routes — POST /api/upload and POST /api/documents/text

Both create an SRSDocument owned by the caller and return its id. File uploads
are streamed to disk with a hard size cap; text is extracted immediately so
unreadable files fail fast.
"""

from __future__ import annotations

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.domain.entities.srs_document import FileType, SRSDocument
from app.domain.entities.user import User
from app.domain.errors import DocumentError
from app.domain.paths import safe_filename
from app.infrastructure.api.dependencies import (
    Container,
    get_container,
    get_current_user,
)
from app.infrastructure.api.schemas.api_schemas import (
    ErrorResponse,
    TextDocumentRequest,
    UploadResponse,
)

router = APIRouter(prefix="/api", tags=["Upload"])

_CHUNK = 1024 * 1024


def _check_min_length(content: str, min_chars: int) -> None:
    if len(content.strip()) < min_chars:
        raise DocumentError(
            "No extractable text was found (a scanned PDF has no text layer). "
            "Upload a text-based file or type the requirements instead."
        )


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type"},
        413: {"model": ErrorResponse, "description": "File too large"},
        422: {"model": ErrorResponse, "description": "File has no readable text"},
    },
    summary="Upload an SRS document",
    description="Upload a PDF, DOCX, Markdown, or Text file for analysis.",
)
async def upload_srs(
    request: Request,
    file: UploadFile = File(
        ..., description="SRS document (PDF, DOCX, Markdown, or Text)"
    ),
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
) -> UploadResponse:
    settings = container.settings
    too_large = HTTPException(
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        f"File exceeds {settings.max_upload_size_mb}MB limit.",
    )

    declared = request.headers.get("content-length")
    if (
        declared
        and declared.isdigit()
        and int(declared) > settings.max_upload_bytes + _CHUNK
    ):
        raise too_large
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Filename is required.")

    try:
        file_type = container.file_parser.detect_file_type(file.filename)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    document = SRSDocument(
        owner_id=user.id, filename=safe_filename(file.filename), file_type=file_type
    )
    uploads_dir = settings.uploads_dir
    uploads_dir.mkdir(parents=True, exist_ok=True)
    # Never use the client's filename on disk; only its extension.
    suffix = (
        "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    )
    file_path = uploads_dir / f"{document.id}{suffix}"

    written = 0
    try:
        async with aiofiles.open(file_path, "wb") as out:
            while chunk := await file.read(_CHUNK):
                written += len(chunk)
                if written > settings.max_upload_bytes:
                    raise too_large
                await out.write(chunk)

        document.content = await container.file_parser.parse(file_path, file_type)
        _check_min_length(document.content, settings.min_srs_chars)
    except (HTTPException, DocumentError):
        file_path.unlink(missing_ok=True)
        raise

    await container.documents.save(document, file_path)
    return UploadResponse(
        document_id=document.id,
        filename=document.filename,
        file_type=file_type.value,
        char_count=len(document.content),
        message=f"File '{document.filename}' uploaded successfully.",
    )


@router.post(
    "/documents/text",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ErrorResponse, "description": "Text too short"}},
    summary="Create a document from typed requirements",
)
async def create_text_document(
    body: TextDocumentRequest,
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
) -> UploadResponse:
    settings = container.settings
    _check_min_length(body.content, settings.min_srs_chars)

    document = SRSDocument(
        owner_id=user.id,
        filename=safe_filename(body.filename, default="requirements.txt"),
        file_type=FileType.TEXT,
        content=body.content.strip(),
    )
    await container.documents.save(document, None)
    return UploadResponse(
        document_id=document.id,
        filename=document.filename,
        file_type=document.file_type.value,
        char_count=len(document.content),
        message="Requirements saved.",
    )
