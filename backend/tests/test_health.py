"""Smoke tests for the FastAPI application."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_root_reports_running() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_is_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
