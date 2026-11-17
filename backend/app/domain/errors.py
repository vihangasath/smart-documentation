"""
Domain errors.

``DomainError`` carries a message that is safe to show to end users. Anything
else (raw SDK exceptions, file-system errors, ...) is logged server-side and
replaced with a generic message before it reaches a client.
"""

from __future__ import annotations


class DomainError(Exception):
    """An expected failure whose message is safe to show to the user."""

    def __init__(self, user_message: str, *, code: str = "DOMAIN_ERROR") -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.code = code


class AuthError(DomainError):
    """Invalid credentials, duplicate email, bad token, etc."""

    def __init__(self, user_message: str) -> None:
        super().__init__(user_message, code="AUTH_ERROR")


class LLMError(DomainError):
    """The language model failed or returned unusable output."""

    def __init__(self, user_message: str) -> None:
        super().__init__(user_message, code="LLM_ERROR")


class DocumentError(DomainError):
    """The uploaded document could not be read or is unusable."""

    def __init__(self, user_message: str) -> None:
        super().__init__(user_message, code="DOCUMENT_ERROR")
