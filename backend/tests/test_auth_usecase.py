import datetime as dt

import jwt
import pytest

from app.domain.errors import AuthError


@pytest.fixture
def auth(container):
    return container.auth


async def test_register_login_and_token(auth):
    user, token = await auth.register("Ann", "ann@example.com", "password123")
    assert (await auth.get_current_user(token)).id == user.id

    logged_in, token2 = await auth.login("ANN@example.com", "password123")
    assert logged_in.id == user.id and token2


async def test_duplicate_email_and_bad_password(auth):
    await auth.register("Ann", "ann@example.com", "password123")
    with pytest.raises(AuthError):
        await auth.register("Ann2", "ann@example.com", "password123")
    with pytest.raises(AuthError):
        await auth.login("ann@example.com", "wrong-password")
    with pytest.raises(AuthError):
        await auth.login("nobody@example.com", "password123")


async def test_forged_expired_and_garbage_tokens(auth, container):
    user, _ = await auth.register("Ann", "ann@example.com", "password123")
    secret = container.settings.jwt_secret_key

    forged = jwt.encode(
        {"sub": user.id, "ver": 0}, "another-secret-" + "y" * 40, algorithm="HS256"
    )
    expired = jwt.encode(
        {
            "sub": user.id,
            "ver": 0,
            "exp": dt.datetime.now(dt.UTC) - dt.timedelta(hours=1),
        },
        secret,
        algorithm="HS256",
    )
    for bad in (forged, expired, "garbage", ""):
        with pytest.raises(AuthError):
            await auth.get_current_user(bad)


async def test_revoke_all_tokens(auth):
    user, token = await auth.register("Ann", "ann@example.com", "password123")
    await auth.revoke_all_tokens(user)
    with pytest.raises(AuthError):
        await auth.get_current_user(token)
    _, fresh = await auth.login("ann@example.com", "password123")
    assert await auth.get_current_user(fresh)
