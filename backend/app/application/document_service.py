"""Resume document upload, extraction, and chunk persistence workflow."""

from __future__ import annotations

import hashlib
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..infrastructure.database.models import Document, DocumentChunk, User
from ..infrastructure.database.repositories import DocumentRepository, UserRepository
from ..infrastructure.database.vector import BGE_M3_DIMENSION
from ..infrastructure.embedding.provider import EmbeddingProvider, EmbeddingResponseError
from .crud_service import ResourceNotFoundError
from .document_processing import chunk_resume_text, extract_docx_text, extract_pdf_text

MAX_DOCUMENT_SIZE = 10 * 1024 * 1024


@dataclass(frozen=True)
class DocumentSummary:
    id: uuid.UUID
    filename: str
    file_type: str
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DocumentUploadResult:
    document: Document
    created: bool


class UnsupportedDocumentTypeError(ValueError):
    """The uploaded file is not one of the supported resume formats."""


class DocumentProcessingError(RuntimeError):
    """The document could not be parsed into usable text chunks."""


class DocumentTooLargeError(ValueError):
    """The uploaded file exceeds the configured hard limit."""


def sanitize_filename(filename: str) -> str:
    """Return a safe cross-platform basename for an uploaded filename."""
    normalized = unicodedata.normalize("NFKC", filename).replace("\\", "/")
    basename = normalized.rsplit("/", 1)[-1].strip()
    basename = re.sub(r'[\x00-\x1f<>:"/\\|?*]', "_", basename).strip(" .")
    if not basename or basename in {".", ".."}:
        raise UnsupportedDocumentTypeError("a valid filename is required")
    if len(basename) > 500:
        raise UnsupportedDocumentTypeError("filename must not exceed 500 characters")
    return basename


class DocumentService:
    """Coordinate user-scoped document storage and database transactions."""

    SUPPORTED_TYPES = {"pdf", "docx"}

    def __init__(
        self,
        session: Session,
        user_email: str,
        storage_root: Path,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.session = session
        self.user_email = user_email.strip().lower()
        self.storage_root = storage_root.expanduser().resolve()
        self.embedding_provider = embedding_provider
        self.users = UserRepository(session)
        self.documents = DocumentRepository(session)

    def _current_user(self) -> User:
        return self.users.get_or_create_by_email(self.user_email)

    @staticmethod
    def _summary(document: Document, chunk_count: int) -> DocumentSummary:
        return DocumentSummary(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            status=document.status,
            chunk_count=chunk_count,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def upload(self, filename: str, data: bytes) -> DocumentUploadResult:
        safe_filename = sanitize_filename(filename)
        file_type = Path(safe_filename).suffix.lower().lstrip(".")
        if file_type not in self.SUPPORTED_TYPES:
            raise UnsupportedDocumentTypeError("only PDF and DOCX files are supported")
        if not data:
            raise DocumentProcessingError("uploaded document is empty")
        if len(data) > MAX_DOCUMENT_SIZE:
            raise DocumentTooLargeError("document must not exceed 10 MB")

        user = self._current_user()
        file_hash = hashlib.sha256(data).hexdigest()
        existing = self.documents.get_by_hash_for_user(file_hash, user.id)
        if existing is not None:
            self.session.commit()
            return DocumentUploadResult(document=existing, created=False)

        document_id = uuid.uuid4()
        destination = (
            self.storage_root / str(user.id) / str(document_id) / safe_filename
        ).resolve()
        if not destination.is_relative_to(self.storage_root):
            raise UnsupportedDocumentTypeError("invalid filename")
        document = self.documents.add(
            Document(
                id=document_id,
                user_id=user.id,
                filename=safe_filename,
                file_type=file_type,
                storage_path=str(destination),
                file_hash=file_hash,
                status="processing",
            )
        )
        self.session.commit()

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            text = extract_pdf_text(data) if file_type == "pdf" else extract_docx_text(data)
            chunks = chunk_resume_text(text)
            if not chunks:
                raise DocumentProcessingError("document contains no extractable resume text")
            if self.embedding_provider.dimension != BGE_M3_DIMENSION:
                raise EmbeddingResponseError(
                    "embedding provider dimension does not match the database schema"
                )
            embeddings = self.embedding_provider.embed_texts(
                [chunk.content for chunk in chunks]
            )
            if len(embeddings) != len(chunks):
                raise EmbeddingResponseError(
                    "embedding response count does not match document chunks"
                )
            chunk_models = [
                DocumentChunk(
                    document_id=document.id,
                    content=chunk.content,
                    section=chunk.section,
                    chunk_index=index,
                    embedding=embeddings[index],
                )
                for index, chunk in enumerate(chunks)
            ]
            self.documents.add_chunks(chunk_models)
            document.status = "ready"
            self.session.commit()
            self.session.refresh(document)
            return DocumentUploadResult(document=document, created=True)
        except Exception as exc:
            self.session.rollback()
            failed_document = self.session.get(Document, document_id)
            if failed_document is not None:
                failed_document.status = "failed"
                self.session.commit()
            if isinstance(exc, DocumentProcessingError):
                raise
            raise DocumentProcessingError("failed to process uploaded document") from exc

    def list_documents(self) -> list[DocumentSummary]:
        user = self._current_user()
        documents = [
            self._summary(document, chunk_count)
            for document, chunk_count in self.documents.list_for_user_with_chunk_count(user.id)
        ]
        self.session.commit()
        return documents

    def get_document(self, document_id: uuid.UUID) -> DocumentSummary:
        user = self._current_user()
        result = self.documents.get_for_user_with_chunk_count(document_id, user.id)
        if result is None:
            self.session.rollback()
            raise ResourceNotFoundError("document not found")
        self.session.commit()
        return self._summary(*result)

    def list_chunks(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        user = self._current_user()
        if self.documents.get_for_user(document_id, user.id) is None:
            self.session.rollback()
            raise ResourceNotFoundError("document not found")
        chunks = self.documents.list_chunks_for_document(document_id)
        self.session.commit()
        return chunks
