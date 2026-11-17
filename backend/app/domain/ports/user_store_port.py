"""
User Store Port — abstract interface for user persistence.

All user-store-specific details (storage backend, queries) live in adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.user import User


class UserStorePort(ABC):
    """Port for user storage operations."""

    @abstractmethod
    async def save(self, user: User) -> None:
        """Insert or update a user."""
        ...

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Look up a user by email. Returns None if not found."""
        ...

    @abstractmethod
    async def find_by_id(self, user_id: str) -> User | None:
        """Look up a user by ID. Returns None if not found."""
        ...

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check whether an email is already registered."""
        ...
