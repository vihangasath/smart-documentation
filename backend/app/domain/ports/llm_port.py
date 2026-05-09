"""
LLM Port — abstract interface for Large Language Model interactions.

All LLM-specific details (API keys, model names, retry logic) live in the adapter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


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
    ) -> str:
        """
        Generate a complete text response from the LLM.

        Args:
            prompt: The user/task prompt.
            system_instruction: System-level instruction for the model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.

        Returns:
            Generated text response.
        """
        ...

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """
        Stream text response chunks from the LLM.

        Args:
            prompt: The user/task prompt.
            system_instruction: System-level instruction for the model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.

        Yields:
            Text chunks as they are generated.
        """
        ...
