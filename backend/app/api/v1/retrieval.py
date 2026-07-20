"""Semantic resume retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from ...application.retrieval_service import RetrievalService
from ...infrastructure.embedding.provider import EmbeddingServiceError
from ...schemas import RetrievalSearchRequest, RetrievalSearchResult
from ..dependencies import get_retrieval_service

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=list[RetrievalSearchResult])
def search_resume_chunks(
    payload: RetrievalSearchRequest,
    service: RetrievalService = Depends(get_retrieval_service),
) -> object:
    try:
        return service.search(payload.query, payload.top_k)
    except EmbeddingServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.public_message) from exc
