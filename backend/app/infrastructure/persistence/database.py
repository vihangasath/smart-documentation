"""
Database — SQLAlchemy engine, table definitions and a threadpool helper.

SQLite is used for local development; set ``DATABASE_URL`` to a Postgres URL in
production. The SQL drivers are synchronous, so every call from async code goes
through :meth:`Database.run`, which executes it on a worker thread.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from sqlalchemy import (
    Column,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.engine import Connection, Engine

T = TypeVar("T")

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(100), nullable=False),
    Column("email", String(320), nullable=False, unique=True),
    Column("hashed_password", String(255), nullable=False),
    Column("token_version", Integer, nullable=False, default=0),
    Column("created_at", String(40), nullable=False),
)

documents_table = Table(
    "documents",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("owner_id", String(36), nullable=False),
    Column("filename", String(512), nullable=False),
    Column("file_type", String(20), nullable=False),
    Column("content", Text, nullable=False, default=""),
    Column("file_path", String(1024), nullable=True),
    Column("uploaded_at", String(40), nullable=False),
    Index("ix_documents_owner_id", "owner_id"),
    Index("ix_documents_uploaded_at", "uploaded_at"),
)

results_table = Table(
    "results",
    metadata,
    Column("document_id", String(36), primary_key=True),
    Column("schema_json", Text, nullable=True),
    Column("diagrams_json", Text, nullable=True),
    Column("scaffold_json", Text, nullable=True),
)

jobs_table = Table(
    "jobs",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("document_id", String(36), nullable=False),
    Column("owner_id", String(36), nullable=False),
    Column("status", String(20), nullable=False),
    Column("errors_json", Text, nullable=False, default="[]"),
    Column("instructions", Text, nullable=False, default=""),
    Column("created_at", String(40), nullable=False),
    Column("finished_at", String(40), nullable=True),
    Index("ix_jobs_owner_status", "owner_id", "status"),
    Index("ix_jobs_document_id", "document_id"),
)


class Database:
    """Owns the SQLAlchemy engine and creates the schema on demand."""

    def __init__(self, url: str) -> None:
        kwargs: dict = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            # Make sure the parent directory of a file database exists.
            path = url.split("///", 1)[-1]
            if path and path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(url, **kwargs)

    def create_all(self) -> None:
        metadata.create_all(self.engine)

    async def run(self, fn: Callable[[Connection], T]) -> T:
        """Run ``fn(connection)`` in a transaction on a worker thread."""

        def _call() -> T:
            with self.engine.begin() as conn:
                return fn(conn)

        return await asyncio.to_thread(_call)

    def dispose(self) -> None:
        self.engine.dispose()
