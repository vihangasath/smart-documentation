"""
Diagrammer Agent — Mermaid.js specialist that converts extracted schemas
into visual diagrams.

Generates Class Diagrams, ER Diagrams, and Sequence Diagrams from the
structured output of the Parser Agent.
"""

from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.domain.ports.llm_port import LLMPort
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.diagram import Diagram, DiagramType, DiagramSet
from app.infrastructure.adapters.mermaid_validator import MermaidValidator


class DiagrammerAgent(BaseAgent):
    """
    Specialized agent for generating validated Mermaid.js diagrams.

    Supports: Class, ER, Sequence, Flowchart, and Architecture diagrams.
    Each diagram is validated against Mermaid syntax rules before output.
    """

    AGENT_NAME = "DiagrammerAgent"

    SYSTEM_INSTRUCTIONS: dict[DiagramType, str] = {
        DiagramType.CLASS: """You are an expert Mermaid.js diagrammer specializing in Class Diagrams.

Generate a valid Mermaid.js Class Diagram from the provided schema.

Rules:
- Start with `classDiagram`
- Include ALL entities as classes with their attributes and types
- Show relationships using proper Mermaid notation:
  - Inheritance: `<|--`
  - Composition: `*--`
  - Aggregation: `o--`
  - Association: `-->`
- Add cardinality labels where appropriate
- Use proper access modifiers: + (public), - (private), # (protected)

Return ONLY the raw Mermaid code. No markdown fences, no explanation.""",
        DiagramType.ER: """You are an expert Mermaid.js diagrammer specializing in Entity-Relationship Diagrams.

Generate a valid Mermaid.js ER Diagram from the provided schema.

Rules:
- Start with `erDiagram`
- Use Crow's foot notation for cardinality (e.g., ||--o{, }o--||)
- Use solid lines (--) for identifying relationships
- Use dashed lines (..) for non-identifying relationships
- Define attributes in blocks delimited by {} using format: type name
- Append key constraints: PK, FK, UK
- Use entity aliases with square brackets if needed

Return ONLY the raw Mermaid code. No markdown fences, no explanation.""",
        DiagramType.SEQUENCE: """You are an expert Mermaid.js diagrammer specializing in Sequence Diagrams.

Generate a valid Mermaid.js Sequence Diagram from the provided schema.

Rules:
- Start with `sequenceDiagram`
- Model the primary user flows from the actions
- Use proper participant declarations
- Show request/response patterns with arrows (->> and -->>)
- Include activation bars where appropriate
- Add notes for important business logic

Return ONLY the raw Mermaid code. No markdown fences, no explanation.""",
        DiagramType.FLOWCHART: """You are an expert Mermaid.js diagrammer specializing in Flowcharts.

Generate a valid Mermaid.js Flowchart from the provided schema.

Rules:
- Start with `flowchart TD` (top-down) or `flowchart LR` (left-right)
- Map the overall system flow from input to output
- Use proper node shapes: [] for process, {} for decision, () for terminal
- Connect with labeled arrows

Return ONLY the raw Mermaid code. No markdown fences, no explanation.""",
        DiagramType.ARCHITECTURE: """You are an expert Mermaid.js diagrammer specializing in Architecture Diagrams.

Generate a valid Mermaid.js Architecture Diagram from the provided schema.

Rules:
- Start with `architecture-beta`
- Use groups, services, edges, and junctions
- Declare groups: group id(icon)[Label]
- Declare services: service id(icon)[Label] in group_id
- Only use default icons: cloud, database, disk, internet, server
- Connect with edges: service1:R --> L:service2

Return ONLY the raw Mermaid code. No markdown fences, no explanation.""",
    }

    def __init__(self, llm: LLMPort) -> None:
        super().__init__(llm)
        self._validator = MermaidValidator()

    async def generate_all(
        self, schema: ExtractedSchema
    ) -> DiagramSet:
        """
        Generate all applicable diagram types for the given schema.

        Args:
            schema: Extracted schema from the Parser Agent.

        Returns:
            DiagramSet containing all generated diagrams.
        """
        diagram_types = [
            DiagramType.ER,
            DiagramType.CLASS,
            DiagramType.SEQUENCE,
        ]

        diagrams: list[Diagram] = []
        for dtype in diagram_types:
            diagram = await self.generate_single(schema, dtype)
            diagrams.append(diagram)

        return DiagramSet(
            document_id=schema.document_id,
            diagrams=diagrams,
        )

    async def generate_single(
        self,
        schema: ExtractedSchema,
        diagram_type: DiagramType,
    ) -> Diagram:
        """
        Generate a single Mermaid diagram of the specified type.

        Args:
            schema: Extracted schema from the Parser Agent.
            diagram_type: Type of diagram to generate.

        Returns:
            A validated Diagram entity.
        """
        system_instruction = self.SYSTEM_INSTRUCTIONS.get(
            diagram_type,
            self.SYSTEM_INSTRUCTIONS[DiagramType.CLASS],
        )

        schema_context = schema.model_dump_json(indent=2)

        prompt = self._build_prompt(
            task_prompt=(
                f"Generate a {diagram_type.value} diagram from the following "
                f"extracted schema. Return ONLY valid Mermaid.js code."
            ),
            additional_context=schema_context,
        )

        mermaid_code = await self._llm.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.4,
            max_tokens=4096,
        )

        # Clean up any markdown fences
        mermaid_code = self._clean_mermaid_output(mermaid_code)

        # Validate the syntax
        is_valid, errors = self._validator.validate(mermaid_code)

        # If invalid, attempt one retry with error feedback
        if not is_valid:
            mermaid_code = await self._retry_with_feedback(
                schema_context, diagram_type, system_instruction,
                mermaid_code, errors,
            )
            is_valid, errors = self._validator.validate(mermaid_code)

        return Diagram(
            document_id=schema.document_id,
            diagram_type=diagram_type,
            title=f"{schema.project_name} — {diagram_type.value.title()} Diagram",
            mermaid_code=mermaid_code,
            is_valid=is_valid,
            validation_errors=errors,
        )

    async def _retry_with_feedback(
        self,
        schema_context: str,
        diagram_type: DiagramType,
        system_instruction: str,
        previous_code: str,
        errors: list[str],
    ) -> str:
        """Retry diagram generation with validation error feedback."""
        retry_prompt = self._build_prompt(
            task_prompt=(
                f"The previous {diagram_type.value} diagram had syntax errors:\n"
                f"Errors: {errors}\n\n"
                f"Previous code:\n{previous_code}\n\n"
                f"Fix ALL syntax errors and return ONLY valid Mermaid.js code."
            ),
            additional_context=schema_context,
        )

        result = await self._llm.generate(
            prompt=retry_prompt,
            system_instruction=system_instruction,
            temperature=0.2,
            max_tokens=4096,
        )
        return self._clean_mermaid_output(result)

    def _clean_mermaid_output(self, raw: str) -> str:
        """Remove markdown code fences from LLM output."""
        cleaned = raw.strip()
        if cleaned.startswith("```mermaid"):
            cleaned = cleaned[len("```mermaid") :]
        elif cleaned.startswith("```"):
            first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
            cleaned = cleaned[first_newline + 1 :]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()
