"""User persistence model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, TimestampMixin

if TYPE_CHECKING:
    from .analysis import Analysis
    from .candidate_profile import CandidateProfile
    from .job import Job


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)

    candidate_profiles: Mapped[list["CandidateProfile"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[list["Job"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
