"""Result Repository Port — persistence for pipeline outputs per document."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.diagram import DiagramSet
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.project_scaffold import ProjectScaffold


class ResultRepositoryPort(ABC):
    """Stores the schema, diagrams and scaffold generated for a document."""

    @abstractmethod
    async def save_schema(self, schema: ExtractedSchema) -> None: ...

    @abstractmethod
    async def get_schema(self, document_id: str) -> ExtractedSchema | None: ...

    @abstractmethod
    async def save_diagrams(self, diagrams: DiagramSet) -> None: ...

    @abstractmethod
    async def get_diagrams(self, document_id: str) -> DiagramSet | None: ...

    @abstractmethod
    async def save_scaffold(self, scaffold: ProjectScaffold) -> None: ...

    @abstractmethod
    async def get_scaffold(self, document_id: str) -> ProjectScaffold | None: ...
