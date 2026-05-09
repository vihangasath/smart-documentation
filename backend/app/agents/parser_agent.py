"""
Parser Agent — NLP specialist for extracting entities, relationships, and actions
from SRS documents.

This agent focuses on finding nouns (entities) and verbs (actions) in the SRS,
then mapping them to a structured JSON schema.
"""

from __future__ import annotations

import json

from app.agents.base_agent import BaseAgent
from app.domain.ports.llm_port import LLMPort
from app.domain.entities.extracted_schema import (
    ExtractedSchema,
    EntityDefinition,
    Attribute,
    Relationship,
    Action,
)


class ParserAgent(BaseAgent):
    """
    Specialized agent for SRS document analysis.

    Extracts:
    - Domain entities (nouns) with their attributes
    - Relationships between entities
    - Functional actions/API endpoints (verbs)
    """

    AGENT_NAME = "ParserAgent"

    SYSTEM_INSTRUCTION = """You are an expert Software Requirements Analyst and Domain-Driven Design specialist.

Your task is to analyze a Software Requirements Specification (SRS) document and extract a structured domain model.

You MUST extract:
1. **Entities**: The core domain objects (nouns). For each entity, identify its attributes with data types.
2. **Relationships**: How entities relate to each other (one-to-one, one-to-many, many-to-many).
3. **Actions**: Functional operations/API endpoints (verbs). Map each to an actor, target entity, HTTP method, and route.

You MUST respond with ONLY valid JSON in this exact format (no markdown, no explanation):
{
    "project_name": "string",
    "description": "string",
    "entities": [
        {
            "name": "string",
            "description": "string",
            "attributes": [
                {"name": "string", "data_type": "string", "is_required": true, "description": "string"}
            ]
        }
    ],
    "relationships": [
        {"source": "string", "target": "string", "relationship_type": "one-to-many", "label": "string"}
    ],
    "actions": [
        {
            "name": "string",
            "description": "string",
            "actor": "string",
            "target_entity": "string",
            "http_method": "GET|POST|PUT|DELETE",
            "endpoint": "/api/..."
        }
    ]
}

Follow Clean Architecture and DDD principles. Identify bounded contexts where appropriate.
Be thorough — extract ALL entities, even implicit ones. Include IDs, timestamps, and foreign keys as attributes."""

    def __init__(self, llm: LLMPort) -> None:
        super().__init__(llm)

    async def analyze(
        self, document_id: str, srs_content: str
    ) -> ExtractedSchema:
        """
        Analyze an SRS document and extract a structured schema.

        Args:
            document_id: ID of the source SRS document.
            srs_content: Raw text content of the SRS document.

        Returns:
            ExtractedSchema with entities, relationships, and actions.
        """
        prompt = self._build_prompt(
            task_prompt=(
                "Analyze the above SRS document thoroughly. "
                "Extract ALL domain entities, their attributes, relationships, "
                "and functional actions. Return ONLY valid JSON."
            ),
            srs_content=srs_content,
        )

        raw_response = await self._llm.generate(
            prompt=prompt,
            system_instruction=self.SYSTEM_INSTRUCTION,
            temperature=0.3,  # Lower temperature for structured output
            max_tokens=8192,
        )

        return self._parse_response(document_id, raw_response)

    def _parse_response(
        self, document_id: str, raw_response: str
    ) -> ExtractedSchema:
        """Parse LLM JSON response into an ExtractedSchema entity."""
        cleaned = raw_response.strip()

        # Strip markdown code fences
        if "```" in cleaned:
            import re
            # Extract content between ``` fences
            fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
            if fence_match:
                cleaned = fence_match.group(1).strip()

        # Robustly find the outermost JSON object (handles thinking-model preamble)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            # Log the parse failure for debugging and return minimal schema
            print(f"[ParserAgent] JSON parse failed: {exc}")
            print(f"[ParserAgent] Raw response (first 500 chars): {raw_response[:500]}")
            return ExtractedSchema(
                document_id=document_id,
                raw_analysis=raw_response,
            )

        entities = [
            EntityDefinition(
                name=e.get("name", "Unknown"),
                description=e.get("description", ""),
                attributes=[
                    Attribute(
                        name=a.get("name", ""),
                        data_type=a.get("data_type", "string"),
                        is_required=a.get("is_required", True),
                        description=a.get("description", ""),
                    )
                    for a in e.get("attributes", [])
                ],
            )
            for e in data.get("entities", [])
        ]

        relationships = [
            Relationship(
                source=r.get("source", ""),
                target=r.get("target", ""),
                relationship_type=r.get("relationship_type", "one-to-many"),
                label=r.get("label", ""),
            )
            for r in data.get("relationships", [])
        ]

        actions = [
            Action(
                name=a.get("name", ""),
                description=a.get("description", ""),
                actor=a.get("actor", ""),
                target_entity=a.get("target_entity", ""),
                http_method=a.get("http_method", "GET"),
                endpoint=a.get("endpoint", ""),
            )
            for a in data.get("actions", [])
        ]

        return ExtractedSchema(
            document_id=document_id,
            project_name=data.get("project_name", "Untitled Project"),
            description=data.get("description", ""),
            entities=entities,
            relationships=relationships,
            actions=actions,
            raw_analysis=raw_response,
        )
