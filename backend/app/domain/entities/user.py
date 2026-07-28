"""
User entity — represents a registered user in the system.

This is a pure domain object with no infrastructure dependencies.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class User(BaseModel):
    """
    Core entity representing a registered user.

    Attributes:
        id: Unique identifier.
        name: Display name of the user.
        email: Unique email address (used for login).
        hashed_password: bcrypt-hashed password.
        created_at: UTC timestamp of registration.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    hashed_password: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
