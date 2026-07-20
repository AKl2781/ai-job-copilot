"""Regression tests for Native Host backend project detection."""

import json
import os
import time
from pathlib import Path

import pytest

from native_host import host

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _write_state(
    monkeypatch,
    tmp_path: Path,
    *,
    project_root: object,
    listener_pid: int = 1200,
    host_pid: int = 1100,
) -> None:
    state_path = tmp_path / "backend-state.json"
    state_path.write_text(
        json.dumps(
            {
                "ProjectRoot": str(project_root),
                "HostProcessId": host_pid,
                "ListenerProcessId": listener_pid,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(host, "_state_file_path", lambda: state_path)


def _mock_valid_process_evidence(monkeypatch) -> None:
    monkeypatch.setattr(host, "_pid_owns_backend_port", lambda pid: pid == 1200)
    monkeypatch.setattr(
        host,
        "_process_matches_backend",
        lambda listener_pid, host_pid: (listener_pid, host_pid) == (1200, 1100),
    )


def test_current_project_backend_is_recognized(monkeypatch, tmp_path) -> None:
    _write_state(monkeypatch, tmp_path, project_root=host.PROJECT_ROOT)
    _mock_valid_process_evidence(monkeypatch)

    assert host._backend_state_matches_project()


def test_project_path_accepts_case_slashes_and_spaces(monkeypatch, tmp_path) -> None:
    project_root = tmp_path / "Project With Space"
    project_root.mkdir()
    monkeypatch.setattr(host, "PROJECT_ROOT", project_root)
    alternate_form = str(project_root).upper().replace("\\", "/")
    _write_state(monkeypatch, tmp_path, project_root=alternate_form)
    _mock_valid_process_evidence(monkeypatch)

    assert host._backend_state_matches_project()


def test_relative_current_project_path_is_recognized(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(PROJECT_ROOT.parent)
    monkeypatch.setattr(host, "PROJECT_ROOT", PROJECT_ROOT)
    _write_state(monkeypatch, tmp_path, project_root=PROJECT_ROOT.name)
    _mock_valid_process_evidence(monkeypatch)

    assert host._backend_state_matches_project()


def test_wrong_project_is_not_recognized(monkeypatch, tmp_path) -> None:
    _write_state(monkeypatch, tmp_path, project_root=tmp_path / "another-project")
    _mock_valid_process_evidence(monkeypatch)

    assert not host._backend_state_matches_project()


def test_exited_listener_pid_is_not_recognized(monkeypatch, tmp_path) -> None:
    _write_state(monkeypatch, tmp_path, project_root=host.PROJECT_ROOT)
    monkeypatch.setattr(host, "_pid_owns_backend_port", lambda _pid: True)
    monkeypatch.setattr(host, "_process_matches_backend", lambda *_args: False)

    assert not host._backend_state_matches_project()


def test_wrong_port_or_process_identity_is_not_recognized(monkeypatch, tmp_path) -> None:
    _write_state(monkeypatch, tmp_path, project_root=host.PROJECT_ROOT)
    monkeypatch.setattr(host, "_pid_owns_backend_port", lambda _pid: False)
    monkeypatch.setattr(host, "_process_matches_backend", lambda *_args: True)
    assert not host._backend_state_matches_project()

    monkeypatch.setattr(host, "_pid_owns_backend_port", lambda _pid: True)
    monkeypatch.setattr(host, "_process_matches_backend", lambda *_args: False)
    assert not host._backend_state_matches_project()


@pytest.mark.skipif(os.name != "nt", reason="Native Host lifecycle is Windows-only")
def test_real_native_host_start_status_stop_lifecycle() -> None:
    if not (PROJECT_ROOT / ".env").is_file():
        pytest.skip("local Native Host lifecycle requires the ignored root .env file")
    if host.is_backend_healthy():
        pytest.skip("port 8000 is already serving a backend")

    try:
        started = host.start_action()
        assert started["state"] in {"running", "starting"}
        deadline = time.monotonic() + 8
        state = host.status_action()
        while state["state"] != "running" and time.monotonic() < deadline:
            time.sleep(0.5)
            state = host.status_action()
        assert state["state"] == "running"
    finally:
        stopped = host.stop_action()
        assert stopped["state"] in {"stopped", "stopping"}

    deadline = time.monotonic() + 5
    while host.status_action()["state"] != "stopped" and time.monotonic() < deadline:
        time.sleep(0.25)
    assert host.status_action()["state"] == "stopped"
    assert not host.is_backend_healthy()
