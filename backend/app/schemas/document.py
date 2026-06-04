"""Pydantic schemas for documents and chunks."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.permissions import AccessLevel


class DocumentBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    access_level: AccessLevel = AccessLevel.INTERNAL
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    doc_metadata: dict = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    access_level: AccessLevel | None = None
    category: str | None = None
    tags: list[str] | None = None
    doc_metadata: dict | None = None


class DocumentOut(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    file_size: int
    mime_type: str
    owner_id: UUID
    status: str
    chunk_count: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentOut]
    total: int
    page: int
    page_size: int


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
