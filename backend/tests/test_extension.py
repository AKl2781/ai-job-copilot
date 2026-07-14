"""Static checks for the candidate profile flow in the browser extension."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POPUP_HTML = (PROJECT_ROOT / "extension" / "popup.html").read_text(encoding="utf-8")
POPUP_JS = (PROJECT_ROOT / "extension" / "popup.js").read_text(encoding="utf-8")


def test_candidate_profile_input_and_request_payload_exist() -> None:
    assert 'id="candidate-profile"' in POPUP_HTML
    assert "我的技能 / 简历简介" in POPUP_HTML
    assert "candidate_profile: candidateProfileText" in POPUP_JS


def test_empty_candidate_profile_blocks_request() -> None:
    validation_position = POPUP_JS.index("if (!candidateProfileText)")
    fetch_position = POPUP_JS.index('fetch("http://127.0.0.1:8000/api/analyze-job"')

    assert validation_position < fetch_position
    assert "请先填写个人技能或简历简介" in POPUP_JS


def test_candidate_profile_uses_local_storage() -> None:
    assert "localStorage.getItem(CANDIDATE_PROFILE_STORAGE_KEY)" in POPUP_JS
    assert "localStorage.setItem(CANDIDATE_PROFILE_STORAGE_KEY" in POPUP_JS
    assert "DEFAULT_CANDIDATE_PROFILE" in POPUP_JS


def test_analysis_json_fields_are_rendered() -> None:
    for field in (
        "score",
        "summary",
        "matched_skills",
        "missing_skills",
        "learning_plan",
        "reasoning",
        "greeting",
        "confidence",
    ):
        assert f"analysis.{field}" in POPUP_JS
