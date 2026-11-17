"""End-to-end API tests using the fake LLM and a temp SQLite database."""

from __future__ import annotations

import io
import time
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.api.dependencies import build_container
from app.main import create_app

from .conftest import make_settings

TEXT = (
    "The library lets members borrow books. Each loan has a due date and a member. " * 3
)


def signup(client: TestClient, email="a@example.com") -> dict[str, str]:
    r = client.post(
        "/api/auth/signup",
        json={"name": "A", "email": email, "password": "password123"},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def text_doc(client, headers, content=TEXT) -> str:
    r = client.post("/api/documents/text", json={"content": content}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["document_id"]


def wait_for_job(client, headers, job_id, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/api/jobs/{job_id}", headers=headers)
        assert r.status_code == 200, r.text
        if r.json()["status"] in ("completed", "failed"):
            return r.json()
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def run_pipeline(client, headers, doc_id, instructions=""):
    r = client.post(
        "/api/analyze/full",
        json={"document_id": doc_id, "instructions": instructions},
        headers=headers,
    )
    assert r.status_code == 202, r.text
    return wait_for_job(client, headers, r.json()["job_id"])


# ─── Authentication & ownership ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/api/upload"),
        ("post", "/api/documents/text"),
        ("post", "/api/analyze"),
        ("post", "/api/analyze/full"),
        ("get", "/api/jobs/x"),
        ("get", "/api/diagrams/x"),
        ("post", "/api/diagrams/x"),
        ("get", "/api/scaffold/x"),
        ("get", "/api/scaffold/x/download"),
        ("get", "/api/events/x"),
        ("get", "/api/auth/me"),
    ],
)
def test_endpoints_require_a_token(client, method, path):
    assert getattr(client, method)(path).status_code == 401
    bad = {"Authorization": "Bearer nope"}
    assert getattr(client, method)(path, headers=bad).status_code == 401


def test_health_is_public(client):
    assert client.get("/health").json()["status"] == "healthy"


def test_user_cannot_see_another_users_document(client):
    owner, intruder = signup(client, "a@example.com"), signup(client, "b@example.com")
    doc_id = text_doc(client, owner)
    run_pipeline(client, owner, doc_id)

    for path in (
        f"/api/diagrams/{doc_id}",
        f"/api/scaffold/{doc_id}",
        f"/api/scaffold/{doc_id}/download",
        f"/api/events/{doc_id}",
    ):
        assert client.get(path, headers=intruder).status_code == 404, path
    assert (
        client.post(
            "/api/analyze/full", json={"document_id": doc_id}, headers=intruder
        ).status_code
        == 404
    )

    job_id = client.post(
        "/api/analyze/full", json={"document_id": doc_id}, headers=owner
    ).json()["job_id"]
    assert client.get(f"/api/jobs/{job_id}", headers=intruder).status_code == 404
    wait_for_job(client, owner, job_id)


# ─── Auth endpoints ─────────────────────────────────────────────────────────


def test_signup_validation_and_duplicates(client):
    bad = [
        {"name": "A", "email": "not-an-email", "password": "password123"},
        {"name": "A", "email": "a@example.com", "password": "short"},
        {"name": "A", "email": "a@example.com", "password": "x" * 73},
        {"name": " ", "email": "a@example.com", "password": "password123"},
    ]
    for body in bad:
        assert client.post("/api/auth/signup", json=body).status_code == 422, body

    signup(client)
    dup = client.post(
        "/api/auth/signup",
        json={"name": "A", "email": "A@Example.com", "password": "password123"},
    )
    assert dup.status_code == 409


def test_login_me_and_logout_all(client):
    headers = signup(client)
    assert (
        client.get("/api/auth/me", headers=headers).json()["email"] == "a@example.com"
    )

    assert (
        client.post(
            "/api/auth/login", json={"email": "a@example.com", "password": "bad"}
        ).status_code
        == 401
    )
    ok = client.post(
        "/api/auth/login", json={"email": "A@example.com", "password": "password123"}
    )
    assert ok.status_code == 200

    assert client.post("/api/auth/logout-all", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_auth_endpoints_are_rate_limited(tmp_path, fake_llm):
    container = build_container(
        make_settings(tmp_path, auth_rate_limit_per_minute=3), llm=fake_llm
    )
    with TestClient(create_app(container)) as c:
        codes = [
            c.post(
                "/api/auth/login", json={"email": "x@example.com", "password": "p"}
            ).status_code
            for _ in range(5)
        ]
    assert codes == [401, 401, 401, 429, 429]


# ─── Documents ──────────────────────────────────────────────────────────────


def test_text_document_too_short_is_rejected(client):
    r = client.post(
        "/api/documents/text", json={"content": "tiny"}, headers=signup(client)
    )
    assert r.status_code == 422


def test_upload_txt_with_non_utf8_bytes_and_hostile_filename(client, container):
    headers = signup(client)
    content = ("Café requirements: users borrow books and pay late fees. " * 3).encode(
        "cp1252"
    )
    r = client.post(
        "/api/upload",
        files={"file": ("../../evil name.txt", io.BytesIO(content), "text/plain")},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["filename"] == "evil-name.txt"
    saved = list(container.settings.uploads_dir.iterdir())
    assert len(saved) == 1 and saved[0].parent == container.settings.uploads_dir
    assert saved[0].suffix == ".txt" and "evil" not in saved[0].name


def test_upload_rejects_bad_type_empty_and_oversized(tmp_path, fake_llm):
    container = build_container(
        make_settings(tmp_path, max_upload_size_mb=1), llm=fake_llm
    )
    with TestClient(create_app(container)) as c:
        h = signup(c)
        up = lambda name, data: c.post(  # noqa: E731
            "/api/upload",
            files={"file": (name, io.BytesIO(data), "application/octet-stream")},
            headers=h,
        )
        assert up("x.exe", b"abc").status_code == 400
        assert up("x.doc", b"abc").status_code == 400
        assert up("x.txt", b"   ").status_code == 422  # no readable text
        assert up("x.txt", b"a" * (1024 * 1024 + 10)).status_code == 413
        assert (
            list(container.settings.uploads_dir.iterdir()) == []
        )  # nothing left behind


# ─── Pipeline ───────────────────────────────────────────────────────────────


def test_full_pipeline_end_to_end(client, container):
    headers = signup(client)
    doc_id = text_doc(client, headers)
    job = run_pipeline(client, headers, doc_id, instructions="Focus on loans")

    assert job["status"] == "completed" and job["success"] is True, job["errors"]
    assert job["analysis"]["entity_count"] == 2
    types = {d["diagram_type"]: d for d in job["diagrams"]["diagrams"]}
    assert set(types) == {"er", "class", "sequence", "architecture"}
    assert all(d["is_valid"] for d in types.values()), {
        k: v["validation_errors"] for k, v in types.items()
    }
    assert job["scaffold"]["file_count"] == 6

    r = client.get(f"/api/scaffold/{doc_id}/download", headers=headers)
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    names = zipfile.ZipFile(io.BytesIO(r.content)).namelist()
    assert "Library-System/main.py" in names

    assert (
        len(client.get(f"/api/scaffold/{doc_id}", headers=headers).json()["files"]) == 6
    )
    assert client.get(f"/api/diagrams/{doc_id}", headers=headers).status_code == 200


def test_zips_do_not_collide_between_documents(client, container):
    headers = signup(client)
    ids = [text_doc(client, headers) for _ in range(2)]
    for doc_id in ids:
        run_pipeline(client, headers, doc_id)
    assert len(list(container.settings.outputs_dir.glob("*.zip"))) == 2


def test_instructions_reach_the_parser_prompt(client, fake_llm, container):
    seen: list[str] = []
    original = fake_llm.generate

    async def spy(prompt, *a, **kw):
        seen.append(prompt)
        return await original(prompt, *a, **kw)

    fake_llm.generate = spy
    headers = signup(client)
    run_pipeline(
        client, headers, text_doc(client, headers), instructions="USE-GRAPHQL-PLEASE"
    )
    assert any("USE-GRAPHQL-PLEASE" in p for p in seen)


def test_reads_do_not_trigger_llm_calls(client, fake_llm):
    headers = signup(client)
    doc_id = text_doc(client, headers)
    assert client.get(f"/api/diagrams/{doc_id}", headers=headers).status_code == 404
    assert client.get(f"/api/scaffold/{doc_id}", headers=headers).status_code == 404
    assert fake_llm.calls == []
    # POST needs an analysis first
    assert client.post(f"/api/diagrams/{doc_id}", headers=headers).status_code == 409


def test_partial_failure_still_returns_results_with_errors(client, fake_llm):
    fake_llm.fail_for.add("ONE file")  # scaffolder fails
    headers = signup(client)
    job = run_pipeline(client, headers, text_doc(client, headers))

    assert job["status"] == "completed" and job["success"] is False
    assert job["analysis"] and job["diagrams"] and job["scaffold"] is None
    assert any("ScaffolderAgent" in e for e in job["errors"])


def test_unreadable_llm_output_fails_the_job_cleanly(client, fake_llm):
    fake_llm.overrides["Requirements Analyst"] = "I cannot help with that."
    headers = signup(client)
    job = run_pipeline(client, headers, text_doc(client, headers))

    assert job["status"] == "failed" and job["analysis"] is None
    assert job["errors"] and all("Traceback" not in e for e in job["errors"])


def test_parser_internal_errors_are_not_leaked(client, fake_llm):
    async def boom(*a, **k):
        raise RuntimeError("secret internal path /srv/keys")

    fake_llm.generate = boom
    headers = signup(client)
    job = run_pipeline(client, headers, text_doc(client, headers))
    assert job["status"] == "failed"
    assert "secret" not in " ".join(job["errors"])


def test_concurrent_job_cap(tmp_path, fake_llm):
    import asyncio

    release = asyncio.Event()
    original = fake_llm.generate

    async def slow(*a, **k):
        await release.wait()
        return await original(*a, **k)

    fake_llm.generate = slow
    container = build_container(
        make_settings(tmp_path, max_active_jobs_per_user=1), llm=fake_llm
    )
    with TestClient(create_app(container)) as c:
        h = signup(c)
        a, b = text_doc(c, h), text_doc(c, h)
        first = c.post("/api/analyze/full", json={"document_id": a}, headers=h)
        assert first.status_code == 202
        second = c.post("/api/analyze/full", json={"document_id": b}, headers=h)
        assert second.status_code == 429
        c.portal.call(release.set)
        wait_for_job(c, h, first.json()["job_id"])


def test_sse_stream_is_scoped_replays_and_terminates(client):
    owner, other = signup(client, "a@example.com"), signup(client, "b@example.com")
    doc_id, other_doc = text_doc(client, owner), text_doc(client, other)
    run_pipeline(client, owner, doc_id)
    run_pipeline(client, other, other_doc)

    with client.stream("GET", f"/api/events/{doc_id}", headers=owner) as r:
        assert r.status_code == 200
        body = "".join(r.iter_text())

    assert "event: pipeline_start" in body and "event: pipeline_complete" in body
    assert doc_id in body and other_doc not in body


def test_stale_jobs_are_failed_on_startup(tmp_path, fake_llm):
    import asyncio

    from app.domain.entities.job import Job

    container = build_container(make_settings(tmp_path), llm=fake_llm)
    stale = Job(document_id="d", owner_id="o")
    asyncio.run(container.jobs.save(stale))
    with TestClient(create_app(container)):
        pass
    reloaded = asyncio.run(
        build_container(make_settings(tmp_path), llm=fake_llm).jobs.get(stale.id)
    )
    assert reloaded.status.value == "failed"


def test_request_id_header_and_generic_500(client, container):
    assert (
        client.get("/health", headers={"X-Request-ID": "abc"}).headers["x-request-id"]
        == "abc"
    )
    assert client.get("/health").headers["x-request-id"]


def test_data_survives_restart(tmp_path, fake_llm):
    settings = make_settings(tmp_path)
    with TestClient(create_app(build_container(settings, llm=fake_llm))) as c:
        h = signup(c)
        doc_id = text_doc(c, h)
        job = run_pipeline(c, h, doc_id)

    with TestClient(create_app(build_container(settings, llm=fake_llm))) as c2:
        assert c2.get("/api/auth/me", headers=h).status_code == 200
        again = c2.get(f"/api/jobs/{job['job_id']}", headers=h).json()
        assert again["status"] == "completed" and again["analysis"]["entity_count"] == 2
