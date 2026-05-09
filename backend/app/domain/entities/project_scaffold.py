"""
Project Scaffold entity — represents the generated project structure and files.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class GeneratedFile(BaseModel):
    """A single generated file within the project scaffold."""

    path: str  # Relative path within the scaffold, e.g. "app/models.py"
    content: str = ""
    language: str = "python"


class ProjectScaffold(BaseModel):
    """
    The complete scaffolded project output from the Scaffolder Agent.

    Contains the full directory tree as a list of generated files,
    plus metadata about the project structure.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    project_name: str = "generated-project"
    directory_tree: str = ""  # ASCII tree representation
    files: list[GeneratedFile] = Field(default_factory=list)
    zip_path: str = ""  # Path to the generated ZIP file
