"""Independent nodes for the deterministic Career Copilot graph."""

from __future__ import annotations

import json
from collections.abc import Callable

from ...infrastructure.llm.parser import ExtractedAnalysis
from .schemas import (
    CalculateMatchScoreInput,
    CalculateMatchScoreOutput,
    GenerateApplicationMaterialInput,
    GenerateApplicationMaterialOutput,
    RetrieveCandidateEvidenceInput,
    RetrieveCandidateEvidenceOutput,
    SaveAnalysisResultInput,
    SaveAnalysisResultOutput,
    ValidatedAgentInput,
)
from .state import CareerCopilotState
from .tools import ToolRegistry


def _profile_text(value: ValidatedAgentInput, evidence: RetrieveCandidateEvidenceOutput | None = None) -> str:
    return json.dumps({
        "name": value.candidate_name,
        "target_role": value.candidate_target_role,
        "summary": value.candidate_summary,
        "skills": value.candidate_skills,
        "retrieved_resume_evidence": [
            item.model_dump(mode="json") for item in (evidence.evidence if evidence else [])
        ],
    }, ensure_ascii=False)


def validate_input(
    state: CareerCopilotState,
    loader: Callable[[CareerCopilotState], ValidatedAgentInput],
) -> CareerCopilotState:
    state.validated_input = loader(state)
    return state


def extract_job_requirements(
    state: CareerCopilotState,
    extractor: Callable[[str, str, str], ExtractedAnalysis],
) -> CareerCopilotState:
    value = state.validated_input
    if value is None:
        raise RuntimeError("validated input is missing")
    extracted = extractor(value.job_title, value.job_description, _profile_text(value))
    state.extracted_analysis = extracted
    state.job_requirements = extracted.job_requirements
    return state


def retrieve_candidate_evidence(state: CareerCopilotState, tools: ToolRegistry) -> CareerCopilotState:
    requirements = state.job_requirements
    if requirements is None:
        raise RuntimeError("job requirements are missing")
    ordered = (
        requirements.core_skills + requirements.preferred_skills
        + requirements.project_requirements + requirements.education_requirements
        + requirements.experience_requirements
    )
    unique = list(dict.fromkeys(item.strip() for item in ordered if item.strip()))[:20]
    output = tools.invoke(
        "retrieve_candidate_evidence",
        RetrieveCandidateEvidenceInput(requirements=unique),
        RetrieveCandidateEvidenceOutput,
    )
    state.retrieved_evidence = output.evidence
    return state


def calculate_score(
    state: CareerCopilotState,
    extractor: Callable[[str, str, str], ExtractedAnalysis],
    tools: ToolRegistry,
) -> CareerCopilotState:
    value = state.validated_input
    if value is None:
        raise RuntimeError("validated input is missing")
    evidence = RetrieveCandidateEvidenceOutput(evidence=state.retrieved_evidence)
    extracted = extractor(value.job_title, value.job_description, _profile_text(value, evidence))
    state.extracted_analysis = extracted
    state.job_requirements = extracted.job_requirements
    state.calculated_score = tools.invoke(
        "calculate_match_score",
        CalculateMatchScoreInput(extracted_analysis=extracted),
        CalculateMatchScoreOutput,
    )
    return state


def generate_analysis(state: CareerCopilotState, tools: ToolRegistry) -> CareerCopilotState:
    if state.extracted_analysis is None or state.calculated_score is None:
        raise RuntimeError("scored analysis input is missing")
    output = tools.invoke(
        "generate_application_material",
        GenerateApplicationMaterialInput(
            extracted_analysis=state.extracted_analysis,
            calculated_score=state.calculated_score,
        ),
        GenerateApplicationMaterialOutput,
    )
    state.analysis_result = output.analysis
    return state


def save_result(state: CareerCopilotState, tools: ToolRegistry) -> CareerCopilotState:
    value = state.validated_input
    if value is None or state.analysis_result is None:
        raise RuntimeError("completed analysis input is missing")
    output = tools.invoke(
        "save_analysis_result",
        SaveAnalysisResultInput(
            run_id=state.run_id,
            user_id=state.user_id,
            job_id=state.job_id,
            candidate_profile_id=value.candidate_profile_id,
            analysis=state.analysis_result,
            evidence=state.retrieved_evidence,
        ),
        SaveAnalysisResultOutput,
    )
    state.analysis_id = output.analysis_id
    return state
