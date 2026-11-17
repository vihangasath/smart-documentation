"""
Mermaid Validator — validates Mermaid.js syntax using heuristic checks.

This is a lightweight, dependency-free first line of defence (header, brackets,
empty body). The frontend renderer remains the final authority on syntax.
"""

from __future__ import annotations

import re

from app.domain.ports.mermaid_validator_port import MermaidValidatorPort

_HEADER_RE = re.compile(
    r"^(?:classDiagram(?:-v2)?|erDiagram|sequenceDiagram|flowchart|graph|"
    r"stateDiagram(?:-v2)?|architecture-beta|pie|gantt|gitGraph|mindmap|timeline|"
    r"journey|quadrantChart|requirementDiagram|C4Context|sankey-beta|xychart-beta|"
    r"block-beta)\b"
)
_QUOTED_RE = re.compile(r'"[^"\n]*"')
# Crow's-foot relationship operators such as ||--o{ , }o--|| , |o..o{
_ER_OPERATOR_RE = re.compile(r"[|}o][|o]?(?:--|\.\.)[|o]?[|{o]")
_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)


class MermaidValidator(MermaidValidatorPort):
    """Validates Mermaid.js diagram syntax using pattern-based heuristics."""

    def validate(self, mermaid_code: str) -> tuple[bool, list[str]]:
        """Return ``(is_valid, error_messages)`` for the given Mermaid code."""
        errors: list[str] = []
        code = mermaid_code.strip()
        if not code:
            return False, ["Empty diagram code."]

        code = _FRONTMATTER_RE.sub("", code, count=1).strip()
        lines = [
            line.strip()
            for line in code.split("\n")
            if line.strip() and not line.strip().startswith("%%")
        ]
        if not lines:
            return False, ["Empty diagram code."]

        header = _HEADER_RE.match(lines[0])
        if not header:
            errors.append(f"Invalid diagram type on first line: '{lines[0]}'.")
        if len(lines) < 2:
            errors.append("Diagram appears to have no content (only type declaration).")

        diagram_type = header.group(0) if header else ""
        # Free text in sequence diagrams (notes, messages) may contain stray brackets.
        if diagram_type != "sequenceDiagram":
            errors.extend(self._check_brackets("\n".join(lines[1:]), diagram_type))

        return len(errors) == 0, errors

    @staticmethod
    def _check_brackets(body: str, diagram_type: str) -> list[str]:
        text = _QUOTED_RE.sub('""', body)
        if diagram_type == "erDiagram":
            text = _ER_OPERATOR_RE.sub(" -- ", text)

        pairs = {"(": ")", "[": "]", "{": "}"}
        closers = set(pairs.values())
        stack: list[str] = []
        for char in text:
            if char in pairs:
                stack.append(pairs[char])
            elif char in closers:
                if not stack or stack[-1] != char:
                    return [f"Unbalanced bracket: '{char}'"]
                stack.pop()
        if stack:
            return [f"Unclosed brackets detected. Expected: {''.join(reversed(stack))}"]
        return []
