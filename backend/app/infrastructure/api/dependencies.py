"""
FastAPI Dependency Injection — wires domain ports to concrete adapters.

This is the single composition root where all dependencies are constructed.
The Dependency Rule is enforced: inner layers never import outer layers.
"""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings, OUTPUTS_DIR
from app.domain.ports.file_parser_port import FileParserPort
from app.domain.ports.llm_port import LLMPort
from app.infrastructure.adapters.file_parser_adapter import FileParserAdapter
from app.infrastructure.adapters.gemini_llm_adapter import GeminiLLMAdapter
from app.infrastructure.adapters.zip_builder import ZipBuilder
from app.agents.parser_agent import ParserAgent
from app.agents.diagrammer_agent import DiagrammerAgent
from app.agents.scaffolder_agent import ScaffolderAgent
from app.application.parse_srs_usecase import ParseSRSUseCase
from app.application.generate_diagrams_usecase import GenerateDiagramsUseCase
from app.application.scaffold_project_usecase import ScaffoldProjectUseCase
from app.application.orchestrator import Orchestrator


# ─── Adapter Singletons ────────────────────────────────────────────────────


@lru_cache
def get_file_parser() -> FileParserPort:
    """Provide the file parser adapter."""
    return FileParserAdapter()


@lru_cache
def get_llm() -> LLMPort:
    """Provide the LLM adapter (Gemini)."""
    return GeminiLLMAdapter()


@lru_cache
def get_zip_builder() -> ZipBuilder:
    """Provide the ZIP builder."""
    return ZipBuilder()


# ─── Agent Singletons ──────────────────────────────────────────────────────


@lru_cache
def get_parser_agent() -> ParserAgent:
    """Provide the Parser Agent."""
    return ParserAgent(llm=get_llm())


@lru_cache
def get_diagrammer_agent() -> DiagrammerAgent:
    """Provide the Diagrammer Agent."""
    return DiagrammerAgent(llm=get_llm())


@lru_cache
def get_scaffolder_agent() -> ScaffolderAgent:
    """Provide the Scaffolder Agent."""
    return ScaffolderAgent(llm=get_llm())


# ─── Use Case Singletons ───────────────────────────────────────────────────


@lru_cache
def get_parse_usecase() -> ParseSRSUseCase:
    """Provide the Parse SRS use case."""
    return ParseSRSUseCase(
        file_parser=get_file_parser(),
        parser_agent=get_parser_agent(),
    )


@lru_cache
def get_diagrams_usecase() -> GenerateDiagramsUseCase:
    """Provide the Generate Diagrams use case."""
    return GenerateDiagramsUseCase(
        diagrammer_agent=get_diagrammer_agent(),
    )


@lru_cache
def get_scaffold_usecase() -> ScaffoldProjectUseCase:
    """Provide the Scaffold Project use case."""
    return ScaffoldProjectUseCase(
        scaffolder_agent=get_scaffolder_agent(),
        zip_builder=get_zip_builder(),
        output_dir=OUTPUTS_DIR,
    )


# ─── Orchestrator ──────────────────────────────────────────────────────────


@lru_cache
def get_orchestrator() -> Orchestrator:
    """Provide the Lead Orchestrator."""
    return Orchestrator(
        parse_usecase=get_parse_usecase(),
        diagrams_usecase=get_diagrams_usecase(),
        scaffold_usecase=get_scaffold_usecase(),
    )
