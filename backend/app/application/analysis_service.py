"""Job-analysis application use cases."""

import json
import os
import uuid

from sqlalchemy.orm import Session

from .crud_service import ResourceNotFoundError
from ..infrastructure.database.models import Analysis, CandidateProfile
from ..infrastructure.database.repositories import (
    AnalysisRepository,
    JobRepository,
    ProfileRepository,
    UserRepository,
)
from ..infrastructure.llm.deepseek import DeepSeekProvider
from ..infrastructure.llm.parser import JobAnalysis, parse_analysis
from ..infrastructure.llm.provider import LLMProvider, LLMServiceError

SCORING_VERSION = "deterministic-v1"
PROMPT_VERSION = "evidence-extraction-v1"


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


def _profile_text(profile: CandidateProfile) -> str:
    """Serialize the stored profile without inventing candidate evidence."""
    return json.dumps(
        {
            "name": profile.name,
            "target_role": profile.target_role,
            "summary": profile.summary,
            "skills": profile.skills,
        },
        ensure_ascii=False,
    )


class ApplicationAnalysisService:
    """Run and persist analysis for a user-owned saved job."""

    def __init__(
        self,
        session: Session,
        user_email: str,
        analyzer: AnalysisService | None = None,
    ) -> None:
        self.session = session
        self.user_email = user_email.strip().lower()
        self.analyzer = analyzer or AnalysisService(DeepSeekProvider())
        self.users = UserRepository(session)
        self.profiles = ProfileRepository(session)
        self.jobs = JobRepository(session)
        self.analyses = AnalysisRepository(session)

    def analyze_job(self, job_id: uuid.UUID) -> Analysis:
        user = self.users.get_or_create_by_email(self.user_email)
        job = self.jobs.get_for_user(job_id, user.id)
        if job is None:
            self.session.rollback()
            raise ResourceNotFoundError("job not found")

        profile = self.profiles.get_for_user(user.id)
        if profile is None:
            self.session.rollback()
            raise ResourceNotFoundError("profile not found")

        analysis = self.analyses.add(
            Analysis(
                user_id=user.id,
                job_id=job.id,
                candidate_profile_id=profile.id,
                status="pending",
                result_json={},
                scoring_version=SCORING_VERSION,
                prompt_version=PROMPT_VERSION,
                model_provider=os.getenv("LLM_PROVIDER", "deepseek").strip() or "deepseek",
                model_name=os.getenv("LLM_MODEL", "deepseek-chat").strip() or "deepseek-chat",
            )
        )
        self.session.commit()
        self.session.refresh(analysis)

        try:
            result = self.analyzer.analyze_job(
                job.title,
                job.description,
                _profile_text(profile),
            )
            self.analyses.set_result(
                analysis,
                status="completed",
                score=result.score,
                result_json=result.model_dump(mode="json"),
            )
            self.session.commit()
            self.session.refresh(analysis)
            return analysis
        except Exception as exc:
            self.session.rollback()
            failure_message = (
                exc.public_message
                if isinstance(exc, LLMServiceError)
                else "analysis failed"
            )
            self.analyses.set_result(
                analysis,
                status="failed",
                score=None,
                result_json={"error": failure_message},
            )
            self.session.commit()
            raise


def analyze_job(job_title: str, job_description: str, candidate_profile: str) -> JobAnalysis:
    """Analyze a job using the configured production provider."""
    return AnalysisService(DeepSeekProvider()).analyze_job(
        job_title,
        job_description,
        candidate_profile,
    )
