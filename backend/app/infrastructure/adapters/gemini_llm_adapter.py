"""
Gemini LLM Adapter — concrete implementation of LLMPort using Google Gemini.

Uses the ``google.genai`` SDK. This is the only module that talks to Gemini.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re

from google import genai
from google.genai import types

from app.domain.errors import LLMError
from app.domain.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)

_RETRYABLE_CODES = {408, 429, 500, 502, 503, 504}
_RETRY_AFTER_RE = re.compile(r"retry[^0-9]{0,30}(\d+(?:\.\d+)?)\s*s", re.IGNORECASE)


def _error_code(exc: Exception) -> int | None:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code
    match = re.search(r"\b(408|429|500|502|503|504)\b", str(exc))
    return int(match.group(1)) if match else None


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError, ConnectionError)):
        return True
    text = str(exc)
    if (
        "RESOURCE_EXHAUSTED" in text
        or "UNAVAILABLE" in text
        or "timed out" in text.lower()
    ):
        return True
    return _error_code(exc) in _RETRYABLE_CODES


def _is_quota_error(exc: Exception) -> bool:
    return _error_code(exc) == 429 or "RESOURCE_EXHAUSTED" in str(exc)


class GeminiLLMAdapter(LLMPort):
    """Adapter for the Gemini API with retries, backoff and empty-output checks."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        thinking_budget: int | None = None,
        max_retries: int = 4,
        retry_base_seconds: float = 2.0,
        retry_max_seconds: float = 60.0,
        max_concurrency: int = 3,
        client: genai.Client | None = None,
    ) -> None:
        if client is None:
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Please add it to your .env file."
                )
            client = genai.Client(api_key=api_key)
        self._client = client
        self._model_name = model_name
        self._thinking_budget = thinking_budget
        self._max_retries = max_retries
        self._retry_base = retry_base_seconds
        self._retry_max = retry_max_seconds
        # Caps simultaneous Gemini calls across all agents (rate-limit friendly).
        self._semaphore = asyncio.Semaphore(max_concurrency)

    def _config(
        self,
        system_instruction: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> types.GenerateContentConfig:
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_instruction:
            config.system_instruction = system_instruction
        if json_mode:
            config.response_mime_type = "application/json"
        if self._thinking_budget is not None:
            config.thinking_config = types.ThinkingConfig(
                thinking_budget=self._thinking_budget
            )
        return config

    def _retry_delay(self, exc: Exception, attempt: int) -> float:
        hinted = _RETRY_AFTER_RE.search(str(exc))
        if hinted:
            delay = float(hinted.group(1)) + 1.0
        else:
            delay = self._retry_base * (2**attempt)
        delay += random.uniform(0, self._retry_base)  # jitter
        return min(delay, self._retry_max)

    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """Generate a complete response, retrying transient failures."""
        config = self._config(system_instruction, temperature, max_tokens, json_mode)

        for attempt in range(self._max_retries):
            try:
                async with self._semaphore:
                    response = await self._client.aio.models.generate_content(
                        model=self._model_name, contents=prompt, config=config
                    )
            except Exception as exc:  # noqa: BLE001 - SDK raises many types
                last_attempt = attempt == self._max_retries - 1
                if _is_retryable(exc) and not last_attempt:
                    delay = self._retry_delay(exc, attempt)
                    logger.warning(
                        "Gemini call failed (%s); retry %d/%d in %.1fs",
                        type(exc).__name__,
                        attempt + 1,
                        self._max_retries - 1,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.error("Gemini call failed (model=%s): %s", self._model_name, exc)
                if _is_quota_error(exc):
                    raise LLMError(
                        "The AI service quota has been exhausted. Please try again later."
                    ) from exc
                raise LLMError(
                    "The AI service is currently unavailable. Please try again in a moment."
                ) from exc
            return self._extract_text(response)

        raise LLMError("The AI service is currently unavailable.")  # pragma: no cover

    @staticmethod
    def _extract_text(response) -> str:
        candidates = getattr(response, "candidates", None) or []
        finish = getattr(candidates[0], "finish_reason", None) if candidates else None
        finish_name = (
            getattr(finish, "name", str(finish)) if finish is not None else "UNKNOWN"
        )
        try:
            text = response.text
        except Exception:  # noqa: BLE001 - .text raises on blocked content
            text = None

        if not text or not text.strip():
            logger.error("Gemini returned no text (finish_reason=%s)", finish_name)
            raise LLMError(
                f"The AI returned an empty response (reason: {finish_name}). Please try again."
            )
        if finish_name == "MAX_TOKENS":
            logger.error("Gemini output truncated (finish_reason=MAX_TOKENS)")
            raise LLMError(
                "The AI response was cut off before it finished. Please try again."
            )
        return text
