"""
API Schemas — Pydantic v2 request/response models for the REST API.

These are separate from domain entities to maintain the Hexagonal Architecture
boundary. API schemas handle HTTP serialization; domain entities handle business logic.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ─── Auth Schemas ────────────────────────────────────────────────────────────


class SignupRequest(BaseModel):
    """Request body for user registration."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(
        ..., min_length=8, description="Password (8+ chars, max 72 bytes)"
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name must not be blank.")
        return v

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes long.")
        return v


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()


class UserResponse(BaseModel):
    """Public user profile returned in auth responses."""

    id: str
    name: str
    email: str


class AuthResponse(BaseModel):
    """Response returned after successful signup or login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─── Upload Schemas ──────────────────────────────────────────────────────────


class UploadResponse(BaseModel):
    """Response after a successful SRS upload or text submission."""

    document_id: str
    filename: str
    file_type: str
    char_count: int = 0
    message: str = "File uploaded successfully."


class TextDocumentRequest(BaseModel):
    """Create a document from typed requirements instead of a file."""

    content: str = Field(..., min_length=1, max_length=500_000)
    filename: str = Field(default="requirements.txt", max_length=200)


# ─── Analysis Schemas ────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Request to analyze an existing document."""

    document_id: str
    instructions: str = Field(
        default="",
        max_length=5000,
        description="Optional extra guidance for the analysis.",
    )


class _FromEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AttributeSchema(_FromEntity):
    """API representation of an entity attribute."""

    name: str
    data_type: str = "string"
    is_required: bool = True
    description: str = ""


class EntitySchema(_FromEntity):
    """API representation of an extracted entity."""

    name: str
    description: str = ""
    attributes: list[AttributeSchema] = Field(default_factory=list)


class RelationshipSchema(_FromEntity):
    """API representation of a relationship between entities."""

    source: str
    target: str
    relationship_type: str = "one-to-many"
    label: str = ""


class ActionSchema(_FromEntity):
    """API representation of an extracted action/endpoint."""

    name: str
    description: str = ""
    actor: str = ""
    target_entity: str = ""
    http_method: str = "GET"
    endpoint: str = ""


class AnalysisResponse(BaseModel):
    """Response containing the full extracted schema from SRS analysis."""

    document_id: str
    project_name: str
    description: str = ""
    entities: list[EntitySchema] = Field(default_factory=list)
    relationships: list[RelationshipSchema] = Field(default_factory=list)
    actions: list[ActionSchema] = Field(default_factory=list)
    entity_count: int = 0
    relationship_count: int = 0
    action_count: int = 0


# ─── Diagram Schemas ────────────────────────────────────────────────────────


class DiagramSchema(BaseModel):
    """API representation of a single Mermaid diagram."""

    id: str
    diagram_type: str
    title: str = ""
    mermaid_code: str = ""
    is_valid: bool = False
    validation_errors: list[str] = Field(default_factory=list)


class DiagramSetResponse(BaseModel):
    """Response containing all generated diagrams for a document."""

    document_id: str
    diagrams: list[DiagramSchema] = Field(default_factory=list)
    all_valid: bool = False
    errors: list[str] = Field(default_factory=list)


# ─── Scaffold Schemas ───────────────────────────────────────────────────────


class GeneratedFileSchema(_FromEntity):
    """API representation of a generated file."""

    path: str
    content: str = ""
    language: str = "python"


class ScaffoldResponse(BaseModel):
    """Response containing the project scaffold metadata."""

    document_id: str
    project_name: str
    directory_tree: str = ""
    file_count: int = 0
    files: list[GeneratedFileSchema] = Field(default_factory=list)
    download_url: str = ""


# ─── Job / Pipeline Schemas ─────────────────────────────────────────────────


class JobResponse(BaseModel):
    """State (and, once finished, results) of a background pipeline run."""

    job_id: str
    document_id: str
    status: str
    success: bool = False
    errors: list[str] = Field(default_factory=list)
    analysis: AnalysisResponse | None = None
    diagrams: DiagramSetResponse | None = None
    scaffold: ScaffoldResponse | None = None


# ─── Health/Error Schemas ───────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: str = "INTERNAL_ERROR"
    request_id: str = ""
