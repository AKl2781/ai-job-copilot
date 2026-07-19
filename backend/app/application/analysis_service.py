"""Job-analysis application use case."""

from ..infrastructure.llm.deepseek import DeepSeekProvider
from ..infrastructure.llm.parser import JobAnalysis, parse_analysis
from ..infrastructure.llm.provider import LLMProvider


class AnalysisService:
    """Coordinate evidence extraction and deterministic response building."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def analyze_job(
        self,
        job_title: str,
        job_description: str,
        candidate_profile: str,
    ) -> JobAnalysis:
        content = self.provider.analyze_job(job_title, job_description, candidate_profile)
        return parse_analysis(content)


def analyze_job(job_title: str, job_description: str, candidate_profile: str) -> JobAnalysis:
    """Analyze a job using the configured production provider."""
    return AnalysisService(DeepSeekProvider()).analyze_job(
        job_title,
        job_description,
        candidate_profile,
    )
