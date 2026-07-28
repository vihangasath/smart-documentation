"""
API Schemas — Pydantic v2 request/response models for the REST API.

These are separate from domain entities to maintain the Hexagonal Architecture
boundary. API schemas handle HTTP serialization; domain entities handle business logic.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ─── Auth Schemas ────────────────────────────────────────────────────────────────


class SignupRequest(BaseModel):
    """Request body for user registration."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Plain-text password (min 8 chars)")

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address.")
        return v.lower().strip()


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
    """Response after a successful SRS file upload."""

    document_id: str
    filename: str
    file_type: str
    message: str = "File uploaded successfully."


# ─── Analysis Schemas ────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Request to analyze an already-uploaded document."""

    document_id: str


class AttributeSchema(BaseModel):
    """API representation of an entity attribute."""

    name: str
    data_type: str = "string"
    is_required: bool = True
    description: str = ""


class EntitySchema(BaseModel):
    """API representation of an extracted entity."""

    name: str
    description: str = ""
    attributes: list[AttributeSchema] = Field(default_factory=list)


class RelationshipSchema(BaseModel):
    """API representation of a relationship between entities."""

    source: str
    target: str
    relationship_type: str = "one-to-many"
    label: str = ""


class ActionSchema(BaseModel):
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


# ─── Scaffold Schemas ───────────────────────────────────────────────────────


class GeneratedFileSchema(BaseModel):
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


# ─── Pipeline Schemas ───────────────────────────────────────────────────────


class PipelineResponse(BaseModel):
    """Response from the full orchestration pipeline."""

    document_id: str
    success: bool
    analysis: AnalysisResponse | None = None
    diagrams: DiagramSetResponse | None = None
    scaffold: ScaffoldResponse | None = None
    errors: list[str] = Field(default_factory=list)


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
