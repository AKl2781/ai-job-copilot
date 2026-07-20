"""Saved job endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from ...application.analysis_service import ApplicationAnalysisService
from ...application.crud_service import CrudService
from ...infrastructure.llm.provider import LLMServiceError
from ...schemas import JobAnalysisRead, JobCreate, JobRead
from ..dependencies import get_application_analysis_service, get_crud_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    service: CrudService = Depends(get_crud_service),
) -> object:
    return service.create_job(payload)


@router.get("", response_model=list[JobRead])
def list_jobs(service: CrudService = Depends(get_crud_service)) -> object:
    return service.list_jobs()


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: uuid.UUID,
    service: CrudService = Depends(get_crud_service),
) -> object:
    return service.get_job(job_id)


@router.post("/{job_id}/analyze", response_model=JobAnalysisRead)
def analyze_saved_job(
    job_id: uuid.UUID,
    service: ApplicationAnalysisService = Depends(get_application_analysis_service),
) -> object:
    try:
        return service.analyze_job(job_id)
    except LLMServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc
