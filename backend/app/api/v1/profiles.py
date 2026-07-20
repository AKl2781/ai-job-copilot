"""Candidate profile endpoints."""

from fastapi import APIRouter, Depends, status

from ...application.crud_service import CrudService
from ...schemas import ProfileCreate, ProfileRead, ProfileUpdate
from ..dependencies import get_crud_service

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileRead)
def get_my_profile(service: CrudService = Depends(get_crud_service)) -> object:
    return service.get_profile()


@router.post("", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreate,
    service: CrudService = Depends(get_crud_service),
) -> object:
    return service.create_profile(payload)


@router.patch("/me", response_model=ProfileRead)
def update_my_profile(
    payload: ProfileUpdate,
    service: CrudService = Depends(get_crud_service),
) -> object:
    return service.update_profile(payload)
