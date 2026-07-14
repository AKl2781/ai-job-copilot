"""DeepSeek-backed job analysis service."""

import json
import os
from pathlib import Path
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

SYSTEM_PROMPT = """你是一名专业的技术招聘顾问。
请根据用户提供的岗位标题和岗位描述进行分析，并严格返回一个 JSON 对象。
不要返回 Markdown，不要解释，不要输出 JSON 以外的任何内容。

JSON 必须严格使用以下结构：
{
  "score": 85,
  "summary": "岗位匹配摘要",
  "matched_skills": ["已匹配技能"],
  "missing_skills": ["待补技能"],
  "learning_plan": ["具体学习建议"],
  "reasoning": ["判断理由"],
  "greeting": "真实、简洁、不夸大的打招呼文案",
  "confidence": 0.91
}

要求：
1. score 是 0 到 100 之间的整数，表示岗位匹配度。
2. 分析已匹配技能、待补技能、学习建议以及为什么这样判断。
3. greeting 必须真实、简洁、不夸大候选人的能力。
4. confidence 是 0 到 1 之间的数字。
5. 所有数组只包含字符串。
"""


class JobAnalysis(BaseModel):
    """Validated job analysis returned by the model."""

    model_config = ConfigDict(extra="forbid", strict=True)

    score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=1)
    matched_skills: list[str]
    missing_skills: list[str]
    learning_plan: list[str]
    reasoning: list[str]
    greeting: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class LLMServiceError(RuntimeError):
    """Safe error that can be returned by the API layer."""

    def __init__(self, public_message: str, status_code: int = 502) -> None:
        super().__init__(public_message)
        self.public_message = public_message
        self.status_code = status_code


class LLMConfigurationError(LLMServiceError):
    """Raised when required LLM configuration is missing or unsupported."""


class LLMResponseFormatError(LLMServiceError):
    """Raised when the model response cannot be parsed and validated."""


def _load_env_file() -> None:
    """Load simple KEY=VALUE entries from the project .env without overriding OS values."""
    if not ENV_FILE.is_file():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value[:1] in {'"', "'"}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def _read_config() -> tuple[str, str, str]:
    _load_env_file()

    provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").strip()
    model = os.getenv("LLM_MODEL", "deepseek-chat").strip()

    if provider != "deepseek":
        raise LLMConfigurationError("当前仅支持 DeepSeek 服务", status_code=503)
    if not api_key:
        raise LLMConfigurationError(
            "AI 服务尚未配置，请在项目根目录 .env 中填写 LLM_API_KEY",
            status_code=503,
        )
    if not base_url or not model:
        raise LLMConfigurationError("AI 服务配置不完整", status_code=503)

    return api_key, base_url, model


def _extract_json_object(content: str) -> dict[str, Any]:
    """Parse a JSON object, extracting it from surrounding model text when necessary."""
    stripped = content.strip()
    if not stripped:
        raise LLMResponseFormatError("模型返回格式错误")

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, character in enumerate(stripped):
        if character != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise LLMResponseFormatError("模型返回格式错误")


def _parse_analysis(content: str) -> JobAnalysis:
    try:
        return JobAnalysis.model_validate(_extract_json_object(content))
    except (ValidationError, LLMResponseFormatError) as exc:
        raise LLMResponseFormatError("模型返回格式错误") from exc


def analyze_job(job_title: str, job_description: str) -> JobAnalysis:
    """Ask DeepSeek to analyze a job description and return validated JSON."""
    api_key, base_url, model = _read_config()
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=30.0, max_retries=1)
    user_prompt = f"岗位标题：{job_title}\n\n岗位描述：\n{job_description}"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2000,
        )
    except APITimeoutError as exc:
        raise LLMServiceError("AI 服务请求超时，请稍后重试", status_code=504) from exc
    except AuthenticationError as exc:
        raise LLMServiceError("AI 服务认证失败，请检查 API Key", status_code=502) from exc
    except RateLimitError as exc:
        raise LLMServiceError("AI 服务请求过于频繁，请稍后重试", status_code=503) from exc
    except APIConnectionError as exc:
        raise LLMServiceError("无法连接 AI 服务，请稍后重试", status_code=502) from exc
    except APIStatusError as exc:
        raise LLMServiceError("AI 服务暂时不可用，请稍后重试", status_code=502) from exc

    try:
        content = response.choices[0].message.content or ""
    except (AttributeError, IndexError) as exc:
        raise LLMResponseFormatError("模型返回格式错误") from exc
    return _parse_analysis(content)
