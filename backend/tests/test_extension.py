"""Static checks for browser extension workflows."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POPUP_HTML = (PROJECT_ROOT / "extension" / "popup.html").read_text(encoding="utf-8")
POPUP_JS = (PROJECT_ROOT / "extension" / "popup.js").read_text(encoding="utf-8")
MANIFEST = json.loads(
    (PROJECT_ROOT / "extension" / "manifest.json").read_text(encoding="utf-8")
)


def test_candidate_profile_input_and_request_payload_exist() -> None:
    assert 'id="candidate-profile"' in POPUP_HTML
    assert "我的技能 / 简历简介" in POPUP_HTML
    assert "candidate_profile: candidateProfileText" in POPUP_JS


def test_empty_candidate_profile_blocks_request() -> None:
    validation_position = POPUP_JS.index("if (!candidateProfileText)")
    fetch_position = POPUP_JS.index('fetch("http://127.0.0.1:8000/api/analyze-job"')

    assert validation_position < fetch_position
    assert "请先填写真实的个人技能或简历简介" in POPUP_JS


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


def test_optional_analysis_fields_are_backward_compatible() -> None:
    for field in ("score_breakdown", "partial_skills", "unverified_skills"):
        assert f"analysis.{field}" in POPUP_JS

    assert "function asArray" in POPUP_JS
    assert 'id="score-breakdown-section"' in POPUP_HTML
    assert 'id="partial-skills-section"' in POPUP_HTML
    assert 'id="unverified-skills-section"' in POPUP_HTML


def test_popup_has_loading_copy_and_scroll_interactions() -> None:
    assert "setLoadingState(true)" in POPUP_JS
    assert "正在分析岗位……" in POPUP_JS
    assert 'id="analyze-spinner"' in POPUP_HTML
    assert 'id="copy-greeting"' in POPUP_HTML
    assert "navigator.clipboard.writeText" in POPUP_JS
    assert "scrollIntoView" in POPUP_JS


def test_popup_automatically_reads_and_keeps_reread_button() -> None:
    assert "readCurrentJob({ automatic: true })" in POPUP_JS
    assert "jobDescriptionEdited" in POPUP_JS
    assert "window.confirm" in POPUP_JS
    assert "重新读取岗位" in POPUP_HTML
    assert "打开岗位详情页后按 Alt+J，可自动读取岗位内容" in POPUP_HTML


def test_manifest_has_action_shortcut_without_broad_access() -> None:
    command = MANIFEST["commands"]["_execute_action"]

    assert command["suggested_key"]["default"] == "Alt+J"
    assert command["suggested_key"]["windows"] == "Alt+J"
    assert "<all_urls>" not in MANIFEST.get("host_permissions", [])
