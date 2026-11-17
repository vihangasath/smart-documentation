"""Loads the knowledge anchor and splits it into named sections."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def load_knowledge_anchor(path: Path) -> dict[str, str]:
    """
    Return ``{section title: section text}`` for every ``## `` section.

    A missing file is logged as a warning and yields an empty mapping, so the
    agents still run (just without the reference context).
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("Knowledge anchor not found at %s; agents run without it.", path)
        return {}

    matches = list(_HEADING.finditer(text))
    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.end() : end].strip()
    return sections
