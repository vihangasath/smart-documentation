"""
Mermaid Validator — validates Mermaid.js syntax using heuristic checks.

For production, this could be extended to use a headless browser with
mermaid-cli, but the heuristic approach covers the common cases well
and keeps the backend dependency-light.
"""

from __future__ import annotations

import re


class MermaidValidator:
    """
    Validates Mermaid.js diagram syntax using pattern-based heuristics.

    Checks for:
    - Valid diagram type declaration
    - Balanced brackets and braces
    - Common syntax errors
    """

    VALID_DIAGRAM_TYPES = {
        "classDiagram",
        "sequenceDiagram",
        "erDiagram",
        "stateDiagram",
        "stateDiagram-v2",
        "flowchart",
        "graph",
        "architecture-beta",
        "pie",
        "gantt",
        "gitGraph",
        "mindmap",
        "timeline",
    }

    def validate(self, mermaid_code: str) -> tuple[bool, list[str]]:
        """
        Validate Mermaid syntax.

        Args:
            mermaid_code: Raw Mermaid code string.

        Returns:
            Tuple of (is_valid, list_of_error_messages).
        """
        errors: list[str] = []
        code = mermaid_code.strip()

        if not code:
            return False, ["Empty diagram code."]

        # Check diagram type declaration
        first_line = code.split("\n")[0].strip()
        diagram_type_found = False
        for dtype in self.VALID_DIAGRAM_TYPES:
            if first_line.startswith(dtype) or first_line.startswith(f"{dtype} "):
                diagram_type_found = True
                break
        # Also check for "graph TD", "graph LR", etc.
        if first_line.startswith("graph "):
            diagram_type_found = True

        if not diagram_type_found:
            errors.append(
                f"Invalid diagram type on first line: '{first_line}'. "
                f"Expected one of: {sorted(self.VALID_DIAGRAM_TYPES)}"
            )

        # Check balanced brackets
        bracket_pairs = {"(": ")", "[": "]", "{": "}"}
        stack: list[str] = []
        for char in code:
            if char in bracket_pairs:
                stack.append(bracket_pairs[char])
            elif char in bracket_pairs.values():
                if not stack or stack[-1] != char:
                    errors.append(f"Unbalanced bracket: '{char}'")
                    break
                stack.pop()
        if stack:
            errors.append(
                f"Unclosed brackets detected. Expected: {''.join(stack)}"
            )

        # Check for empty diagram body
        lines = [
            line.strip()
            for line in code.split("\n")
            if line.strip() and not line.strip().startswith("%%")
        ]
        if len(lines) < 2:
            errors.append("Diagram appears to have no content (only type declaration).")

        is_valid = len(errors) == 0
        return is_valid, errors
