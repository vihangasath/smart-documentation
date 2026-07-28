"""
Auth Use Case — register users, authenticate credentials, decode tokens.

Covers all auth-related business logic, keeping it outside the HTTP layer.
Uses bcrypt for password hashing and HS256 JWT for session tokens.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings
from app.domain.entities.user import User
from app.domain.ports.user_store_port import UserStorePort


class AuthError(Exception):
    """Raised for auth-related failures (invalid credentials, duplicate email, etc.)."""


class AuthUseCase:
    """
    Application-layer use case for user authentication.

    Handles:
    - Registration (hashing password, checking duplicate email)
    - Login (verifying password, issuing JWT)
    - Token verification (decoding JWT, fetching user)
    """

    def __init__(self, user_store: UserStorePort) -> None:
        self._store = user_store
        self._settings = get_settings()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _hash_password(self, plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def _create_token(self, user_id: str) -> str:
        """Create a signed JWT with a configured expiry."""
        expire = datetime.now(timezone.utc) + timedelta(
            days=self._settings.jwt_expire_days
        )
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )

    def _decode_token(self, token: str) -> str:
        """Decode a JWT and return the user_id (sub claim). Raises AuthError on failure."""
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
            user_id: str | None = payload.get("sub")
            if not user_id:
                raise AuthError("Token payload missing subject.")
            return user_id
        except JWTError as exc:
            raise AuthError(f"Invalid or expired token: {exc}") from exc

    # ── Use Cases ──────────────────────────────────────────────────────────

    async def register(self, name: str, email: str, password: str) -> tuple[User, str]:
        """
        Register a new user.

        Args:
            name: Display name.
            email: Email address (must be unique).
            password: Plain-text password (will be hashed).

        Returns:
            Tuple of (new User entity, JWT token string).

        Raises:
            AuthError: If the email is already registered.
        """
        if await self._store.email_exists(email):
            raise AuthError(f"An account with '{email}' already exists.")

        user = User(
            name=name,
            email=email,
            hashed_password=self._hash_password(password),
        )
        await self._store.save(user)
        token = self._create_token(user.id)
        return user, token

    async def login(self, email: str, password: str) -> tuple[User, str]:
        """
        Authenticate an existing user.

        Args:
            email: Registered email address.
            password: Plain-text password to verify.

        Returns:
            Tuple of (User entity, JWT token string).

        Raises:
            AuthError: If credentials are invalid.
        """
        user = await self._store.find_by_email(email)
        if not user or not self._verify_password(password, user.hashed_password):
            raise AuthError("Invalid email or password.")

        token = self._create_token(user.id)
        return user, token

    async def get_current_user(self, token: str) -> User:
        """
        Validate a token and return the associated user.

        Args:
            token: Raw JWT string (without 'Bearer ' prefix).

        Returns:
            The authenticated User entity.

        Raises:
            AuthError: If the token is invalid or the user no longer exists.
        """
        user_id = self._decode_token(token)
        user = await self._store.find_by_id(user_id)
        if not user:
            raise AuthError("User not found.")
        return user
