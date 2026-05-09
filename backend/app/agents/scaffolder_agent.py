"""
Scaffolder Agent — Python specialist that generates project boilerplate
from extracted schemas.

Creates directory structures, Pydantic models, FastAPI routes, and
configuration files based on the domain entities and actions.
"""

from __future__ import annotations

import json

from app.agents.base_agent import BaseAgent
from app.domain.ports.llm_port import LLMPort
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.project_scaffold import ProjectScaffold, GeneratedFile


class ScaffolderAgent(BaseAgent):
    """
    Specialized agent for generating project boilerplate code.

    Generates:
    - Pydantic models from domain entities
    - FastAPI route handlers from actions
    - requirements.txt with dependencies
    - main.py entrypoint
    - Directory tree structure
    """

    AGENT_NAME = "ScaffolderAgent"

    SYSTEM_INSTRUCTION = """You are an expert Python developer specializing in FastAPI and Clean Architecture.

Your task is to generate production-ready Python project boilerplate from a domain schema.

You MUST generate a complete project with these files:
1. `main.py` — FastAPI app entrypoint with CORS, router includes
2. `models.py` — Pydantic v2 models for ALL entities
3. `routes.py` — FastAPI route handlers for ALL actions/endpoints
4. `requirements.txt` — Python dependencies
5. `config.py` — Settings using pydantic-settings
6. `.env.example` — Environment variable template

Rules:
- Use Pydantic v2 syntax (model_config, Field validators)
- Follow Clean Architecture: separate concerns
- Add proper type hints everywhere
- Include docstrings for all classes and functions
- Use async/await for route handlers
- Include proper HTTP status codes and error handling
- Format code with black-compatible style (88 char line length)

Respond with ONLY valid JSON in this format:
{
    "project_name": "string",
    "directory_tree": "ASCII tree string",
    "files": [
        {"path": "relative/path.py", "content": "file content", "language": "python"}
    ]
}

No markdown fences. No explanation. ONLY JSON."""

    def __init__(self, llm: LLMPort) -> None:
        super().__init__(llm)

    async def scaffold(
        self, schema: ExtractedSchema
    ) -> ProjectScaffold:
        """
        Generate a complete project scaffold from an extracted schema.

        Args:
            schema: Structured schema from the Parser Agent.

        Returns:
            ProjectScaffold with all generated files.
        """
        schema_context = schema.model_dump_json(indent=2)

        prompt = self._build_prompt(
            task_prompt=(
                "Generate a complete Python FastAPI project scaffold "
                "from the above schema. Include ALL entities as Pydantic models "
                "and ALL actions as API route handlers. "
                "Return ONLY valid JSON."
            ),
            additional_context=schema_context,
        )

        raw_response = await self._llm.generate(
            prompt=prompt,
            system_instruction=self.SYSTEM_INSTRUCTION,
            temperature=0.3,
            max_tokens=8192,
        )

        return self._parse_response(schema.document_id, raw_response)

    def _parse_response(
        self, document_id: str, raw_response: str
    ) -> ProjectScaffold:
        """Parse LLM JSON response into a ProjectScaffold entity."""
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            first_newline = cleaned.index("\n")
            cleaned = cleaned[first_newline + 1 :]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: create a minimal scaffold
            return ProjectScaffold(
                document_id=document_id,
                files=[
                    GeneratedFile(
                        path="README.md",
                        content=f"# Generated Project\n\nRaw output:\n{raw_response}",
                        language="markdown",
                    )
                ],
            )

        files = [
            GeneratedFile(
                path=f.get("path", "unknown.py"),
                content=f.get("content", ""),
                language=f.get("language", "python"),
            )
            for f in data.get("files", [])
        ]

        return ProjectScaffold(
            document_id=document_id,
            project_name=data.get("project_name", "generated-project"),
            directory_tree=data.get("directory_tree", ""),
            files=files,
        )
