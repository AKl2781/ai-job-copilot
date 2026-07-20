"""SQLAlchemy repositories for versioned CRUD APIs."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Analysis, CandidateProfile, Job, User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_by_email(self, email: str) -> User:
        user = self.session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email)
            self.session.add(user)
            self.session.flush()
        return user


class ProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_user(self, user_id: uuid.UUID) -> CandidateProfile | None:
        return self.session.scalar(
            select(CandidateProfile).where(CandidateProfile.user_id == user_id)
        )

    def add(self, profile: CandidateProfile) -> CandidateProfile:
        self.session.add(profile)
        self.session.flush()
        return profile


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, job: Job) -> Job:
        self.session.add(job)
        self.session.flush()
        return job

    def list_for_user(self, user_id: uuid.UUID) -> list[Job]:
        return list(
            self.session.scalars(
                select(Job)
                .where(Job.user_id == user_id)
                .order_by(Job.created_at.desc(), Job.id.desc())
            )
        )

    def get_for_user(self, job_id: uuid.UUID, user_id: uuid.UUID) -> Job | None:
        return self.session.scalar(
            select(Job).where(Job.id == job_id, Job.user_id == user_id)
        )


class AnalysisRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, analysis: Analysis) -> Analysis:
        self.session.add(analysis)
        self.session.flush()
        return analysis

    def set_result(
        self,
        analysis: Analysis,
        *,
        status: str,
        score: int | None,
        result_json: dict[str, object],
    ) -> Analysis:
        analysis.status = status
        analysis.score = score
        analysis.result_json = result_json
        self.session.flush()
        return analysis

    def list_for_user(self, user_id: uuid.UUID) -> list[Analysis]:
        return list(
            self.session.scalars(
                select(Analysis)
                .where(Analysis.user_id == user_id)
                .order_by(Analysis.created_at.desc(), Analysis.id.desc())
            )
        )
