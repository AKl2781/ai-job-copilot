"""Backward-compatible imports for the modular job-analysis implementation."""

from ..application.analysis_service import AnalysisService
from ..infrastructure.llm import deepseek as _deepseek
from ..infrastructure.llm.parser import (
    ExtractedAnalysis,
    JobAnalysis,
    JobRequirements,
    ScoreBreakdown,
    ScoreDimension,
    build_final_analysis,
    extract_json_object,
    parse_analysis,
)
from ..infrastructure.llm.provider import (
    LLMConfigurationError,
    LLMResponseFormatError,
    LLMServiceError,
)

# These aliases keep existing imports and test seams working during migration.
ENV_FILE = _deepseek.ENV_FILE
OpenAI = _deepseek.OpenAI
PROJECT_ROOT = _deepseek.PROJECT_ROOT
SYSTEM_PROMPT = _deepseek.SYSTEM_PROMPT


def _load_env_file() -> None:
    _deepseek._load_env_file(ENV_FILE)


def _read_config() -> tuple[str, str, str]:
    return _deepseek._read_config(ENV_FILE)


def _extract_json_object(content: str):
    return extract_json_object(content)


def _build_final_analysis(extracted: ExtractedAnalysis) -> JobAnalysis:
    return build_final_analysis(extracted)


def _parse_analysis(content: str) -> JobAnalysis:
    return parse_analysis(content)


def analyze_job(job_title: str, job_description: str, candidate_profile: str) -> JobAnalysis:
    """Preserve the original service entry point while delegating to the use case."""
    provider = _deepseek.DeepSeekProvider(env_file=ENV_FILE, client_factory=OpenAI)
    return AnalysisService(provider).analyze_job(
        job_title,
        job_description,
        candidate_profile,
    )


__all__ = [
    "ExtractedAnalysis",
    "ENV_FILE",
    "JobAnalysis",
    "JobRequirements",
    "LLMConfigurationError",
    "LLMResponseFormatError",
    "LLMServiceError",
    "OpenAI",
    "PROJECT_ROOT",
    "ScoreBreakdown",
    "ScoreDimension",
    "SYSTEM_PROMPT",
    "analyze_job",
]
