"""
File Parser Adapter — concrete implementation of FileParserPort.

Handles PDF (via PyMuPDF), Markdown, DOCX (via python-docx, including tables)
and plain text. Parsing is CPU/IO bound and synchronous, so it runs in a worker
thread to keep the event loop responsive.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import docx  # python-docx
import fitz  # PyMuPDF
from charset_normalizer import from_bytes
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.domain.entities.srs_document import FileType
from app.domain.errors import DocumentError
from app.domain.ports.file_parser_port import FileParserPort


class FileParserAdapter(FileParserPort):
    """Adapter that extracts text content from PDF, DOCX, Markdown, and Text files."""

    EXTENSION_MAP: dict[str, FileType] = {
        ".pdf": FileType.PDF,
        ".md": FileType.MARKDOWN,
        ".markdown": FileType.MARKDOWN,
        ".txt": FileType.TEXT,
        ".text": FileType.TEXT,
        ".docx": FileType.DOCX,
    }

    def detect_file_type(self, filename: str) -> FileType:
        """Detect file type from extension."""
        ext = Path(filename).suffix.lower()
        if ext == ".doc":
            raise ValueError(
                "Legacy Word documents (.doc) are not supported. "
                "Please save your file as a newer .docx file or PDF and try again."
            )
        if ext not in self.EXTENSION_MAP:
            raise ValueError(
                f"Unsupported file type: '{ext}'. Supported: {list(self.EXTENSION_MAP.keys())}"
            )
        return self.EXTENSION_MAP[ext]

    async def parse(self, file_path: Path, file_type: FileType) -> str:
        """Extract text from the given file based on its type."""
        match file_type:
            case FileType.PDF:
                return await asyncio.to_thread(self._parse_pdf, file_path)
            case FileType.MARKDOWN | FileType.TEXT:
                return await asyncio.to_thread(self._parse_text, file_path)
            case FileType.DOCX:
                return await asyncio.to_thread(self._parse_docx, file_path)

    # ── Parsers (blocking) ──────────────────────────────────────────────────

    def _parse_pdf(self, file_path: Path) -> str:
        """Extract text from all pages of a PDF using PyMuPDF."""
        try:
            with fitz.open(str(file_path)) as doc:
                return "\n".join(page.get_text() for page in doc).strip()
        except Exception as exc:  # noqa: BLE001
            raise DocumentError(
                "Failed to read the PDF. Ensure it is a valid, unencrypted PDF."
            ) from exc

    def _parse_text(self, file_path: Path) -> str:
        """Read a plain-text/Markdown file, detecting its encoding."""
        raw = file_path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            return raw[3:].decode("utf-8", errors="replace").strip()
        try:
            return raw.decode("utf-8").strip()
        except UnicodeDecodeError:
            best = from_bytes(raw).best()
            if best is not None:
                return str(best).strip()
            return raw.decode("utf-8", errors="replace").strip()

    def _parse_docx(self, file_path: Path) -> str:
        """Extract paragraphs and tables (in document order) from a .docx file."""
        try:
            document = docx.Document(str(file_path))
        except Exception as exc:  # noqa: BLE001
            raise DocumentError(
                "Failed to read the Word document. Ensure it is a valid .docx file "
                "and not corrupted."
            ) from exc

        lines: list[str] = []
        for block in document.iter_inner_content():
            if isinstance(block, Paragraph):
                if block.text.strip():
                    lines.append(block.text)
            elif isinstance(block, Table):
                lines.extend(self._table_lines(block))
        return "\n".join(lines).strip()

    @staticmethod
    def _table_lines(table: Table) -> list[str]:
        lines: list[str] = []
        for row in table.rows:
            cells: list[str] = []
            previous = None
            for cell in row.cells:
                if cell._tc is previous:  # merged cells repeat the same element
                    continue
                previous = cell._tc
                cells.append(" ".join(cell.text.split()))
            if any(cells):
                lines.append(" | ".join(cells))
        return lines
