"""Authentication service: register, login, refresh."""
from uuid import UUID

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Role
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import Token, UserRegister


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)

    async def register(self, data: UserRegister) -> User:
        if await self.users.get_by_email(data.email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
        if await self.users.get_by_username(data.username):
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")

        user = User(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=Role.USER.value,
            is_active=True,
        )
        return await self.users.create(user)

    async def authenticate(self, identifier: str, password: str) -> User:
        user = await self.users.get_by_identifier(identifier)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
        return user

    def issue_tokens(self, user: User) -> Token:
        return Token(
            access_token=create_access_token(str(user.id), role=user.role),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> Token:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
        if payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")

        user = await self.users.get(UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
        return self.issue_tokens(user)
