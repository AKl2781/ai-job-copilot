"""Static checks for browser extension workflows."""

import json
import importlib.util
import io
import struct
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POPUP_HTML = (PROJECT_ROOT / "extension" / "popup.html").read_text(encoding="utf-8")
POPUP_JS = (PROJECT_ROOT / "extension" / "popup.js").read_text(encoding="utf-8")
MANIFEST = json.loads(
    (PROJECT_ROOT / "extension" / "manifest.json").read_text(encoding="utf-8")
)
BACKGROUND_JS = (PROJECT_ROOT / "extension" / "background.js").read_text(encoding="utf-8")
HOST_PATH = PROJECT_ROOT / "native_host" / "host.py"
HOST_SOURCE = HOST_PATH.read_text(encoding="utf-8")
INSTALL_SOURCE = (PROJECT_ROOT / "scripts" / "install_native_host.ps1").read_text(encoding="utf-8")
UNINSTALL_SOURCE = (PROJECT_ROOT / "scripts" / "uninstall_native_host.ps1").read_text(encoding="utf-8")
START_BACKEND_SOURCE = (PROJECT_ROOT / "scripts" / "start_backend.ps1").read_text(encoding="utf-8-sig")

HOST_SPEC = importlib.util.spec_from_file_location("ai_job_copilot_native_host", HOST_PATH)
assert HOST_SPEC and HOST_SPEC.loader
HOST = importlib.util.module_from_spec(HOST_SPEC)
HOST_SPEC.loader.exec_module(HOST)


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
    assert "confirm(" not in POPUP_JS
    assert "window.confirm" not in POPUP_JS
    assert "重新读取岗位" in POPUP_HTML
    assert "打开岗位详情页后按 Alt+J，可自动读取岗位内容" in POPUP_HTML


def test_manifest_has_action_shortcut_without_broad_access() -> None:
    command = MANIFEST["commands"]["_execute_action"]

    assert command["suggested_key"]["default"] == "Alt+J"
    assert command["suggested_key"]["windows"] == "Alt+J"
    assert "<all_urls>" not in MANIFEST.get("host_permissions", [])


def _native_message(value: object) -> bytes:
    payload = json.dumps(value).encode("utf-8")
    return struct.pack("<I", len(payload)) + payload


def test_native_host_reads_valid_message() -> None:
    assert HOST.read_message(io.BytesIO(_native_message({"action": "status"}))) == {
        "action": "status"
    }


def test_native_host_writes_little_endian_length_prefixed_json() -> None:
    stream = io.BytesIO()
    response = {"ok": True, "state": "running", "message": "本地服务正在运行"}
    HOST.write_message(stream, response)
    encoded = stream.getvalue()
    length = struct.unpack("<I", encoded[:4])[0]
    assert length == len(encoded[4:])
    assert json.loads(encoded[4:].decode("utf-8")) == response


@pytest.mark.parametrize(
    "payload",
    [
        b"\x01\x00",
        struct.pack("<I", 0),
        struct.pack("<I", HOST.MAX_MESSAGE_BYTES + 1),
        struct.pack("<I", 5) + b"{}",
    ],
)
def test_native_host_rejects_invalid_lengths(payload: bytes) -> None:
    with pytest.raises(HOST.NativeMessageError):
        HOST.read_message(io.BytesIO(payload))


def test_native_host_rejects_invalid_json_safely() -> None:
    payload = b"{bad}"
    with pytest.raises(HOST.NativeMessageError, match="JSON"):
        HOST.read_message(io.BytesIO(struct.pack("<I", len(payload)) + payload))


def test_native_host_rejects_unknown_action_and_ignores_injected_fields() -> None:
    assert HOST.handle_message({"action": "launch", "command": "whoami"}) == {
        "ok": False,
        "state": "error",
        "message": "不支持的本地服务操作",
    }
    called = []
    original = HOST.ACTIONS["status"]
    try:
        HOST.ACTIONS["status"] = lambda: called.append("status") or {
            "ok": True,
            "state": "stopped",
            "message": "ok",
        }
        HOST.handle_message({"action": "status", "command": "whoami", "path": "C:\\temp"})
    finally:
        HOST.ACTIONS["status"] = original
    assert called == ["status"]


