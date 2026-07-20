"""State carried through the fixed Career Copilot workflow."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from ...infrastructure.llm.parser import ExtractedAnalysis, JobAnalysis, JobRequirements
from ...schemas.analysis import AnalysisEvidence
from .schemas import (
    AgentError,
    AgentRunStatus,
    AgentStepName,
    CalculateMatchScoreOutput,
    ValidatedAgentInput,
)


class CareerCopilotState(BaseModel):
    """A bounded state model; arbitrary keys and untyped dictionaries are rejected."""

    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)

    run_id: uuid.UUID
    job_id: uuid.UUID
    user_id: uuid.UUID
    status: AgentRunStatus = AgentRunStatus.RUNNING
    current_step: AgentStepName = AgentStepName.VALIDATE_INPUT
    validated_input: ValidatedAgentInput | None = None
    job_requirements: JobRequirements | None = None
    retrieved_evidence: list[AnalysisEvidence] = Field(default_factory=list)
    extracted_analysis: ExtractedAnalysis | None = None
    calculated_score: CalculateMatchScoreOutput | None = None
    analysis_result: JobAnalysis | None = None
    analysis_id: uuid.UUID | None = None
    errors: list[AgentError] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
