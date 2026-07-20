"""Strongly typed contracts used by the Career Copilot workflow and tools."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from ...infrastructure.llm.parser import (
    ExtractedAnalysis,
    JobAnalysis,
    JobRequirements,
    ScoreBreakdown,
)
from ...schemas.analysis import AnalysisEvidence


class AgentRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentStepStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStepName(StrEnum):
    VALIDATE_INPUT = "validate_input"
    EXTRACT_JOB_REQUIREMENTS = "extract_job_requirements"
    RETRIEVE_CANDIDATE_EVIDENCE = "retrieve_candidate_evidence"
    CALCULATE_SCORE = "calculate_score"
    GENERATE_ANALYSIS = "generate_analysis"
    SAVE_RESULT = "save_result"
    END = "end"


class ValidatedAgentInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    job_title: str
    job_description: str
    candidate_profile_id: uuid.UUID
    candidate_name: str
    candidate_target_role: str | None = None
    candidate_summary: str | None = None
    candidate_skills: list[str] = Field(default_factory=list)


class RetrieveCandidateEvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    requirements: list[str]


class RetrieveCandidateEvidenceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    evidence: list[AnalysisEvidence] = Field(default_factory=list)


class CalculateMatchScoreInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    extracted_analysis: ExtractedAnalysis


class CalculateMatchScoreOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    matched_skills: list[str]
    partial_skills: list[str]
    missing_skills: list[str]
    unverified_skills: list[str]


class GenerateApplicationMaterialInput(BaseModel):
    """The first constrained generator produces the match report only."""

    model_config = ConfigDict(extra="forbid", strict=True)

    extracted_analysis: ExtractedAnalysis
    calculated_score: CalculateMatchScoreOutput


class GenerateApplicationMaterialOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    analysis: JobAnalysis


class SaveAnalysisResultInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    candidate_profile_id: uuid.UUID
    analysis: JobAnalysis
    evidence: list[AnalysisEvidence]


class SaveAnalysisResultOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    analysis_id: uuid.UUID


class AgentError(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    step: AgentStepName
    message: str


class AgentFinalResult(BaseModel):
    # Persisted JSON represents UUIDs as strings and is revalidated on read.
    model_config = ConfigDict(extra="forbid")

    analysis_id: uuid.UUID
    analysis: JobAnalysis
    evidence: list[AnalysisEvidence]


class AgentRunCreate(BaseModel):
    # JSON transports UUIDs as strings; keep the boundary closed while allowing that conversion.
    model_config = ConfigDict(extra="forbid")

    job_id: uuid.UUID


class AgentRunStarted(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    run_id: uuid.UUID
    status: AgentRunStatus


class AgentStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_name: AgentStepName
    status: AgentStepStatus
    input_summary: str | None
    output_summary: str | None
    duration_ms: int | None
    created_at: datetime


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    status: AgentRunStatus
    current_step: AgentStepName
    steps: list[AgentStepRead]
    result: AgentFinalResult | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
