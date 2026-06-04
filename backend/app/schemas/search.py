"""Pydantic schemas for the search/RAG endpoints."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.4, ge=0.0, le=1.0)
    hybrid: bool = True
    generate_answer: bool = True
    categories: list[str] | None = None
    tags: list[str] | None = None


class Source(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_title: str
    chunk_index: int
    content: str
    similarity: float


class SearchResponse(BaseModel):
    query: str
    answer: str | None = None
    sources: list[Source]
    elapsed_ms: int


class SearchHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    query: str
    answer: str | None = None
    sources: list
    result_count: int
    created_at: datetime
