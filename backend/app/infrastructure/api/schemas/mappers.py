"""Entity → API schema mappers (shared by every route)."""

from __future__ import annotations

from app.domain.entities.diagram import DiagramSet
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.job import Job, JobStatus
from app.domain.entities.project_scaffold import ProjectScaffold
from app.infrastructure.api.schemas.api_schemas import (
    ActionSchema,
    AnalysisResponse,
    DiagramSchema,
    DiagramSetResponse,
    EntitySchema,
    GeneratedFileSchema,
    JobResponse,
    RelationshipSchema,
    ScaffoldResponse,
)


def to_analysis_response(schema: ExtractedSchema) -> AnalysisResponse:
    return AnalysisResponse(
        document_id=schema.document_id,
        project_name=schema.project_name,
        description=schema.description,
        entities=[EntitySchema.model_validate(e) for e in schema.entities],
        relationships=[
            RelationshipSchema.model_validate(r) for r in schema.relationships
        ],
        actions=[ActionSchema.model_validate(a) for a in schema.actions],
        entity_count=len(schema.entities),
        relationship_count=len(schema.relationships),
        action_count=len(schema.actions),
    )


def to_diagram_set_response(diagrams: DiagramSet) -> DiagramSetResponse:
    return DiagramSetResponse(
        document_id=diagrams.document_id,
        diagrams=[
            DiagramSchema(
                id=d.id,
                diagram_type=d.diagram_type.value,
                title=d.title,
                mermaid_code=d.mermaid_code,
                is_valid=d.is_valid,
                validation_errors=d.validation_errors,
            )
            for d in diagrams.diagrams
        ],
        all_valid=diagrams.all_valid,
        errors=diagrams.errors,
    )


def to_scaffold_response(
    scaffold: ProjectScaffold, include_files: bool = True
) -> ScaffoldResponse:
    return ScaffoldResponse(
        document_id=scaffold.document_id,
        project_name=scaffold.project_name,
        directory_tree=scaffold.directory_tree,
        file_count=len(scaffold.files),
        files=(
            [GeneratedFileSchema.model_validate(f) for f in scaffold.files]
            if include_files
            else []
        ),
        download_url=f"/api/scaffold/{scaffold.document_id}/download",
    )


def to_job_response(
    job: Job,
    schema: ExtractedSchema | None = None,
    diagrams: DiagramSet | None = None,
    scaffold: ProjectScaffold | None = None,
) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        document_id=job.document_id,
        status=job.status.value,
        success=job.status == JobStatus.COMPLETED and not job.errors,
        errors=job.errors,
        analysis=to_analysis_response(schema) if schema else None,
        diagrams=to_diagram_set_response(diagrams) if diagrams else None,
        scaffold=(
            to_scaffold_response(scaffold, include_files=False) if scaffold else None
        ),
    )
