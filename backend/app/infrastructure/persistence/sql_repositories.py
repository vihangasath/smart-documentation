"""SQL implementations of the user, document, result and job ports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.exc import IntegrityError

from app.domain.entities.diagram import DiagramSet
from app.domain.entities.extracted_schema import ExtractedSchema
from app.domain.entities.job import Job, JobStatus
from app.domain.entities.project_scaffold import ProjectScaffold
from app.domain.entities.srs_document import FileType, SRSDocument
from app.domain.entities.user import User
from app.domain.errors import AuthError
from app.domain.ports.document_repository_port import DocumentRepositoryPort
from app.domain.ports.job_repository_port import JobRepositoryPort
from app.domain.ports.result_repository_port import ResultRepositoryPort
from app.domain.ports.user_store_port import UserStorePort
from app.infrastructure.persistence.database import (
    Database,
    documents_table,
    jobs_table,
    results_table,
    users_table,
)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


# ─── Users ──────────────────────────────────────────────────────────────────


class SqlUserStore(UserStorePort):
    def __init__(self, db: Database) -> None:
        self._db = db

    @staticmethod
    def _to_entity(row) -> User:
        return User(
            id=row.id,
            name=row.name,
            email=row.email,
            hashed_password=row.hashed_password,
            token_version=row.token_version,
            created_at=_dt(row.created_at),
        )

    async def save(self, user: User) -> None:
        values = {
            "name": user.name,
            "email": user.email.lower(),
            "hashed_password": user.hashed_password,
            "token_version": user.token_version,
        }

        def _save(conn) -> None:
            exists = conn.execute(
                select(users_table.c.id).where(users_table.c.id == user.id)
            ).first()
            if exists:
                conn.execute(
                    update(users_table)
                    .where(users_table.c.id == user.id)
                    .values(**values)
                )
            else:
                conn.execute(
                    insert(users_table).values(
                        id=user.id, created_at=_iso(user.created_at), **values
                    )
                )

        try:
            await self._db.run(_save)
        except IntegrityError as exc:  # unique(email) lost a race
            raise AuthError("An account with this email already exists.") from exc

    async def find_by_email(self, email: str) -> User | None:
        row = await self._db.run(
            lambda c: c.execute(
                select(users_table).where(users_table.c.email == email.lower())
            ).first()
        )
        return self._to_entity(row) if row else None

    async def find_by_id(self, user_id: str) -> User | None:
        row = await self._db.run(
            lambda c: c.execute(
                select(users_table).where(users_table.c.id == user_id)
            ).first()
        )
        return self._to_entity(row) if row else None

    async def email_exists(self, email: str) -> bool:
        row = await self._db.run(
            lambda c: c.execute(
                select(users_table.c.id).where(users_table.c.email == email.lower())
            ).first()
        )
        return row is not None


# ─── Documents ──────────────────────────────────────────────────────────────


class SqlDocumentRepository(DocumentRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def save(self, document: SRSDocument, file_path: Path | None) -> None:
        values = {
            "owner_id": document.owner_id,
            "filename": document.filename,
            "file_type": document.file_type.value,
            "content": document.content,
            "file_path": str(file_path) if file_path else None,
        }

        def _save(conn) -> None:
            exists = conn.execute(
                select(documents_table.c.id).where(documents_table.c.id == document.id)
            ).first()
            if exists:
                conn.execute(
                    update(documents_table)
                    .where(documents_table.c.id == document.id)
                    .values(**values)
                )
            else:
                conn.execute(
                    insert(documents_table).values(
                        id=document.id,
                        uploaded_at=_iso(document.uploaded_at),
                        **values,
                    )
                )

        await self._db.run(_save)

    async def get(self, document_id: str) -> tuple[SRSDocument, Path | None] | None:
        row = await self._db.run(
            lambda c: c.execute(
                select(documents_table).where(documents_table.c.id == document_id)
            ).first()
        )
        if not row:
            return None
        document = SRSDocument(
            id=row.id,
            owner_id=row.owner_id,
            filename=row.filename,
            file_type=FileType(row.file_type),
            content=row.content,
            uploaded_at=_dt(row.uploaded_at),
        )
        return document, Path(row.file_path) if row.file_path else None

    async def delete_older_than(self, cutoff_iso: str) -> int:
        def _delete(conn) -> int:
            ids = [
                r.id
                for r in conn.execute(
                    select(documents_table.c.id).where(
                        documents_table.c.uploaded_at < cutoff_iso
                    )
                )
            ]
            if not ids:
                return 0
            conn.execute(
                delete(results_table).where(results_table.c.document_id.in_(ids))
            )
            conn.execute(delete(jobs_table).where(jobs_table.c.document_id.in_(ids)))
            conn.execute(delete(documents_table).where(documents_table.c.id.in_(ids)))
            return len(ids)

        return await self._db.run(_delete)


# ─── Results ────────────────────────────────────────────────────────────────


class SqlResultRepository(ResultRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def _put(self, document_id: str, column: str, payload: str) -> None:
        def _save(conn) -> None:
            exists = conn.execute(
                select(results_table.c.document_id).where(
                    results_table.c.document_id == document_id
                )
            ).first()
            if exists:
                conn.execute(
                    update(results_table)
                    .where(results_table.c.document_id == document_id)
                    .values(**{column: payload})
                )
            else:
                conn.execute(
                    insert(results_table).values(
                        document_id=document_id, **{column: payload}
                    )
                )

        await self._db.run(_save)

    async def _get(self, document_id: str, column: str) -> str | None:
        row = await self._db.run(
            lambda c: c.execute(
                select(results_table.c[column]).where(
                    results_table.c.document_id == document_id
                )
            ).first()
        )
        return row[0] if row else None

    async def save_schema(self, schema: ExtractedSchema) -> None:
        await self._put(schema.document_id, "schema_json", schema.model_dump_json())

    async def get_schema(self, document_id: str) -> ExtractedSchema | None:
        raw = await self._get(document_id, "schema_json")
        return ExtractedSchema.model_validate_json(raw) if raw else None

    async def save_diagrams(self, diagrams: DiagramSet) -> None:
        await self._put(
            diagrams.document_id, "diagrams_json", diagrams.model_dump_json()
        )

    async def get_diagrams(self, document_id: str) -> DiagramSet | None:
        raw = await self._get(document_id, "diagrams_json")
        return DiagramSet.model_validate_json(raw) if raw else None

    async def save_scaffold(self, scaffold: ProjectScaffold) -> None:
        await self._put(
            scaffold.document_id, "scaffold_json", scaffold.model_dump_json()
        )

    async def get_scaffold(self, document_id: str) -> ProjectScaffold | None:
        raw = await self._get(document_id, "scaffold_json")
        return ProjectScaffold.model_validate_json(raw) if raw else None

    async def clear(self, document_id: str) -> None:
        await self._db.run(
            lambda c: c.execute(
                delete(results_table).where(results_table.c.document_id == document_id)
            )
        )


# ─── Jobs ───────────────────────────────────────────────────────────────────


class SqlJobRepository(JobRepositoryPort):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def save(self, job: Job) -> None:
        values = {
            "document_id": job.document_id,
            "owner_id": job.owner_id,
            "status": job.status.value,
            "errors_json": json.dumps(job.errors),
            "instructions": job.instructions,
            "finished_at": _iso(job.finished_at),
        }

        def _save(conn) -> None:
            exists = conn.execute(
                select(jobs_table.c.id).where(jobs_table.c.id == job.id)
            ).first()
            if exists:
                conn.execute(
                    update(jobs_table).where(jobs_table.c.id == job.id).values(**values)
                )
            else:
                conn.execute(
                    insert(jobs_table).values(
                        id=job.id, created_at=_iso(job.created_at), **values
                    )
                )

        await self._db.run(_save)

    async def get(self, job_id: str) -> Job | None:
        row = await self._db.run(
            lambda c: c.execute(
                select(jobs_table).where(jobs_table.c.id == job_id)
            ).first()
        )
        if not row:
            return None
        return Job(
            id=row.id,
            document_id=row.document_id,
            owner_id=row.owner_id,
            status=JobStatus(row.status),
            errors=json.loads(row.errors_json or "[]"),
            instructions=row.instructions,
            created_at=_dt(row.created_at),
            finished_at=_dt(row.finished_at),
        )

    async def count_active_for_owner(self, owner_id: str) -> int:
        return await self._db.run(
            lambda c: c.execute(
                select(func.count())
                .select_from(jobs_table)
                .where(
                    jobs_table.c.owner_id == owner_id,
                    jobs_table.c.status.in_(
                        [JobStatus.QUEUED.value, JobStatus.RUNNING.value]
                    ),
                )
            ).scalar_one()
        )

    async def fail_stale_jobs(self) -> int:
        def _fail(conn) -> int:
            result = conn.execute(
                update(jobs_table)
                .where(
                    jobs_table.c.status.in_(
                        [JobStatus.QUEUED.value, JobStatus.RUNNING.value]
                    )
                )
                .values(
                    status=JobStatus.FAILED.value,
                    errors_json=json.dumps(
                        ["The server restarted while this run was in progress."]
                    ),
                )
            )
            return result.rowcount

        return await self._db.run(_fail)
