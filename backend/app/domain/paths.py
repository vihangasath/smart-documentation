"""Pure helpers for turning untrusted names/paths into safe ones."""

from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath

_SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


def slugify(name: str, *, default: str = "project", max_length: int = 64) -> str:
    """Reduce ``name`` to ``[A-Za-z0-9._-]`` (max ``max_length`` chars)."""
    slug = _SLUG_RE.sub("-", name.strip()).strip("-.")[:max_length].strip("-.")
    return slug or default


def safe_relative_path(path: str) -> str | None:
    """
    Normalise an archive-relative file path.

    Returns ``None`` for anything that is empty, absolute, drive-qualified or
    that contains a ``..`` component, so callers can reject it.
    """
    if not path or "\x00" in path:
        return None
    candidate = path.replace("\\", "/")
    posix = PurePosixPath(candidate)
    if posix.is_absolute() or PureWindowsPath(path).drive:
        return None
    parts = [p for p in posix.parts if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        return None
    return "/".join(parts)


def safe_filename(filename: str, *, default: str = "upload") -> str:
    """Return the final component of ``filename`` reduced to safe characters."""
    base = PureWindowsPath(filename.replace("/", "\\")).name
    return slugify(base, default=default, max_length=128)
