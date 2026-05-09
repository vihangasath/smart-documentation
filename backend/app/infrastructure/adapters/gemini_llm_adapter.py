"""
Gemini LLM Adapter — concrete implementation of LLMPort using Google Gemini.

Uses the modern `google.genai` SDK (replacing the deprecated `google.generativeai`).
This is the only module that interacts with the Gemini API.
"""

from __future__ import annotations

from typing import AsyncIterator

from google import genai
from google.genai import types

from app.domain.ports.llm_port import LLMPort
from app.config import get_settings


class GeminiLLMAdapter(LLMPort):
    """
    Adapter for Google Gemini API via the `google-genai` SDK.

    Handles client initialization, prompt construction, and both
    synchronous and streaming response generation.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Please add it to your .env file."
            )
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model_name = model_name

    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a complete response from Gemini."""
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        import asyncio
        
        max_retries = 3
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=config,
                )
                return response.text
            except Exception as e:
                last_error = e
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < max_retries - 1:
                        wait_secs = 30 * (attempt + 1)  # 30s, 60s backoff
                        await asyncio.sleep(wait_secs)
                        continue
                    # All retries exhausted — raise a clear message
                    raise RuntimeError(
                        "Gemini API quota exhausted. "
                        "Your free-tier daily limit has been reached. "
                        "Please wait ~24 hours or add billing to your Google AI account. "
                        f"Original error: {error_msg}"
                    ) from e
                # Non-rate-limit error — surface with clear context
                raise RuntimeError(
                    f"Gemini API call failed (model={self._model_name}): {error_msg}"
                ) from e
        # Should not reach here, but satisfy the type checker
        raise last_error or RuntimeError("Unknown Gemini API error")

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream response chunks from Gemini."""
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        async for chunk in self._client.aio.models.generate_content_stream(
            model=self._model_name,
            contents=prompt,
            config=config,
        ):
            if chunk.text:
                yield chunk.text
