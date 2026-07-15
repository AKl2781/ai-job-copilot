"""DeepSeek evidence extraction plus deterministic backend scoring."""

import json
import os
from pathlib import Path
from typing import Any, Literal

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .scoring import calculate_match_score

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

SYSTEM_PROMPT = """你是岗位要求与候选人证据提取器。严格返回 JSON，不要返回 Markdown 或解释。

只提取岗位要求、候选人证据和离散状态；不要决定、建议或估算最终 score，也不要输出维度分数。
必须返回以下结构：
{
  "job_requirements": {
    "core_skills": [], "preferred_skills": [], "project_requirements": [],
    "education_requirements": [], "experience_requirements": []
  },
  "matched_skills": [], "partial_skills": [], "missing_skills": [], "unverified_skills": [],
  "project_evidence": [], "education_evidence": [], "experience_evidence": [],
  "project_status": "direct|related|general|unverified|missing",
  "education_status": "matched|partial|unverified|missing",
  "experience_status": "matched|partial|unverified|missing",
  "learning_plan": [], "reasoning": [], "greeting": "...", "confidence": 0.85
}

规则：
1. matched 仅表示 candidate_profile 有明确直接证据；partial 仅表示了解、基础、学习中或使用过但未达到要求。
2. missing 仅表示资料明确说明不会或没有经验；JD 提到但资料不足的一律为 unverified。
3. 技能状态数组使用 job_requirements 中完全相同的技能名称，每项要求只放入一个状态数组。
4. JD 中的技能不能自动视为候选人技能，不得提升候选人的熟练程度。
5. 不得虚构项目、教育、工作或实习经历。证据数组只能来自 candidate_profile。
6. project_status 只描述项目证据相关性：直接相关、相近、泛项目、未核实或明确没有。
7. 教育和经验状态只描述证据是否满足对应要求；岗位无对应要求时使用 unverified，后端会标记不适用。
8. greeting 必须真实、克制，尽量复用 candidate_profile 原始措辞，不得夸大。
9. 所有数组只包含字符串，confidence 为 0 到 1 的数字，严格返回 JSON。
"""


class JobRequirements(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    core_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    project_requirements: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    experience_requirements: list[str] = Field(default_factory=list)


class ExtractedAnalysis(BaseModel):
    """Structured evidence returned by the model; legacy score is ignored as extra data."""

    model_config = ConfigDict(extra="ignore", strict=True)

    job_requirements: JobRequirements = Field(default_factory=JobRequirements)
    matched_skills: list[str] = Field(default_factory=list)
    partial_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    unverified_skills: list[str] = Field(default_factory=list)
    project_evidence: list[str] = Field(default_factory=list)
    education_evidence: list[str] = Field(default_factory=list)
    experience_evidence: list[str] = Field(default_factory=list)
    project_status: Literal["direct", "related", "general", "unverified", "missing"] = "unverified"
    education_status: Literal["matched", "partial", "unverified", "missing"] = "unverified"
    experience_status: Literal["matched", "partial", "unverified", "missing"] = "unverified"
    learning_plan: list[str] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)
    greeting: str = "分析已完成。"
    confidence: float = Field(default=0.0, ge=0, le=1)


class ScoreDimension(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    score: int = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    applicable: bool
    reason: str = Field(min_length=1)


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    core_skills: ScoreDimension
    preferred_skills: ScoreDimension
    project_experience: ScoreDimension
    education_background: ScoreDimension
    work_experience: ScoreDimension


class JobAnalysis(BaseModel):
    """Final API response after backend scoring."""

    model_config = ConfigDict(extra="forbid", strict=True)

    score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    summary: str = Field(min_length=1)
    matched_skills: list[str]
    partial_skills: list[str]
    missing_skills: list[str]
    unverified_skills: list[str]
    project_evidence: list[str]
    education_evidence: list[str]
    experience_evidence: list[str]
    learning_plan: list[str]
    reasoning: list[str]
    greeting: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class LLMServiceError(RuntimeError):
    def __init__(self, public_message: str, status_code: int = 502) -> None:
        super().__init__(public_message)
        self.public_message = public_message
        self.status_code = status_code


class LLMConfigurationError(LLMServiceError):
    pass


class LLMResponseFormatError(LLMServiceError):
    pass


def _load_env_file() -> None:
    if not ENV_FILE.is_file():
        return
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
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
        raise LLMConfigurationError("AI 服务尚未配置，请设置 LLM_API_KEY", status_code=503)
    if not base_url or not model:
        raise LLMConfigurationError("AI 服务配置不完整", status_code=503)
    return api_key, base_url, model


def _extract_json_object(content: str) -> dict[str, Any]:
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


def _build_final_analysis(extracted: ExtractedAnalysis) -> JobAnalysis:
    requirements = extracted.job_requirements
    calculated = calculate_match_score(
        core_skills=requirements.core_skills,
        preferred_skills=requirements.preferred_skills,
        project_requirements=requirements.project_requirements,
        education_requirements=requirements.education_requirements,
        experience_requirements=requirements.experience_requirements,
        matched_skills=extracted.matched_skills,
        partial_skills=extracted.partial_skills,
        missing_skills=extracted.missing_skills,
        unverified_skills=extracted.unverified_skills,
        project_status=extracted.project_status,
        education_status=extracted.education_status,
        experience_status=extracted.experience_status,
    )
    score = calculated["score"]
    classified = calculated["classified_skills"]
    return JobAnalysis.model_validate(
        {
            "score": score,
            "score_breakdown": calculated["score_breakdown"],
            "summary": f"按岗位明确要求和候选人证据确定性计算，综合匹配度为 {score} 分。",
            "matched_skills": classified["matched"],
            "partial_skills": classified["partial"],
            "missing_skills": classified["missing"],
            "unverified_skills": classified["unverified"],
            "project_evidence": extracted.project_evidence,
            "education_evidence": extracted.education_evidence,
            "experience_evidence": extracted.experience_evidence,
            "learning_plan": extracted.learning_plan,
            "reasoning": extracted.reasoning,
            "greeting": extracted.greeting,
            "confidence": extracted.confidence,
        }
    )


def _parse_analysis(content: str) -> JobAnalysis:
    try:
        extracted = ExtractedAnalysis.model_validate(_extract_json_object(content))
        return _build_final_analysis(extracted)
    except (ValidationError, LLMResponseFormatError) as exc:
        raise LLMResponseFormatError("模型返回格式错误") from exc


def analyze_job(job_title: str, job_description: str, candidate_profile: str) -> JobAnalysis:
    api_key, base_url, model = _read_config()
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=30.0, max_retries=1)
    user_prompt = (
        f"岗位标题：{job_title}\n\n岗位描述（仅用于识别岗位要求）：\n{job_description}\n\n"
        f"候选人资料（判断候选人技能和经历的唯一依据）：\n{candidate_profile}"
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=2500,
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
