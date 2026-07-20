"""API and persistence tests for the saved-job analysis workflow."""

import json
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.application.analysis_service import AnalysisService
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.database.models import Analysis
from backend.app.infrastructure.database.session import create_session_factory, get_db_session
from backend.app.infrastructure.llm.parser import ExtractedAnalysis, build_final_analysis
from backend.app.infrastructure.llm.provider import LLMServiceError
from backend.app.main import app


@pytest.fixture
def workflow_database(
    tmp_path: Path,
) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine(f"sqlite+pysqlite:///{(tmp_path / 'workflow.db').as_posix()}")
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


def _create_profile_and_job(client: TestClient) -> tuple[dict, dict]:
    profile = client.post(
        "/api/v1/profiles",
        json={
            "name": "Candidate",
            "target_role": "Backend Engineer",
            "summary": "Built production APIs",
            "skills": ["Python", "FastAPI"],
        },
    ).json()
    job = client.post(
        "/api/v1/jobs",
        json={
            "title": "Backend Engineer",
            "description": "Requires Python, FastAPI and Redis",
        },
    ).json()
    return profile, job


def _completed_result():
    return build_final_analysis(
        ExtractedAnalysis.model_validate(
            {
                "job_requirements": {
                    "core_skills": ["Python", "FastAPI", "Redis"],
                    "preferred_skills": [],
                    "project_requirements": [],
                    "education_requirements": [],
                    "experience_requirements": [],
                },
                "matched_skills": ["Python", "FastAPI"],
                "missing_skills": ["Redis"],
                "reasoning": ["Python and FastAPI have direct profile evidence"],
                "greeting": "分析已完成。",
                "confidence": 0.9,
            }
        )
    )


def test_analyze_saved_job_calls_existing_service_and_returns_completed(
    workflow_database,
    monkeypatch,
) -> None:
    client, _ = workflow_database
    profile, job = _create_profile_and_job(client)
    captured: dict[str, str] = {}

    def fake_analyze(self, job_title, job_description, candidate_profile):
        captured.update(
            title=job_title,
            description=job_description,
            profile=candidate_profile,
        )
        return _completed_result()

    monkeypatch.setattr(AnalysisService, "analyze_job", fake_analyze)
    response = client.post(f"/api/v1/jobs/{job['id']}/analyze")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["score"] == 67
    assert payload["job_id"] == job["id"]
    assert payload["candidate_profile_id"] == profile["id"]
    assert payload["result_json"]["missing_skills"] == ["Redis"]
    assert captured["title"] == "Backend Engineer"
    assert captured["description"] == "Requires Python, FastAPI and Redis"
    assert json.loads(captured["profile"])["skills"] == ["Python", "FastAPI"]


def test_completed_analysis_is_persisted_in_a_new_session(
    workflow_database,
    monkeypatch,
) -> None:
    client, session_factory = workflow_database
    profile, job = _create_profile_and_job(client)
    monkeypatch.setattr(AnalysisService, "analyze_job", lambda *args: _completed_result())

    analysis_id = client.post(f"/api/v1/jobs/{job['id']}/analyze").json()["id"]

    with session_factory() as session:
        stored = session.get(Analysis, uuid.UUID(analysis_id))
        assert stored is not None
        assert stored.status == "completed"
        assert stored.score == 67
        assert stored.candidate_profile_id == uuid.UUID(profile["id"])
        assert stored.result_json["reasoning"] == [
            "Python and FastAPI have direct profile evidence"
        ]
        assert stored.scoring_version == "deterministic-v1"


def test_failed_analysis_is_persisted_and_error_is_returned(
    workflow_database,
    monkeypatch,
) -> None:
    client, session_factory = workflow_database
    _, job = _create_profile_and_job(client)

    def fail_analysis(*args):
        raise LLMServiceError("AI service unavailable", status_code=502)

    monkeypatch.setattr(AnalysisService, "analyze_job", fail_analysis)
    response = client.post(f"/api/v1/jobs/{job['id']}/analyze")

    assert response.status_code == 502
    assert response.json() == {"detail": "AI service unavailable"}
    with session_factory() as session:
        stored = session.scalar(select(Analysis))
        assert stored is not None
        assert stored.status == "failed"
        assert stored.score is None
        assert stored.result_json == {"error": "AI service unavailable"}


def test_analyze_requires_owned_job_and_profile(workflow_database, monkeypatch) -> None:
    client, _ = workflow_database
    _, job = _create_profile_and_job(client)
    called = False

    def fake_analyze(*args):
        nonlocal called
        called = True
        return _completed_result()

    monkeypatch.setattr(AnalysisService, "analyze_job", fake_analyze)
    response = client.post(
        f"/api/v1/jobs/{job['id']}/analyze",
        headers={"X-User-Email": "other@example.test"},
    )

    assert response.status_code == 404
    assert called is False
