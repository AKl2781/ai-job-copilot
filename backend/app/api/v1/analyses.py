"""Persisted analysis endpoints."""

from fastapi import APIRouter, Depends, status

from ...application.crud_service import CrudService
from ...schemas import AnalysisCreate, AnalysisRead
from ..dependencies import get_crud_service

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
def create_analysis(
    payload: AnalysisCreate,
    service: CrudService = Depends(get_crud_service),
) -> object:
    return service.create_analysis(payload)


@router.get("", response_model=list[AnalysisRead])
def list_analyses(service: CrudService = Depends(get_crud_service)) -> object:
    return service.list_analyses()
