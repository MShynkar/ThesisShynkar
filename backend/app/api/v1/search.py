"""Search/RAG endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.rate_limit import limiter
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_repo import AuditRepository, SearchHistoryRepository
from app.schemas.search import SearchHistoryOut, SearchRequest, SearchResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
@limiter.limit(settings.RATE_LIMIT_SEARCH)
async def search(
    request: Request,
    body: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    response = await RAGService(db).search(body, user)
    # Audit details include role and the source document titles so the audit log
    # answers "who saw what" without a separate join to documents/search_history.
    await AuditRepository(db).log(
        action="search.query",
        user_id=user.id,
        resource_type="search",
        details={
            "query": body.query[:500],
            "role": user.role,
            "result_count": len(response.sources),
            "source_titles": [s.document_title for s in response.sources],
            "elapsed_ms": response.elapsed_ms,
            "hybrid": body.hybrid,
        },
        ip_address=request.client.host if request.client else None,
    )
    return response


@router.get("/history", response_model=list[SearchHistoryOut])
async def search_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SearchHistoryRepository(db).list(user.id, skip=skip, limit=limit)


@router.delete("/history/{entry_id}", status_code=204)
async def delete_history_entry(
    entry_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await SearchHistoryRepository(db).delete(user.id, entry_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entry not found")
    return None
