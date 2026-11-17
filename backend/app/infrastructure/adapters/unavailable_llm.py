"""LLM stand-in used in development when no Gemini API key is configured."""

from __future__ import annotations

from app.domain.errors import LLMError
from app.domain.ports.llm_port import LLMPort


class UnavailableLLM(LLMPort):
    """Fails every call with a clear message instead of crashing the whole app."""

    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        raise LLMError("GEMINI_API_KEY is not configured on the server.")
