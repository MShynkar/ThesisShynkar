"""Pydantic schemas for user and auth."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.permissions import Role


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(UserCreate):
    """Public registration: role is forced to USER on the server side."""
    pass


class UserUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None
    role: Role | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: Role
    is_active: bool
    created_at: datetime


class UserAdminCreate(UserCreate):
    role: Role = Role.USER
    is_active: bool = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # user id
    role: str | None = None
    exp: int | None = None
    type: str | None = None


class UserListResponse(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class LoginRequest(BaseModel):
    username: str  # accepts username or email
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str
