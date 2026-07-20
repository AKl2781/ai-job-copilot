"""Transactional CRUD use cases for profiles, jobs, and analyses."""

import uuid

from sqlalchemy.orm import Session

from ..infrastructure.database.models import Analysis, CandidateProfile, Job, User
from ..infrastructure.database.repositories import (
    AnalysisRepository,
    JobRepository,
    ProfileRepository,
    UserRepository,
)
from ..schemas import AnalysisCreate, JobCreate, ProfileCreate, ProfileUpdate

DEFAULT_USER_EMAIL = "local@ai-job-copilot.local"


class ResourceNotFoundError(RuntimeError):
    """A requested or associated resource is unavailable to the current user."""


class ResourceConflictError(RuntimeError):
    """Creating a resource would violate an application invariant."""


class CrudService:
    """Coordinate user-scoped persistence and transaction boundaries."""

    def __init__(self, session: Session, user_email: str) -> None:
        self.session = session
        self.user_email = user_email.strip().lower()
        self.users = UserRepository(session)
        self.profiles = ProfileRepository(session)
        self.jobs = JobRepository(session)
        self.analyses = AnalysisRepository(session)

    def _current_user(self) -> User:
        return self.users.get_or_create_by_email(self.user_email)

    def _commit(self, entity: object) -> None:
        self.session.commit()
        self.session.refresh(entity)

    def get_profile(self) -> CandidateProfile:
        user = self._current_user()
        profile = self.profiles.get_for_user(user.id)
        if profile is None:
            self.session.rollback()
            raise ResourceNotFoundError("profile not found")
        self.session.commit()
        return profile

    def create_profile(self, payload: ProfileCreate) -> CandidateProfile:
        user = self._current_user()
        if self.profiles.get_for_user(user.id) is not None:
            self.session.rollback()
            raise ResourceConflictError("profile already exists")
        profile = self.profiles.add(
            CandidateProfile(user_id=user.id, **payload.model_dump())
        )
        self._commit(profile)
        return profile

    def update_profile(self, payload: ProfileUpdate) -> CandidateProfile:
        user = self._current_user()
        profile = self.profiles.get_for_user(user.id)
        if profile is None:
            self.session.rollback()
            raise ResourceNotFoundError("profile not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        self._commit(profile)
        return profile

    def create_job(self, payload: JobCreate) -> Job:
        user = self._current_user()
        job = self.jobs.add(Job(user_id=user.id, **payload.model_dump()))
        self._commit(job)
        return job

    def list_jobs(self) -> list[Job]:
        user = self._current_user()
        jobs = self.jobs.list_for_user(user.id)
        self.session.commit()
        return jobs

    def get_job(self, job_id: uuid.UUID) -> Job:
        user = self._current_user()
        job = self.jobs.get_for_user(job_id, user.id)
        if job is None:
            self.session.rollback()
            raise ResourceNotFoundError("job not found")
        self.session.commit()
        return job

    def create_analysis(self, payload: AnalysisCreate) -> Analysis:
        user = self._current_user()
        if self.jobs.get_for_user(payload.job_id, user.id) is None:
            self.session.rollback()
            raise ResourceNotFoundError("job not found")
        profile = self.profiles.get_for_user(user.id)
        if profile is None or profile.id != payload.candidate_profile_id:
            self.session.rollback()
            raise ResourceNotFoundError("profile not found")
        analysis = self.analyses.add(
            Analysis(user_id=user.id, **payload.model_dump())
        )
        self._commit(analysis)
        return analysis

    def list_analyses(self) -> list[Analysis]:
        user = self._current_user()
        analyses = self.analyses.list_for_user(user.id)
        self.session.commit()
        return analyses
