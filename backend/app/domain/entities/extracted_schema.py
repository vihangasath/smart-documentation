"""
Extracted Schema entity — the structured output of the Parser Agent.

Represents the entities, relationships, and actions extracted from an SRS document.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Attribute(BaseModel):
    """A single attribute/field of a domain entity."""

    name: str
    data_type: str = "string"
    is_required: bool = True
    description: str = ""


class EntityDefinition(BaseModel):
    """
    A domain entity extracted from the SRS document.

    For example: "User", "Order", "Product" — each with their attributes.
    """

    name: str
    description: str = ""
    attributes: list[Attribute] = Field(default_factory=list)


class Relationship(BaseModel):
    """A relationship between two extracted entities."""

    source: str
    target: str
    relationship_type: str = "one-to-many"
    label: str = ""


class Action(BaseModel):
    """A functional action / API endpoint extracted from the SRS."""

    name: str
    description: str = ""
    actor: str = ""
    target_entity: str = ""
    http_method: str = "GET"
    endpoint: str = ""


class ExtractedSchema(BaseModel):
    """
    Complete structured output from the Parser Agent.

    Contains all entities, relationships, and actions derived from
    the SRS document via LLM-powered NLP analysis.
    """

    document_id: str
    project_name: str = "Untitled Project"
    description: str = ""
    entities: list[EntityDefinition] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    raw_analysis: str = ""
