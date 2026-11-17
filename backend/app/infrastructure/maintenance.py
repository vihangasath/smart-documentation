"""Periodic housekeeping: delete expired files and old database records."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.domain.ports.document_repository_port import DocumentRepositoryPort

logger = logging.getLogger(__name__)


def _delete_old_files(directory: Path, max_age_seconds: float) -> int:
    if not directory.is_dir():
        return 0
    cutoff = time.time() - max_age_seconds
    removed = 0
    for path in directory.iterdir():
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
                removed += 1
        except OSError:
            logger.warning("Could not remove expired file %s", path)
    return removed


async def run_cleanup(
    uploads_dir: Path,
    outputs_dir: Path,
    documents: DocumentRepositoryPort,
    file_retention_hours: int,
    data_retention_days: int,
) -> None:
    """
    Remove uploads/ZIPs older than the file retention window, and documents
    (with their results and jobs) older than the data retention window.

    This is the retention policy, not agent behaviour: agents themselves never
    delete a user's SRS file.
    """
    max_age = file_retention_hours * 3600
    files = await asyncio.to_thread(_delete_old_files, uploads_dir, max_age)
    files += await asyncio.to_thread(_delete_old_files, outputs_dir, max_age)
    cutoff = datetime.now(UTC) - timedelta(days=data_retention_days)
    records = await documents.delete_older_than(cutoff.isoformat())
    if files or records:
        logger.info("Cleanup removed %d files and %d documents", files, records)
