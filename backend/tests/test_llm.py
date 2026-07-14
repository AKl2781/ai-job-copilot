"""Tests for LLM response parsing and analysis API errors."""

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.services import llm

client = TestClient(main.app)

VALID_ANALYSIS = {
    "score": 85,
    "summary": "技能与岗位要求较匹配。",
    "matched_skills": ["Python", "FastAPI"],
    "missing_skills": ["云平台经验"],
    "learning_plan": ["完成一个云部署练习"],
    "reasoning": ["后端技术栈与岗位描述一致"],
    "greeting": "你好，我有相关后端开发经验，希望进一步了解这个岗位。",
    "confidence": 0.91,
}


def test_parse_valid_json() -> None:
    analysis = llm._parse_analysis(json.dumps(VALID_ANALYSIS, ensure_ascii=False))

    assert analysis.score == 85
    assert analysis.greeting == VALID_ANALYSIS["greeting"]


def test_extract_json_from_surrounding_text() -> None:
    content = f"model output:\n{json.dumps(VALID_ANALYSIS, ensure_ascii=False)}\nend"

    assert llm._parse_analysis(content).matched_skills == ["Python", "FastAPI"]


def test_invalid_json_raises_safe_error() -> None:
    with pytest.raises(llm.LLMResponseFormatError, match="模型返回格式错误"):
        llm._parse_analysis("not json")


def test_analyze_job_parses_mocked_model_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    content = json.dumps(VALID_ANALYSIS, ensure_ascii=False)
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
    )
    fake_completions = SimpleNamespace(create=lambda **kwargs: fake_response)
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=fake_completions),
    )
    monkeypatch.setattr(llm, "ENV_FILE", tmp_path / ".env")
    monkeypatch.setenv("LLM_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm, "OpenAI", lambda **kwargs: fake_client)

    analysis = llm.analyze_job("Python 开发", "负责 FastAPI 接口开发")

    assert analysis.score == 85


def test_missing_api_key_does_not_crash(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(llm, "ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    response = client.post(
        "/api/analyze-job",
        json={"job_title": "Python 开发", "job_description": "负责 API 开发"},
    )

    assert response.status_code == 503
    assert "LLM_API_KEY" in response.json()["detail"]


def test_invalid_model_response_returns_502(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_format_error(job_title: str, job_description: str) -> None:
        raise llm.LLMResponseFormatError("模型返回格式错误")

    monkeypatch.setattr(main, "analyze_job", raise_format_error)

    response = client.post(
        "/api/analyze-job",
        json={"job_title": "Python 开发", "job_description": "负责 API 开发"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型返回格式错误"}
