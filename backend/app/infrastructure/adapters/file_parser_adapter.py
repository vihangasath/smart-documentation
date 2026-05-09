"""
File Parser Adapter — concrete implementation of FileParserPort.

Handles PDF (via PyMuPDF), Markdown (via markdown-it-py), DOCX (via python-docx),
and plain text parsing.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
import docx  # python-docx
from markdown_it import MarkdownIt

from app.domain.entities.srs_document import FileType
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
                f"Unsupported file type: '{ext}'. "
                f"Supported: {list(self.EXTENSION_MAP.keys())}"
            )
        return self.EXTENSION_MAP[ext]

    async def parse(self, file_path: Path, file_type: FileType) -> str:
        """
        Extract text from the given file based on its type.

        Args:
            file_path: Path to the file on disk.
            file_type: The detected file format.

        Returns:
            Extracted text content.
        """
        match file_type:
            case FileType.PDF:
                return self._parse_pdf(file_path)
            case FileType.MARKDOWN:
                return self._parse_markdown(file_path)
            case FileType.TEXT:
                return self._parse_text(file_path)
            case FileType.DOCX:
                return self._parse_docx(file_path)

    def _parse_pdf(self, file_path: Path) -> str:
        """Extract text from all pages of a PDF using PyMuPDF."""
        text_parts: list[str] = []
        with fitz.open(str(file_path)) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts).strip()

    def _parse_markdown(self, file_path: Path) -> str:
        """
        Parse Markdown and return the raw text content.

        We read the raw Markdown source since the LLM benefits from
        seeing the structural formatting (headings, lists, etc.).
        """
        return file_path.read_text(encoding="utf-8").strip()

    def _parse_text(self, file_path: Path) -> str:
        """Read plain text file."""
        return file_path.read_text(encoding="utf-8").strip()

    def _parse_docx(self, file_path: Path) -> str:
        """
        Extract text from a Word document using python-docx.

        Iterates through all paragraphs and joins them with newlines.
        Preserves paragraph structure for better LLM comprehension.
        """
        try:
            document = docx.Document(str(file_path))
        except Exception as e:
            raise ValueError(
                f"Failed to read the Word document. Ensure it is a valid .docx file and not corrupted. "
                f"Original error: {str(e)}"
            )

        paragraphs: list[str] = [
            para.text for para in document.paragraphs if para.text.strip()
        ]
        return "\n".join(paragraphs).strip()
