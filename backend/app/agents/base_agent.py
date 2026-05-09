"""
Base Agent — shared foundation for all specialized AI agents.

Handles knowledge anchor injection and provides common LLM interaction patterns.
"""

from __future__ import annotations

from pathlib import Path

from app.domain.ports.llm_port import LLMPort
from app.config import KNOWLEDGE_ANCHOR_PATH


class BaseAgent:
    """
    Base class for all AI agents in the swarm.

    Responsibilities:
    - Load and inject knowledge_anchor.md context into every prompt.
    - Provide structured prompt construction helpers.
    - Store the LLM port dependency.
    """

    AGENT_NAME: str = "BaseAgent"

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm
        self._knowledge_context = self._load_knowledge_anchor()

    def _load_knowledge_anchor(self) -> str:
        """
        Load the knowledge anchor document for context injection.

        As specified in the system architecture: the Lead Agent pulls data from
        knowledge_anchor.md and prepends it to every agent prompt to ensure
        the agents remain grounded in high-quality system design principles.
        """
        anchor_path = KNOWLEDGE_ANCHOR_PATH
        if anchor_path.exists():
            return anchor_path.read_text(encoding="utf-8")
        return ""

    def _build_prompt(
        self,
        task_prompt: str,
        srs_content: str = "",
        additional_context: str = "",
    ) -> str:
        """
        Construct a complete prompt with knowledge anchor context.

        Args:
            task_prompt: The specific task instruction for this agent.
            srs_content: Raw SRS document content (if applicable).
            additional_context: Any extra context to inject.

        Returns:
            Fully assembled prompt string.
        """
        parts: list[str] = []

        if self._knowledge_context:
            parts.append(
                "=== ARCHITECTURAL REFERENCE (Knowledge Anchor) ===\n"
                f"{self._knowledge_context}\n"
                "=== END REFERENCE ===\n"
            )

        if additional_context:
            parts.append(
                "=== ADDITIONAL CONTEXT ===\n"
                f"{additional_context}\n"
                "=== END CONTEXT ===\n"
            )

        if srs_content:
            parts.append(
                "=== SRS DOCUMENT CONTENT ===\n"
                f"{srs_content}\n"
                "=== END SRS DOCUMENT ===\n"
            )

        parts.append(f"=== TASK ===\n{task_prompt}\n=== END TASK ===")

        return "\n\n".join(parts)
