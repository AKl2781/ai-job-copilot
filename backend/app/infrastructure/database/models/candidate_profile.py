"""Candidate profile persistence model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, JSON_TYPE, TimestampMixin

if TYPE_CHECKING:
    from .analysis import Analysis
    from .user import User


class CandidateProfile(TimestampMixin, Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSON_TYPE, default=list, nullable=False)

    user: Mapped["User"] = relationship(back_populates="candidate_profiles")
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="candidate_profile",
        cascade="all, delete-orphan",
    )
