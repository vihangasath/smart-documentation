"""
Base Agent — shared foundation for all specialized AI agents.

Handles knowledge anchor injection and provides common prompt construction.
"""

from __future__ import annotations

from collections.abc import Mapping

from app.domain.ports.llm_port import LLMPort


class BaseAgent:
    """
    Base class for all AI agents in the swarm.

    Responsibilities:
    - Inject the knowledge-anchor sections the agent cares about into its prompts.
    - Provide structured prompt construction helpers.
    - Store the LLM port dependency.
    """

    AGENT_NAME: str = "BaseAgent"
    #: Titles of the knowledge-anchor sections this agent needs.
    ANCHOR_SECTIONS: tuple[str, ...] = ()

    def __init__(
        self, llm: LLMPort, knowledge: Mapping[str, str] | None = None
    ) -> None:
        self._llm = llm
        knowledge = knowledge or {}
        self._knowledge_context = "\n\n".join(
            f"### {title}\n{knowledge[title]}"
            for title in self.ANCHOR_SECTIONS
            if knowledge.get(title)
        )

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
        """
        parts: list[str] = []

        if self._knowledge_context:
            parts.append(
                "=== ARCHITECTURAL REFERENCE ===\n"
                f"{self._knowledge_context}\n"
                "=== END REFERENCE ===\n"
            )
        if additional_context:
            parts.append(
                f"=== ADDITIONAL CONTEXT ===\n{additional_context}\n=== END CONTEXT ===\n"
            )
        if srs_content:
            parts.append(
                f"=== SRS DOCUMENT CONTENT ===\n{srs_content}\n=== END SRS DOCUMENT ===\n"
            )
        parts.append(f"=== TASK ===\n{task_prompt}\n=== END TASK ===")
        return "\n\n".join(parts)
