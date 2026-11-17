"""Mermaid Validator Port — abstract interface for diagram syntax validation."""

from __future__ import annotations

from abc import ABC, abstractmethod


class MermaidValidatorPort(ABC):
    """Port for validating Mermaid.js source."""

    @abstractmethod
    def validate(self, mermaid_code: str) -> tuple[bool, list[str]]:
        """Return ``(is_valid, error_messages)`` for the given Mermaid code."""
        ...
