"""FastAPI entry point for AI Job Copilot."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .application.analysis_service import analyze_job
from .infrastructure.llm.parser import JobAnalysis
from .infrastructure.llm.provider import LLMServiceError

APP_NAME = "AI Job Copilot API"

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Return basic service information."""
    return {"name": APP_NAME, "status": "running"}


@app.get("/health")
def read_health() -> dict[str, str]:
    """Return the service health status."""
    return {"status": "ok"}


class JobAnalysisRequest(BaseModel):
    """Input accepted by the job analysis endpoint."""

    job_title: str = Field(min_length=1, max_length=500)
    job_description: str = Field(min_length=1, max_length=8000)
    candidate_profile: str = Field(min_length=1, max_length=8000)

    @field_validator("job_title", "job_description", "candidate_profile")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("字段不能为空")
        return stripped


@app.post("/api/analyze-job", response_model=JobAnalysis)
def analyze_job_endpoint(payload: JobAnalysisRequest) -> JobAnalysis:
    """Analyze a job description through the configured LLM service."""
    try:
        return analyze_job(
            payload.job_title,
            payload.job_description,
            payload.candidate_profile,
        )
    except LLMServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.public_message,
        ) from exc
