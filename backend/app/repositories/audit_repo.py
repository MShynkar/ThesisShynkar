"""Data access for audit logs and search history."""
from uuid import UUID

from sqlalchemy import and_, delete as sql_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog, SearchHistory


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        action: str,
        user_id: UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list(
        self,
        user_id: UUID | None = None,
        action: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        stmt = select(AuditLog)
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        items = list((await self.session.execute(stmt)).scalars().all())

        count_stmt = select(func.count(AuditLog.id))
        if user_id is not None:
            count_stmt = count_stmt.where(AuditLog.user_id == user_id)
        if action:
            count_stmt = count_stmt.where(AuditLog.action == action)
        total = (await self.session.execute(count_stmt)).scalar_one()

        return items, total


class SearchHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        user_id: UUID,
        query: str,
        answer: str | None,
        sources: list,
    ) -> SearchHistory:
        entry = SearchHistory(
            user_id=user_id,
            query=query,
            answer=answer,
            sources=sources,
            result_count=len(sources),
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list(self, user_id: UUID, skip: int = 0, limit: int = 50) -> list[SearchHistory]:
        stmt = (
            select(SearchHistory)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, user_id: UUID, entry_id: UUID) -> bool:
        result = await self.session.execute(
            sql_delete(SearchHistory).where(
                and_(SearchHistory.id == entry_id, SearchHistory.user_id == user_id)
            )
        )
        return result.rowcount > 0
