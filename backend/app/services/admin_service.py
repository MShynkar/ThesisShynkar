"""Admin service: user management."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Role
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserAdminCreate, UserUpdate


class AdminService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)

    async def list_users(self, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        return await self.users.list(skip=skip, limit=limit)

    async def create_user(self, data: UserAdminCreate) -> User:
        if await self.users.get_by_email(data.email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
        if await self.users.get_by_username(data.username):
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
        user = User(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role.value,
            is_active=data.is_active,
        )
        return await self.users.create(user)

    async def update_user(self, user_id: UUID, data: UserUpdate, actor: User) -> User:
        user = await self.users.get(user_id)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        update = data.model_dump(exclude_unset=True)
        # Prevent an admin from de-admining themselves (locks them out)
        if user.id == actor.id and "role" in update and update["role"] != Role.ADMIN:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot change your own role")

        if "role" in update and update["role"] is not None:
            update["role"] = Role(update["role"]).value
        for k, v in update.items():
            setattr(user, k, v)
        return await self.users.update(user)

    async def delete_user(self, user_id: UUID, actor: User) -> None:
        if user_id == actor.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete yourself")
        user = await self.users.get(user_id)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        await self.users.delete(user)