def test_native_host_action_map_is_fixed_and_subprocess_is_not_shell() -> None:
    assert set(HOST.ACTIONS) == {"status", "start", "stop"}
    assert HOST.ACTIONS["status"] is HOST.status_action
    assert HOST.ACTIONS["start"] is HOST.start_action
    assert HOST.ACTIONS["stop"] is HOST.stop_action
    assert "shell=False" in HOST_SOURCE
    assert "START_SCRIPT" in HOST_SOURCE and "STOP_SCRIPT" in HOST_SOURCE
    assert "shell=True" not in HOST_SOURCE


def test_native_host_uses_hidden_windows_only_for_native_start(monkeypatch) -> None:
    captured = {}

    def fake_run(arguments, **kwargs):
        captured["arguments"] = arguments
        captured["kwargs"] = kwargs
        return type("Completed", (), {"returncode": 0})()

    monkeypatch.setattr(HOST.subprocess, "run", fake_run)
    assert HOST._run_fixed_script(
        HOST.START_SCRIPT,
        15.0,
        hidden_backend_window=True,
    )
    assert captured["arguments"][-1] == "-Hidden"
    assert captured["kwargs"]["shell"] is False
    assert captured["kwargs"]["creationflags"] == HOST.subprocess.CREATE_NO_WINDOW
    assert "[switch]$Hidden" in START_BACKEND_SOURCE
    assert "if (-not $Hidden)" in START_BACKEND_SOURCE
    assert "$backendArguments += '-NoExit'" in START_BACKEND_SOURCE
    assert "if ($Hidden) { 'Hidden' } else { 'Normal' }" in START_BACKEND_SOURCE


def test_native_host_does_not_access_secrets_or_modify_env_file() -> None:
    assert "API_KEY" not in HOST_SOURCE
    assert "os.environ" not in HOST_SOURCE
    assert 'PROJECT_ROOT / ".env"' not in HOST_SOURCE
    assert "traceback.print" not in HOST_SOURCE.lower()
    assert "print(" not in HOST_SOURCE


def test_manifest_and_service_worker_use_native_messaging_without_broad_access() -> None:
    assert "nativeMessaging" in MANIFEST["permissions"]
    assert MANIFEST["background"]["service_worker"] == "background.js"
    assert "<all_urls>" not in json.dumps(MANIFEST)
    assert "sendNativeMessage" in BACKGROUND_JS
    for action in ("status", "start", "stop"):
        assert f'"{action}"' in BACKGROUND_JS
    assert "content.js" not in MANIFEST.get("background", {}).values()


def test_popup_contains_service_control_and_safe_analysis_resume() -> None:
    for text in (
        "本地服务",
        "启动本地服务",
        "首次使用需要运行",
        "尚未安装本地连接组件",
        "正在启动",
        "运行中",
        "正在停止",
    ):
        assert text in POPUP_HTML or text in POPUP_JS
    assert "ensureServiceForAnalysis" in POPUP_JS
    assert "if (!(await ensureServiceForAnalysis())) return" in POPUP_JS
    assert "return startLocalService();" in POPUP_JS
    assert "confirm(" not in POPUP_JS


def test_installer_is_edge_hkcu_only_and_exact_origin() -> None:
    assert "HKCU:\\Software\\Microsoft\\Edge\\NativeMessagingHosts" in INSTALL_SOURCE
    assert "chrome-extension://$ExtensionId/" in INSTALL_SOURCE
    assert "^[a-p]{32}$" in INSTALL_SOURCE
    assert "HKLM" not in INSTALL_SOURCE
    assert "Google\\Chrome" not in INSTALL_SOURCE
    assert '"*"' not in INSTALL_SOURCE
    assert "resolvedExistingPath -ne $resolvedManifestPath" in INSTALL_SOURCE


def test_uninstaller_only_removes_current_project_registration() -> None:
    assert "resolvedRegisteredPath -ne $resolvedManifestPath" in UNINSTALL_SOURCE
    assert "Remove-Item -LiteralPath $RegistryPath" in UNINSTALL_SOURCE
    assert "Remove-Item -LiteralPath $ManifestPath" in UNINSTALL_SOURCE
    assert "HKLM" not in UNINSTALL_SOURCE
