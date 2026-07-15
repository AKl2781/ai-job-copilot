"""Short-lived Microsoft Edge Native Messaging host for backend control."""

from __future__ import annotations

import json
import hashlib
import os
import struct
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import BinaryIO, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
START_SCRIPT = PROJECT_ROOT / "scripts" / "start_backend.ps1"
STOP_SCRIPT = PROJECT_ROOT / "scripts" / "stop_backend.ps1"
HEALTH_URL = "http://127.0.0.1:8000/health"
MAX_MESSAGE_BYTES = 64 * 1024
VALID_STATES = {"stopped", "starting", "running", "stopping", "error"}


class NativeMessageError(ValueError):
    """A safe protocol error that may be returned to the extension."""


def _read_exact(stream: BinaryIO, length: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < length:
        chunk = stream.read(length - len(chunks))
        if not chunk:
            raise NativeMessageError("Native Messaging 消息不完整")
        chunks.extend(chunk)
    return bytes(chunks)


def read_message(stream: BinaryIO) -> dict[str, object]:
    try:
        header = _read_exact(stream, 4)
    except NativeMessageError as exc:
        raise NativeMessageError("Native Messaging 消息长度无效") from exc
    length = struct.unpack("<I", header)[0]
    if length == 0 or length > MAX_MESSAGE_BYTES:
        raise NativeMessageError("Native Messaging 消息长度无效")
    try:
        value = json.loads(_read_exact(stream, length).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NativeMessageError("Native Messaging JSON 无效") from exc
    if not isinstance(value, dict):
        raise NativeMessageError("Native Messaging JSON 必须是对象")
    return value


def write_message(stream: BinaryIO, response: dict[str, object]) -> None:
    state = response.get("state")
    if state not in VALID_STATES:
        raise ValueError("invalid response state")
    payload = json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stream.write(struct.pack("<I", len(payload)))
    stream.write(payload)
    stream.flush()


def is_backend_healthy() -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=1.5) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read(4096).decode("utf-8"))
            return isinstance(payload, dict) and payload.get("status") == "ok"
    except (OSError, ValueError, json.JSONDecodeError):
        return False


def _backend_state_matches_project() -> bool:
    normalized = str(PROJECT_ROOT.resolve()).rstrip("\\").lower().encode("utf-8")
    project_id = hashlib.sha256(normalized).hexdigest()[:16]
    state_path = Path(tempfile.gettempdir()) / "AIJobCopilot" / f"backend-{project_id}.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        listener_pid = int(state.get("ListenerProcessId") or 0)
        if Path(str(state.get("ProjectRoot", ""))).resolve() != PROJECT_ROOT.resolve():
            return False
        if listener_pid <= 0:
            return False
        os.kill(listener_pid, 0)
        return True
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def is_current_backend_healthy() -> bool:
    return _backend_state_matches_project() and is_backend_healthy()


def _run_fixed_script(script: Path, timeout: float) -> bool:
    if not script.is_file() or script.parent.resolve() != (PROJECT_ROOT / "scripts").resolve():
        return False
    try:
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ],
            cwd=str(PROJECT_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def status_action() -> dict[str, object]:
    running = is_current_backend_healthy()
    return {
        "ok": True,
        "state": "running" if running else "stopped",
        "message": "本地服务正在运行" if running else "本地服务已停止",
    }


def start_action() -> dict[str, object]:
    if is_current_backend_healthy():
        return {"ok": True, "state": "running", "message": "本地服务正在运行"}
    if not _run_fixed_script(START_SCRIPT, 15.0):
        return {"ok": False, "state": "error", "message": "本地服务启动失败，请检查后端日志"}
    if is_current_backend_healthy():
        return {"ok": True, "state": "running", "message": "本地服务已启动"}
    return {"ok": True, "state": "starting", "message": "本地服务正在启动"}


def stop_action() -> dict[str, object]:
    if not is_backend_healthy():
        return {"ok": True, "state": "stopped", "message": "本地服务已停止"}
    if not _run_fixed_script(STOP_SCRIPT, 10.0):
        return {"ok": False, "state": "error", "message": "本地服务停止失败，请手动检查"}
    if is_current_backend_healthy():
        return {"ok": True, "state": "stopping", "message": "本地服务正在停止"}
    return {"ok": True, "state": "stopped", "message": "本地服务已停止"}


ACTIONS: dict[str, Callable[[], dict[str, object]]] = {
    "status": status_action,
    "start": start_action,
    "stop": stop_action,
}


def handle_message(message: dict[str, object]) -> dict[str, object]:
    action = message.get("action")
    if not isinstance(action, str) or action not in ACTIONS:
        return {"ok": False, "state": "error", "message": "不支持的本地服务操作"}
    return ACTIONS[action]()


def _set_binary_stdio() -> None:
    if os.name == "nt":
        import msvcrt  # pylint: disable=import-outside-toplevel

        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)


def main() -> int:
    _set_binary_stdio()
    try:
        response = handle_message(read_message(sys.stdin.buffer))
    except NativeMessageError as exc:
        response = {"ok": False, "state": "error", "message": str(exc)}
    except Exception:  # Never expose an internal traceback to the extension.
        response = {"ok": False, "state": "error", "message": "本地连接组件发生安全错误"}
    write_message(sys.stdout.buffer, response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
