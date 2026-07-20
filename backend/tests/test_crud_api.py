"""End-to-end tests for the versioned persistence API."""

import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.database.models import Analysis, CandidateProfile, Job, User
from backend.app.infrastructure.database.session import create_session_factory, get_db_session
from backend.app.main import app


@pytest.fixture
def api_database(tmp_path: Path) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(f"sqlite+pysqlite:///{(tmp_path / 'api.db').as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

    def override_session() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    try:
        with TestClient(app) as client:
            yield client, session_factory
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_profile_create_read_patch_and_conflict(api_database) -> None:
    client, _ = api_database

    assert client.get("/api/v1/profiles/me").status_code == 404

    created = client.post(
        "/api/v1/profiles",
        json={
            "name": " Candidate ",
            "target_role": "Backend Engineer",
            "summary": "API builder",
            "skills": ["Python", "FastAPI"],
        },
    )
    assert created.status_code == 201
    profile_id = created.json()["id"]
    assert created.json()["name"] == "Candidate"

    fetched = client.get("/api/v1/profiles/me")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == profile_id

    patched = client.patch(
        "/api/v1/profiles/me",
        json={"target_role": "Platform Engineer", "skills": ["Python", "SQL"]},
    )
    assert patched.status_code == 200
    assert patched.json()["target_role"] == "Platform Engineer"
    assert patched.json()["summary"] == "API builder"
    assert patched.json()["skills"] == ["Python", "SQL"]

    duplicate = client.post(
        "/api/v1/profiles",
        json={"name": "Duplicate", "skills": []},
    )
    assert duplicate.status_code == 409


def test_job_create_list_get_and_user_isolation(api_database) -> None:
    client, _ = api_database
    headers = {"X-User-Email": "owner@example.test"}

    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "title": " Backend Engineer ",
            "company": "Example Co",
            "description": "Build reliable APIs",
            "source_url": "https://example.test/jobs/1",
        },
    )
    assert created.status_code == 201
    job_id = created.json()["id"]
    assert created.json()["title"] == "Backend Engineer"
    assert created.json()["source_type"] == "manual"

    listed = client.get("/api/v1/jobs", headers=headers)
    assert listed.status_code == 200
    assert [job["id"] for job in listed.json()] == [job_id]

    fetched = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["description"] == "Build reliable APIs"

    other_headers = {"X-User-Email": "other@example.test"}
    assert client.get(f"/api/v1/jobs/{job_id}", headers=other_headers).status_code == 404
    assert client.get("/api/v1/jobs", headers=other_headers).json() == []


def test_analysis_create_list_and_relationship_validation(api_database) -> None:
    client, _ = api_database
    profile = client.post(
        "/api/v1/profiles",
        json={"name": "Candidate", "skills": ["Python"]},
    ).json()
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Engineer", "description": "Build APIs"},
    ).json()
    payload = {
        "job_id": job["id"],
        "candidate_profile_id": profile["id"],
        "status": "completed",
        "score": 91,
        "result_json": {"summary": "strong match"},
        "scoring_version": "v1",
        "model_provider": "deepseek",
        "model_name": "deepseek-chat",
    }

    created = client.post("/api/v1/analyses", json=payload)
    assert created.status_code == 201
    analysis_id = created.json()["id"]
    assert created.json()["score"] == 91

    listed = client.get("/api/v1/analyses")
    assert listed.status_code == 200
    assert [analysis["id"] for analysis in listed.json()] == [analysis_id]

    foreign_attempt = client.post(
        "/api/v1/analyses",
        headers={"X-User-Email": "other@example.test"},
        json=payload,
    )
    assert foreign_attempt.status_code == 404


def test_api_writes_are_persisted_in_new_database_session(api_database) -> None:
    client, session_factory = api_database
    profile = client.post(
        "/api/v1/profiles",
        json={"name": "Persistent Candidate", "skills": ["SQLAlchemy"]},
    ).json()
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Persistent Job", "description": "Stored in SQLite"},
    ).json()
    analysis = client.post(
        "/api/v1/analyses",
        json={
            "job_id": job["id"],
            "candidate_profile_id": profile["id"],
            "status": "completed",
            "score": 84,
            "result_json": {"persisted": True},
        },
    ).json()

    with session_factory() as verification_session:
        assert verification_session.scalar(select(func.count()).select_from(User)) == 1
        assert verification_session.scalar(select(func.count()).select_from(CandidateProfile)) == 1
        assert verification_session.scalar(select(func.count()).select_from(Job)) == 1
        assert verification_session.scalar(select(func.count()).select_from(Analysis)) == 1
        stored = verification_session.get(Analysis, uuid.UUID(analysis["id"]))
        assert stored is not None
        assert stored.result_json == {"persisted": True}
        assert stored.job.title == "Persistent Job"
