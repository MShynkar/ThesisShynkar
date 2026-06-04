"""Document service: handles uploads, processing pipeline, and metadata."""
import os
import uuid as uuid_lib
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.permissions import AccessLevel, Role, allowed_levels_for_role
from app.models.document import Chunk, Document
from app.models.user import User
from app.repositories.document_repo import ChunkRepository, DocumentRepository
from app.schemas.document import DocumentCreate, DocumentUpdate
from app.services.chunking import chunk_text
from app.services.ollama_client import OllamaClient
from app.services.text_extraction import extract_text

logger = get_logger(__name__)


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.docs = DocumentRepository(session)
        self.chunks = ChunkRepository(session)

    # ---- Upload --------------------------------------------------------

    async def upload(
        self,
        file: UploadFile,
        meta: DocumentCreate,
        owner: User,
    ) -> Document:
        # Гості не можуть завантажувати документи
        if owner.role == Role.GUEST.value:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Guests cannot upload documents",
            )
        # Заборонити призначати access_level, який перевищує права ролі
        allowed_upload_levels = allowed_levels_for_role(owner.role)
        if meta.access_level.value not in allowed_upload_levels:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Role '{owner.role}' cannot assign access_level '{meta.access_level.value}'",
            )

        ext = Path(file.filename or "").suffix.lower().lstrip(".")
        if ext not in settings.allowed_extensions:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Unsupported extension '.{ext}'. Allowed: {settings.allowed_extensions}",
            )

        # Save the file to disk
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        stored_name = f"{uuid_lib.uuid4()}.{ext}"
        stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)

        size = 0
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        with open(stored_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):  # 1 MB
                size += len(chunk)
                if size > max_bytes:
                    out.close()
                    os.remove(stored_path)
                    raise HTTPException(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit",
                    )
                out.write(chunk)

        doc = Document(
            title=meta.title,
            filename=file.filename or stored_name,
            file_path=stored_path,
            file_size=size,
            mime_type=file.content_type or "application/octet-stream",
            owner_id=owner.id,
            access_level=meta.access_level.value,
            category=meta.category,
            tags=meta.tags,
            doc_metadata=meta.doc_metadata,
            status="pending",
        )
        return await self.docs.create(doc)

    # ---- Processing ----------------------------------------------------

    async def process(self, document_id: UUID) -> None:
        """
        Background-task entrypoint. Orchestrates extract → chunk → embed → persist
        and records the outcome (ready/failed) on the document row.
        """
        doc = await self.docs.get(document_id)
        if not doc:
            logger.error("process_doc_not_found", document_id=str(document_id))
            return

        doc.status = "processing"
        await self.docs.update(doc)

        try:
            pieces = self._extract_and_chunk(doc.file_path)
            embeddings = await self._embed_chunks(pieces)
            await self._persist_chunks(doc, pieces, embeddings)
            await self._mark_ready(doc, len(pieces))
            logger.info("document_processed", document_id=str(doc.id), chunks=len(pieces))
        except Exception as e:
            logger.exception("document_processing_failed", document_id=str(doc.id))
            await self._mark_failed(doc, str(e))

    # ---- Processing helpers --------------------------------------------

    @staticmethod
    def _extract_and_chunk(file_path: str) -> list[str]:
        """Pull text from disk and split into chunks. Raises ValueError on empty input."""
        text = extract_text(file_path)
        if not text.strip():
            raise ValueError("No extractable text found in document")
        pieces = chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        if not pieces:
            raise ValueError("Chunking produced no chunks")
        return pieces

    @staticmethod
    async def _embed_chunks(pieces: list[str]) -> list[list[float]]:
        """Compute embeddings for every chunk via the Ollama client."""
        return await OllamaClient().embed_batch(pieces)

    async def _persist_chunks(
        self,
        doc: Document,
        pieces: list[str],
        embeddings: list[list[float]],
    ) -> None:
        """Insert chunks (with denormalized access_level) and refresh the tsvector column."""
        chunk_rows = [
            Chunk(
                document_id=doc.id,
                chunk_index=i,
                content=piece,
                embedding=emb,
                access_level=doc.access_level,
                token_count=len(piece.split()),
            )
            for i, (piece, emb) in enumerate(zip(pieces, embeddings))
        ]
        await self.chunks.bulk_create(chunk_rows)
        await self.session.execute(
            sql_text(
                "UPDATE chunks SET content_tsv = to_tsvector('english', content) "
                "WHERE document_id = :doc_id"
            ),
            {"doc_id": str(doc.id)},
        )

    async def _mark_ready(self, doc: Document, chunk_count: int) -> None:
        doc.chunk_count = chunk_count
        doc.status = "ready"
        doc.error_message = None
        await self.docs.update(doc)
        await self.session.commit()

    async def _mark_failed(self, doc: Document, error: str) -> None:
        doc.status = "failed"
        doc.error_message = error[:1000]
        await self.docs.update(doc)
        await self.session.commit()

    # ---- CRUD ----------------------------------------------------------

    async def list_for_user(
        self,
        user: User,
        category: str | None = None,
        tag: str | None = None,
        owned_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Document], int]:
        levels = allowed_levels_for_role(user.role)
        owner_id = user.id if owned_only else None
        return await self.docs.list(
            allowed_levels=levels,
            owner_id=owner_id,
            category=category,
            tag=tag,
            skip=skip,
            limit=limit,
        )

    async def get_for_user(self, document_id: UUID, user: User) -> Document:
        levels = allowed_levels_for_role(user.role)
        doc = await self.docs.get(document_id, allowed_levels=levels)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        return doc

    async def update(self, document_id: UUID, data: DocumentUpdate, user: User) -> Document:
        # Read-RBAC pre-check: if the user can't see the document, they can't edit it either
        # (404 rather than 403 — don't reveal that the document exists).
        levels = allowed_levels_for_role(user.role)
        doc = await self.docs.get(document_id, allowed_levels=levels)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        # Among visible documents: only the owner or an admin/manager can edit.
        if doc.owner_id != user.id and user.role not in (Role.ADMIN.value, Role.MANAGER.value):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot edit this document")

        update_data = data.model_dump(exclude_unset=True)
        if "access_level" in update_data and update_data["access_level"] is not None:
            update_data["access_level"] = AccessLevel(update_data["access_level"]).value
        for k, v in update_data.items():
            setattr(doc, k, v)
        updated = await self.docs.update(doc)

        # Keep the denormalized chunk-level access_level in sync with the document
        if "access_level" in update_data and update_data["access_level"] is not None:
            await self.session.execute(
                sql_text(
                    "UPDATE chunks SET access_level = :lvl WHERE document_id = :doc_id"
                ),
                {"lvl": update_data["access_level"], "doc_id": str(doc.id)},
            )
        return updated

    async def delete(self, document_id: UUID, user: User) -> None:
        # Read-RBAC pre-check (same rationale as update()): hide existence from
        # roles that cannot see the document.
        levels = allowed_levels_for_role(user.role)
        doc = await self.docs.get(document_id, allowed_levels=levels)
        if not doc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        if doc.owner_id != user.id and user.role != Role.ADMIN.value:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot delete this document")

        # Best-effort file cleanup
        try:
            if doc.file_path and os.path.exists(doc.file_path):
                os.remove(doc.file_path)
        except OSError as e:
            logger.warning("file_cleanup_failed", path=doc.file_path, error=str(e))

        await self.docs.delete(doc)
