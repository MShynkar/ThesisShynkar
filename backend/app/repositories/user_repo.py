"""Data access for User."""
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_identifier(self, identifier: str) -> User | None:
        """Look up by email or username (used by login)."""
        result = await self.session.execute(
            select(User).where(or_(User.email == identifier, User.username == identifier))
        )
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        # Single round-trip: window function returns total alongside each row.
        total_col = func.count(User.id).over().label("total")
        stmt = (
            select(User, total_col)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        items = [r[0] for r in rows]
        total = rows[0][1] if rows else 0
        return items, total

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User) -> User:
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()
