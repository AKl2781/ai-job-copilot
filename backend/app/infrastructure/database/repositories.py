"""SQLAlchemy repositories for versioned CRUD APIs."""

import math
import uuid

from sqlalchemy import Float, func, select
from sqlalchemy.orm import Session

from .models import (
    AgentRun, AgentStep, Analysis, CandidateProfile, Document, DocumentChunk, Job, User,
)


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

    def get_by_fingerprint_for_user(
        self, job_fingerprint: str, user_id: uuid.UUID
    ) -> Job | None:
        return self.session.scalar(
            select(Job).where(
                Job.job_fingerprint == job_fingerprint,
                Job.user_id == user_id,
            )
        )

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


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, document: Document) -> Document:
        self.session.add(document)
        self.session.flush()
        return document

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self.session.add_all(chunks)
        self.session.flush()

    def get_for_user(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> Document | None:
        return self.session.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
            )
        )

    def get_by_hash_for_user(self, file_hash: str, user_id: uuid.UUID) -> Document | None:
        return self.session.scalar(
            select(Document).where(
                Document.file_hash == file_hash,
                Document.user_id == user_id,
            )
        )

    def list_for_user_with_chunk_count(
        self, user_id: uuid.UUID
    ) -> list[tuple[Document, int]]:
        rows = self.session.execute(
            select(Document, func.count(DocumentChunk.id))
            .outerjoin(DocumentChunk)
            .where(Document.user_id == user_id)
            .group_by(Document.id)
            .order_by(Document.created_at.desc(), Document.id.desc())
        )
        return [(document, int(chunk_count)) for document, chunk_count in rows]

    def get_for_user_with_chunk_count(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[Document, int] | None:
        row = self.session.execute(
            select(Document, func.count(DocumentChunk.id))
            .outerjoin(DocumentChunk)
            .where(Document.id == document_id, Document.user_id == user_id)
            .group_by(Document.id)
        ).one_or_none()
        if row is None:
            return None
        return row[0], int(row[1])

    def list_chunks_for_document(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        return list(
            self.session.scalars(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index, DocumentChunk.id)
            )
        )


class RetrievalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        numerator = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def search_for_user(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        top_k: int,
    ) -> list[tuple[DocumentChunk, float]]:
        if self.session.bind is not None and self.session.bind.dialect.name == "postgresql":
            distance = DocumentChunk.embedding.op("<=>", return_type=Float)(query_embedding)
            rows = self.session.execute(
                select(DocumentChunk, (1.0 - distance).label("score"))
                .join(Document)
                .where(
                    Document.user_id == user_id,
                    Document.status == "ready",
                    DocumentChunk.embedding.is_not(None),
                )
                .order_by(distance)
                .limit(top_k)
            )
            return [(chunk, float(score)) for chunk, score in rows]

        chunks = list(
            self.session.scalars(
                select(DocumentChunk)
                .join(Document)
                .where(
                    Document.user_id == user_id,
                    Document.status == "ready",
                    DocumentChunk.embedding.is_not(None),
                )
            )
        )
        scored = [
            (
                chunk,
                self._cosine_similarity(
                    [float(value) for value in chunk.embedding or []],
                    query_embedding,
                ),
            )
            for chunk in chunks
            if chunk.embedding is not None and len(chunk.embedding) == len(query_embedding)
        ]
        return sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]


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
        evidence_json: list[dict[str, object]] | None = None,
    ) -> Analysis:
        analysis.status = status
        analysis.score = score
        analysis.result_json = result_json
        if evidence_json is not None:
            analysis.evidence_json = evidence_json
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


class AgentRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, run: AgentRun) -> AgentRun:
        self.session.add(run)
        self.session.flush()
        return run

    def get_for_user(self, run_id: uuid.UUID, user_id: uuid.UUID) -> AgentRun | None:
        return self.session.scalar(
            select(AgentRun).where(AgentRun.id == run_id, AgentRun.user_id == user_id)
        )

    def get_active_for_job(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> AgentRun | None:
        return self.session.scalar(
            select(AgentRun).where(
                AgentRun.user_id == user_id,
                AgentRun.job_id == job_id,
                AgentRun.status.in_(("pending", "running")),
            )
        )

    def add_step(self, step: AgentStep) -> AgentStep:
        self.session.add(step)
        self.session.flush()
        return step

    def get_step(self, run_id: uuid.UUID, step_name: str) -> AgentStep | None:
        return self.session.scalar(
            select(AgentStep).where(
                AgentStep.run_id == run_id,
                AgentStep.step_name == step_name,
            )
        )
