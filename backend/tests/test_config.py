import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_requires_a_strong_jwt_secret(tmp_path):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production", jwt_secret_key="")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production", jwt_secret_key="short")
    ok = Settings(_env_file=None, app_env="production", jwt_secret_key="k" * 32)
    assert ok.is_production and ok.uploads_dir.as_posix().startswith("/tmp")


def test_development_gets_a_random_secret_and_postgres_urls_are_normalised():
    a = Settings(_env_file=None, app_env="development")
    b = Settings(_env_file=None, app_env="development")
    assert len(a.jwt_secret_key) >= 32 and a.jwt_secret_key != b.jwt_secret_key

    pg = Settings(_env_file=None, database_url="postgres://u:p@h/db")
    assert pg.database_url == "postgresql+psycopg://u:p@h/db"
