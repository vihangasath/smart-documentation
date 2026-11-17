"""
LLM Port — abstract interface for Large Language Model interactions.

All LLM-specific details (API keys, model names, retry logic) live in the adapter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMPort(ABC):
    """
    Port for LLM operations.

    The domain and application layers depend on this abstraction.
    Concrete adapters (e.g., GeminiLLMAdapter) implement it.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """
        Generate a complete text response from the LLM.

        Args:
            prompt: The user/task prompt.
            system_instruction: System-level instruction for the model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.
            json_mode: Ask the model for a syntactically valid JSON document.

        Returns:
            Generated text response (never empty).

        Raises:
            LLMError: If the call fails or the model returns nothing usable.
        """
        ...
