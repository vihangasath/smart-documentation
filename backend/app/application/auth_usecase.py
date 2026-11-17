"""
Auth Use Case — register users, authenticate credentials, decode tokens.

Uses bcrypt for password hashing and signed JWTs (PyJWT) for session tokens.
Tokens carry the user's ``token_version``; bumping it revokes all earlier tokens.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.domain.entities.user import User
from app.domain.errors import AuthError
from app.domain.ports.user_store_port import UserStorePort

__all__ = ["AuthError", "AuthUseCase"]


class AuthUseCase:
    """Handles registration, login, token verification and token revocation."""

    def __init__(
        self,
        user_store: UserStorePort,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        expire_days: int = 7,
    ) -> None:
        self._store = user_store
        self._secret = jwt_secret
        self._algorithm = jwt_algorithm
        self._expire_days = expire_days
        # Used to keep login timing similar for unknown emails.
        self._dummy_hash = bcrypt.hashpw(b"structify-dummy", bcrypt.gensalt()).decode()

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    async def _hash_password(plain: str) -> str:
        return (
            await asyncio.to_thread(bcrypt.hashpw, plain.encode(), bcrypt.gensalt())
        ).decode()

    @staticmethod
    async def _verify_password(plain: str, hashed: str) -> bool:
        try:
            return await asyncio.to_thread(
                bcrypt.checkpw, plain.encode(), hashed.encode()
            )
        except ValueError:  # e.g. password longer than 72 bytes
            return False

    def _create_token(self, user: User) -> str:
        expire = datetime.now(UTC) + timedelta(days=self._expire_days)
        payload = {"sub": user.id, "ver": user.token_version, "exp": expire}
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def _decode_token(self, token: str) -> tuple[str, int]:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.PyJWTError as exc:
            raise AuthError("Invalid or expired token.") from exc
        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Invalid or expired token.")
        return user_id, int(payload.get("ver", 0))

    # ── Use Cases ──────────────────────────────────────────────────────────

    async def register(self, name: str, email: str, password: str) -> tuple[User, str]:
        """Register a new user. Raises AuthError if the email is taken."""
        if await self._store.email_exists(email):
            raise AuthError("An account with this email already exists.")

        user = User(
            name=name, email=email, hashed_password=await self._hash_password(password)
        )
        await self._store.save(user)
        return user, self._create_token(user)

    async def login(self, email: str, password: str) -> tuple[User, str]:
        """Authenticate an existing user. Raises AuthError on bad credentials."""
        user = await self._store.find_by_email(email)
        hashed = user.hashed_password if user else self._dummy_hash
        valid = await self._verify_password(password, hashed)
        if not user or not valid:
            raise AuthError("Invalid email or password.")
        return user, self._create_token(user)

    async def get_current_user(self, token: str) -> User:
        """Validate a token and return its user. Raises AuthError otherwise."""
        user_id, version = self._decode_token(token)
        user = await self._store.find_by_id(user_id)
        if not user or user.token_version != version:
            raise AuthError("Invalid or expired token.")
        return user

    async def revoke_all_tokens(self, user: User) -> None:
        """Invalidate every token issued to ``user`` so far."""
        user.token_version += 1
        await self._store.save(user)
