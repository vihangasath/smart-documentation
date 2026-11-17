import zipfile

import pytest

from app.domain.entities.project_scaffold import GeneratedFile, ProjectScaffold
from app.domain.paths import safe_filename, safe_relative_path, slugify
from app.infrastructure.adapters.zip_builder import ZipBuilder


@pytest.mark.parametrize(
    "path",
    ["../x", "a/../../x", "/etc/passwd", "C:\\win\\x", "..", "", "a/..", "x\x00y"],
)
def test_unsafe_paths_rejected(path):
    assert safe_relative_path(path) is None


def test_safe_paths_normalised():
    assert safe_relative_path("./app//models.py") == "app/models.py"
    assert safe_relative_path("a\\b.py") == "a/b.py"


def test_slugify_and_filename():
    assert slugify("../../My Project!!") == "My-Project"
    assert slugify("   ") == "project"
    assert len(slugify("x" * 200)) == 64
    assert safe_filename("../../evil name.pdf") == "evil-name.pdf"


async def test_zip_name_is_unique_per_document_and_traversal_is_skipped(tmp_path):
    def scaffold(doc_id, name):
        return ProjectScaffold(
            document_id=doc_id,
            project_name=name,
            files=[
                GeneratedFile(path="main.py", content="ok"),
                GeneratedFile(path="../../escape.py", content="bad"),
                GeneratedFile(path="/abs.py", content="bad"),
            ],
        )

    builder = ZipBuilder()
    a = await builder.build(scaffold("doc-a", "../../same"), tmp_path)
    b = await builder.build(scaffold("doc-b", "../../same"), tmp_path)

    assert a != b and a.parent == tmp_path and b.parent == tmp_path
    names = zipfile.ZipFile(a).namelist()
    assert names == ["same/README.md", "same/main.py"]
    assert not any(".." in n or n.startswith("/") for n in names)
