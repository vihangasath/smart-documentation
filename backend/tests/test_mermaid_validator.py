import pytest

from app.infrastructure.adapters.mermaid_validator import MermaidValidator

from .conftest import ARCH, CLASS, ER, SEQUENCE

v = MermaidValidator()


@pytest.mark.parametrize(
    "code",
    [
        ER,  # regression: crow's-foot braces used to count as unclosed brackets
        CLASS,
        SEQUENCE,
        ARCH,
        "flowchart TD\n    A[Start] --> B{Ok?}\n    B -->|yes| C((End))",
        "graph LR\n    A --> B",
        "sequenceDiagram\n    Note over A: (maybe [later",  # free text is not bracket-checked
        "%% comment\nerDiagram\n    A ||--|{ B : has\n    B }o..o{ C : links",
        "---\ntitle: x\n---\nclassDiagram\n    class A",
    ],
)
def test_valid_diagrams(code):
    ok, errors = v.validate(code)
    assert ok, errors


@pytest.mark.parametrize(
    "code",
    [
        "",
        "   ",
        "erDiagram",  # no body
        "graphics TD\n    A --> B",  # header must be a whole word
        "not a diagram\n    A --> B",
        "classDiagram\n    class A {\n        +int x",  # unclosed brace
        "flowchart TD\n    A[Start --> B",
        "flowchart TD\n    A --> B]",
    ],
)
def test_invalid_diagrams(code):
    ok, errors = v.validate(code)
    assert not ok
    assert errors
