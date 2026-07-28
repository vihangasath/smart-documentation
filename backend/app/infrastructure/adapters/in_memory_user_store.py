"""
In-Memory User Store — concrete adapter for user storage.

Stores users in a plain Python dict. All data is lost on server restart.
For production, replace with a database-backed adapter (PostgreSQL, Firestore, etc.).
"""

from __future__ import annotations

from app.domain.entities.user import User
from app.domain.ports.user_store_port import UserStorePort


class InMemoryUserStore(UserStorePort):
    """
    Simple in-memory user store using a Python dict keyed by user ID.

    Note: This is an MVP adapter. Registered users are not persisted
    across server restarts. Replace with a persistent adapter for production.
    """

    def __init__(self) -> None:
        # _by_id: id → User
        self._by_id: dict[str, User] = {}
        # _by_email: email.lower() → User
        self._by_email: dict[str, User] = {}

    async def save(self, user: User) -> None:
        """Store a new user in both lookup dicts."""
        self._by_id[user.id] = user
        self._by_email[user.email.lower()] = user

    async def find_by_email(self, email: str) -> User | None:
        """Return the user with the given email, or None."""
        return self._by_email.get(email.lower())

    async def find_by_id(self, user_id: str) -> User | None:
        """Return the user with the given ID, or None."""
        return self._by_id.get(user_id)

    async def email_exists(self, email: str) -> bool:
        """Return True if the email is already registered."""
        return email.lower() in self._by_email
