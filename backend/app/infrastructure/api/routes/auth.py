"""
Auth Route — POST /api/auth/signup, POST /api/auth/login, GET /api/auth/me

Handles user registration, login, and current-user retrieval.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.application.auth_usecase import AuthUseCase, AuthError
from app.infrastructure.api.schemas.api_schemas import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])

_bearer = HTTPBearer()


def _get_auth_usecase() -> AuthUseCase:
    """Provide the singleton AuthUseCase (injected from dependencies)."""
    from app.infrastructure.api.dependencies import get_auth_usecase
    return get_auth_usecase()


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse, "description": "Email already registered"}},
    summary="Register a new user",
    description="Create a new account. Returns a JWT token on success.",
)
async def signup(request: SignupRequest) -> AuthResponse:
    """
    Register a new user account.

    Validates that the email is not already in use, hashes the password,
    and returns a signed JWT token.
    """
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters.",
        )

    auth = _get_auth_usecase()
    try:
        user, token = await auth.register(
            name=request.name,
            email=request.email,
            password=request.password,
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
        ),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse, "description": "Invalid credentials"}},
    summary="Log in",
    description="Authenticate with email and password. Returns a JWT token.",
)
async def login(request: LoginRequest) -> AuthResponse:
    """
    Log in an existing user.

    Verifies credentials and returns a JWT access token.
    """
    auth = _get_auth_usecase()
    try:
        user, token = await auth.login(
            email=request.email,
            password=request.password,
        )
    except AuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}},
    summary="Get current user",
    description="Return the authenticated user's profile. Requires Bearer token.",
)
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> UserResponse:
    """
    Return the profile of the currently authenticated user.

    Requires a valid Bearer JWT in the Authorization header.
    """
    auth = _get_auth_usecase()
    try:
        user = await auth.get_current_user(credentials.credentials)
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
    )
