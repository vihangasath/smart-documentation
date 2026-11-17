"""Shared fixtures: a fake LLM and an app wired with it against a temp SQLite DB."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.domain.errors import LLMError
from app.domain.ports.llm_port import LLMPort
from app.infrastructure.api.dependencies import build_container
from app.main import create_app

SCHEMA_JSON = {
    "project_name": "Library System",
    "description": "Lend books to members.",
    "entities": [
        {
            "name": "Book",
            "description": "A book",
            "attributes": [
                {
                    "name": "id",
                    "data_type": "uuid",
                    "is_required": True,
                    "description": "",
                },
                {
                    "name": "title",
                    "data_type": "string",
                    "is_required": True,
                    "description": "",
                },
            ],
        },
        {"name": "Member", "description": "A member", "attributes": []},
    ],
    "relationships": [
        {
            "source": "Member",
            "target": "Book",
            "relationship_type": "one-to-many",
            "label": "borrows",
        }
    ],
    "actions": [
        {
            "name": "List books",
            "description": "",
            "actor": "Member",
            "target_entity": "Book",
            "http_method": "GET",
            "endpoint": "/api/books",
        }
    ],
}

ER = """erDiagram
    MEMBER ||--o{ LOAN : borrows
    BOOK ||--o{ LOAN : "is lent (often)"
    BOOK {
        uuid id PK
        string title
    }"""
CLASS = "classDiagram\n    class Book {\n        +uuid id\n        +string title\n    }"
SEQUENCE = "sequenceDiagram\n    Member->>API: GET /books\n    API-->>Member: 200"
ARCH = "architecture-beta\n    service api(server)[API]\n    service db(database)[DB]\n    api:R --> L:db"


class FakeLLM(LLMPort):
    """Returns canned output chosen by the agent's system instruction."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.fail_for: set[str] = set()  # substrings of system instructions to fail on
        self.overrides: dict[str, str] = {}

    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        self.calls.append(system_instruction[:60])
        for needle in self.fail_for:
            if needle in system_instruction:
                raise LLMError("fake failure")
        for needle, text in self.overrides.items():
            if needle in system_instruction:
                return text
        if "Requirements Analyst" in system_instruction:
            return json.dumps(SCHEMA_JSON)
        if "Entity-Relationship" in system_instruction:
            return ER
        if "Class Diagrams" in system_instruction:
            return "```mermaid\n" + CLASS + "\n```"
        if "Sequence Diagrams" in system_instruction:
            return SEQUENCE
        if "Architecture Diagrams" in system_instruction:
            return ARCH
        if "ONE file" in system_instruction:
            return "```python\nprint('hello')\n```"
        raise AssertionError(
            f"unexpected system instruction: {system_instruction[:80]}"
        )


def make_settings(tmp_path, **overrides) -> Settings:
    values = dict(
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        uploads_dir=tmp_path / "uploads",
        outputs_dir=tmp_path / "outputs",
        jwt_secret_key="test-secret-" + "x" * 40,
        gemini_api_key="",
        auth_rate_limit_per_minute=1000,
        pipeline_runs_per_hour=1000,
        max_active_jobs_per_user=5,
    )
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def settings(tmp_path) -> Settings:
    return make_settings(tmp_path)


@pytest.fixture
def container(settings, fake_llm):
    c = build_container(settings, llm=fake_llm)
    yield c
    c.db.dispose()


@pytest.fixture
def client(container):
    with TestClient(create_app(container)) as c:
        yield c
