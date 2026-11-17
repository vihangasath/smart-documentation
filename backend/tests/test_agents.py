import json

import pytest

from app.agents.parser_agent import ParserAgent
from app.agents.scaffolder_agent import ScaffolderAgent
from app.domain.errors import LLMError

from .conftest import SCHEMA_JSON, FakeLLM

RAW = json.dumps(SCHEMA_JSON)


@pytest.fixture
def parser():
    return ParserAgent(FakeLLM())


@pytest.mark.parametrize(
    "raw",
    [
        RAW,
        f"```json\n{RAW}\n```",
        f"Sure, here you go:\n{RAW}\nHope that helps!",
    ],
)
def test_parser_accepts_fenced_and_chatty_json(parser, raw):
    schema = parser._parse_response("doc", raw)
    assert schema.project_name == "Library System"
    assert [e.name for e in schema.entities] == ["Book", "Member"]


@pytest.mark.parametrize("raw", ["", "not json", "{broken", "[1, 2]", None])
def test_parser_rejects_unusable_output(parser, raw):
    with pytest.raises(LLMError):
        parser._parse_response("doc", raw)


def test_parser_tolerates_junk_items(parser):
    raw = json.dumps(
        {
            "entities": ["x", {"name": "A", "attributes": [1, {"name": "id"}]}],
            "actions": 5,
        }
    )
    schema = parser._parse_response("doc", raw)
    assert [e.name for e in schema.entities] == ["A"]
    assert [a.name for a in schema.entities[0].attributes] == ["id"]
    assert schema.actions == []


async def test_scaffolder_builds_all_files_and_tree():
    agent = ScaffolderAgent(FakeLLM())
    parser = ParserAgent(FakeLLM())
    schema = parser._parse_response("doc", RAW)

    scaffold = await agent.scaffold(schema)

    assert scaffold.project_name == "Library-System"
    assert {f.path for f in scaffold.files} >= {
        "main.py",
        "models.py",
        "routes.py",
        "requirements.txt",
    }
    assert all(
        f.content == "print('hello')\n" for f in scaffold.files
    )  # fences stripped
    assert "main.py" in scaffold.directory_tree


async def test_scaffolder_surfaces_llm_failure():
    llm = FakeLLM()
    llm.fail_for.add("ONE file")
    schema = ParserAgent(llm)._parse_response("doc", RAW)
    with pytest.raises(LLMError):
        await ScaffolderAgent(llm).scaffold(schema)
