"""
Auth Routes — POST /api/auth/signup, /login, /logout-all and GET /api/auth/me.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.entities.user import User
from app.domain.errors import AuthError
from app.infrastructure.api.dependencies import (
    Container,
    get_container,
    get_current_user,
    rate_limit_auth,
)
from app.infrastructure.api.schemas.api_schemas import (
    AuthResponse,
    ErrorResponse,
    LoginRequest,
    SignupRequest,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _auth_response(user: User, token: str) -> AuthResponse:
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(id=user.id, name=user.name, email=user.email),
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"}
    },
    dependencies=[Depends(rate_limit_auth)],
    summary="Register a new user",
)
async def signup(
    request: SignupRequest, container: Container = Depends(get_container)
) -> AuthResponse:
    """Register a new account and return a signed JWT."""
    try:
        user, token = await container.auth.register(
            name=request.name, email=request.email, password=request.password
        )
    except AuthError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, exc.user_message) from exc
    return _auth_response(user, token)


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse, "description": "Invalid credentials"}},
    dependencies=[Depends(rate_limit_auth)],
    summary="Log in",
)
async def login(
    request: LoginRequest, container: Container = Depends(get_container)
) -> AuthResponse:
    """Verify credentials and return a JWT access token."""
    try:
        user, token = await container.auth.login(
            email=request.email, password=request.password
        )
    except AuthError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid email or password."
        ) from exc
    return _auth_response(user, token)


@router.get(
    "/me",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse, "description": "Unauthorized"}},
    summary="Get current user",
)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the authenticated user."""
    return UserResponse(id=user.id, name=user.name, email=user.email)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out everywhere",
    description="Invalidate every token issued to the current user.",
)
async def logout_all(
    user: User = Depends(get_current_user),
    container: Container = Depends(get_container),
) -> None:
    await container.auth.revoke_all_tokens(user)
