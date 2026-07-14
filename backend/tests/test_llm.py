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
    captured_request = {}
    content = json.dumps(VALID_ANALYSIS, ensure_ascii=False)
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
    )
    def create_completion(**kwargs):
        captured_request.update(kwargs)
        return fake_response

    fake_completions = SimpleNamespace(create=create_completion)
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=fake_completions),
    )
    monkeypatch.setattr(llm, "ENV_FILE", tmp_path / ".env")
    monkeypatch.setenv("LLM_API_KEY", "test-key-not-real")
    monkeypatch.setattr(llm, "OpenAI", lambda **kwargs: fake_client)

    analysis = llm.analyze_job(
        "Python 开发",
        "要求 Python、FastAPI 和 Redis",
        "掌握 Python 和 FastAPI，未使用过 Redis",
    )

    assert analysis.score == 85
    messages = captured_request["messages"]
    assert "要求 Python、FastAPI 和 Redis" in messages[1]["content"]
    assert "掌握 Python 和 FastAPI，未使用过 Redis" in messages[1]["content"]
    assert "岗位 JD 中出现的技能不能自动视为候选人已经掌握" in messages[0]["content"]
    assert "不得提升 candidate_profile 中任何技能的熟练程度" in messages[0]["content"]
    assert "不得将“掌握”改写为“熟练掌握”或“精通”" in messages[0]["content"]
    assert "不得将“了解”改写为“掌握”或“熟悉”" in messages[0]["content"]
    assert "greeting 应尽量复用 candidate_profile 的原始措辞" in messages[0]["content"]
    assert "只能使用其中有直接依据的能力描述" in messages[0]["content"]
    assert captured_request["temperature"] == 0.0


def test_missing_api_key_does_not_crash(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(llm, "ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    response = client.post(
        "/api/analyze-job",
        json={
            "job_title": "Python 开发",
            "job_description": "负责 API 开发",
            "candidate_profile": "掌握 Python",
        },
    )

    assert response.status_code == 503
    assert "LLM_API_KEY" in response.json()["detail"]


def test_invalid_model_response_returns_502(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_format_error(
        job_title: str,
        job_description: str,
        candidate_profile: str,
    ) -> None:
        raise llm.LLMResponseFormatError("模型返回格式错误")

    monkeypatch.setattr(main, "analyze_job", raise_format_error)

    response = client.post(
        "/api/analyze-job",
        json={
            "job_title": "Python 开发",
            "job_description": "负责 API 开发",
            "candidate_profile": "掌握 Python",
        },
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型返回格式错误"}


@pytest.mark.parametrize(
    "payload",
    [
        {"job_title": "Python 开发", "job_description": "负责 API 开发"},
        {
            "job_title": "Python 开发",
            "job_description": "负责 API 开发",
            "candidate_profile": "   ",
        },
    ],
)
def test_candidate_profile_is_required(payload: dict[str, str]) -> None:
    response = client.post("/api/analyze-job", json=payload)

    assert response.status_code == 422


def test_three_field_request_enters_llm_service(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_analyze_job(
        job_title: str,
        job_description: str,
        candidate_profile: str,
    ) -> llm.JobAnalysis:
        captured.update(
            job_title=job_title,
            job_description=job_description,
            candidate_profile=candidate_profile,
        )
        return llm.JobAnalysis.model_validate(VALID_ANALYSIS)

    monkeypatch.setattr(main, "analyze_job", fake_analyze_job)
    response = client.post(
        "/api/analyze-job",
        json={
            "job_title": " Python 开发 ",
            "job_description": " 负责 API 开发 ",
            "candidate_profile": " 掌握 Python和 Git ",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "job_title": "Python 开发",
        "job_description": "负责 API 开发",
        "candidate_profile": "掌握 Python和 Git",
    }
