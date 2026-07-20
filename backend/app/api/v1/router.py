"""Aggregate version 1 API routers."""

from fastapi import APIRouter

from .analyses import router as analyses_router
from .documents import router as documents_router
from .jobs import router as jobs_router
from .profiles import router as profiles_router
from .retrieval import router as retrieval_router

router = APIRouter(prefix="/api/v1")
router.include_router(profiles_router)
router.include_router(jobs_router)
router.include_router(analyses_router)
router.include_router(documents_router)
router.include_router(retrieval_router)
