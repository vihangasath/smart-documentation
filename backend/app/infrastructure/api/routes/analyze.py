"""
Analyze Route — POST /api/analyze

Triggers SRS analysis and the full orchestration pipeline.
Returns the extracted schema, diagrams, and scaffold metadata.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, status, BackgroundTasks

from app.infrastructure.api.schemas.api_schemas import (
    AnalyzeRequest,
    AnalysisResponse,
    PipelineResponse,
    DiagramSetResponse,
    DiagramSchema,
    ScaffoldResponse,
    GeneratedFileSchema,
    ErrorResponse,
)
from app.infrastructure.api.routes.upload import get_document_store
from app.infrastructure.api.dependencies import (
    get_orchestrator,
    get_parse_usecase,
)

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        422: {"model": ErrorResponse, "description": "Analysis failed"},
    },
    summary="Analyze an uploaded SRS document",
    description="Run the Parser Agent to extract entities, relationships, and actions.",
)
async def analyze_document(request: AnalyzeRequest) -> AnalysisResponse:
    """
    Analyze an uploaded SRS document with the Parser Agent.

    Extracts domain entities, relationships, and functional actions.
    """
    store = get_document_store()

    if request.document_id not in store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{request.document_id}' not found. Upload it first.",
        )

    document, file_path = store[request.document_id]

    parse_usecase = get_parse_usecase()

    try:
        schema = await parse_usecase.execute(document, file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Analysis failed: {str(e)}",
        )

    # Store the schema for downstream use
    _schemas[request.document_id] = schema

    return AnalysisResponse(
        document_id=schema.document_id,
        project_name=schema.project_name,
        description=schema.description,
        entities=[
            {
                "name": e.name,
                "description": e.description,
                "attributes": [
                    {
                        "name": a.name,
                        "data_type": a.data_type,
                        "is_required": a.is_required,
                        "description": a.description,
                    }
                    for a in e.attributes
                ],
            }
            for e in schema.entities
        ],
        relationships=[
            {
                "source": r.source,
                "target": r.target,
                "relationship_type": r.relationship_type,
                "label": r.label,
            }
            for r in schema.relationships
        ],
        actions=[
            {
                "name": a.name,
                "description": a.description,
                "actor": a.actor,
                "target_entity": a.target_entity,
                "http_method": a.http_method,
                "endpoint": a.endpoint,
            }
            for a in schema.actions
        ],
        entity_count=len(schema.entities),
        relationship_count=len(schema.relationships),
        action_count=len(schema.actions),
    )


@router.post(
    "/analyze/full",
    response_model=PipelineResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
    summary="Run the full analysis pipeline",
    description="Run Parser → Diagrammer → Scaffolder agents sequentially.",
)
async def analyze_full_pipeline(request: AnalyzeRequest) -> PipelineResponse:
    """
    Run the complete orchestration pipeline on an uploaded document.

    Stages: Parse → Generate Diagrams → Scaffold Project.
    """
    store = get_document_store()

    if request.document_id not in store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{request.document_id}' not found.",
        )

    document, file_path = store[request.document_id]
    orchestrator = get_orchestrator()

    result = await orchestrator.run_full_pipeline(document, file_path)

    # Build response
    response = PipelineResponse(
        document_id=document.id,
        success=result.success,
        errors=result.errors,
    )

    # Attach analysis if available
    if result.schema:
        _schemas[request.document_id] = result.schema
        response.analysis = AnalysisResponse(
            document_id=result.schema.document_id,
            project_name=result.schema.project_name,
            description=result.schema.description,
            entities=[
                {
                    "name": e.name,
                    "description": e.description,
                    "attributes": [
                        {
                            "name": a.name,
                            "data_type": a.data_type,
                            "is_required": a.is_required,
                            "description": a.description,
                        }
                        for a in e.attributes
                    ],
                }
                for e in result.schema.entities
            ],
            relationships=[
                {
                    "source": r.source,
                    "target": r.target,
                    "relationship_type": r.relationship_type,
                    "label": r.label,
                }
                for r in result.schema.relationships
            ],
            actions=[
                {
                    "name": a.name,
                    "description": a.description,
                    "actor": a.actor,
                    "target_entity": a.target_entity,
                    "http_method": a.http_method,
                    "endpoint": a.endpoint,
                }
                for a in result.schema.actions
            ],
            entity_count=len(result.schema.entities),
            relationship_count=len(result.schema.relationships),
            action_count=len(result.schema.actions),
        )

    # Attach diagrams if available
    if result.diagrams:
        _diagram_sets[request.document_id] = result.diagrams
        response.diagrams = DiagramSetResponse(
            document_id=result.diagrams.document_id,
            diagrams=[
                DiagramSchema(
                    id=d.id,
                    diagram_type=d.diagram_type.value,
                    title=d.title,
                    mermaid_code=d.mermaid_code,
                    is_valid=d.is_valid,
                    validation_errors=d.validation_errors,
                )
                for d in result.diagrams.diagrams
            ],
            all_valid=result.diagrams.all_valid,
        )

    # Attach scaffold if available
    if result.scaffold:
        _scaffolds[request.document_id] = result.scaffold
        response.scaffold = ScaffoldResponse(
            document_id=result.scaffold.document_id,
            project_name=result.scaffold.project_name,
            directory_tree=result.scaffold.directory_tree,
            file_count=len(result.scaffold.files),
            download_url=f"/api/scaffold/{document.id}/download",
        )

    return response


# ─── In-memory stores for intermediate results ──────────────────────────────

from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.diagram import DiagramSet
from app.domain.entities.project_scaffold import ProjectScaffold

_schemas: dict[str, ExtractedSchema] = {}
_diagram_sets: dict[str, DiagramSet] = {}
_scaffolds: dict[str, ProjectScaffold] = {}


def get_schema_store() -> dict[str, ExtractedSchema]:
    return _schemas


def get_diagram_store() -> dict[str, DiagramSet]:
    return _diagram_sets


def get_scaffold_store() -> dict[str, ProjectScaffold]:
    return _scaffolds
