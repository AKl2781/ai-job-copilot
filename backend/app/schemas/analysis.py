"""Analysis request and response schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from ..infrastructure.llm.parser import JobAnalysis


class AnalysisCreate(BaseModel):
    """Persist an analysis associated with an owned job and profile."""

    job_id: uuid.UUID
    candidate_profile_id: uuid.UUID
    status: str = Field(default="pending", min_length=1, max_length=50)
    score: int | None = Field(default=None, ge=0, le=100)
    result_json: dict[str, Any] = Field(default_factory=dict)
    scoring_version: str | None = Field(default=None, max_length=100)
    prompt_version: str | None = Field(default=None, max_length=100)
    model_provider: str | None = Field(default=None, max_length=100)
    model_name: str | None = Field(default=None, max_length=200)

    @field_validator(
        "status",
        "scoring_version",
        "prompt_version",
        "model_provider",
        "model_name",
    )
    @classmethod
    def strip_text(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if info.field_name == "status" and not stripped:
            raise ValueError("status must not be blank")
        return stripped


class AnalysisRead(AnalysisCreate):
    """Persisted analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class JobAnalysisRead(AnalysisRead):
    """Completed saved-job analysis with a validated deterministic result."""

    result_json: JobAnalysis
