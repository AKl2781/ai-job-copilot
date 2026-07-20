"""Resume document management endpoints."""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from ...application.document_service import (
    DocumentProcessingError,
    DocumentService,
    DocumentTooLargeError,
    MAX_DOCUMENT_SIZE,
    UnsupportedDocumentTypeError,
)
from ...schemas import DocumentChunkPublic, DocumentDetailRead, DocumentListItem, DocumentRead
from ..dependencies import get_document_service

router = APIRouter(prefix="/documents", tags=["documents"])


async def _read_limited(file: UploadFile) -> bytes:
    contents = bytearray()
    while chunk := await file.read(1024 * 1024):
        contents.extend(chunk)
        if len(contents) > MAX_DOCUMENT_SIZE:
            raise DocumentTooLargeError("document must not exceed 10 MB")
    return bytes(contents)


@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    response: Response,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> object:
    """Store, extract, structure, and persist a PDF or DOCX resume."""
    try:
        contents = await _read_limited(file)
        result = service.upload(file.filename or "", contents)
        if not result.created:
            response.status_code = status.HTTP_200_OK
        return result.document
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except DocumentTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)) from exc
    finally:
        await file.close()


@router.get("", response_model=list[DocumentListItem])
def list_documents(service: DocumentService = Depends(get_document_service)) -> object:
    return service.list_documents()


@router.get("/{document_id}", response_model=DocumentDetailRead)
def get_document(
    document_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
) -> object:
    return service.get_document(document_id)


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkPublic])
def list_document_chunks(
    document_id: uuid.UUID,
    service: DocumentService = Depends(get_document_service),
) -> object:
    return service.list_chunks(document_id)
