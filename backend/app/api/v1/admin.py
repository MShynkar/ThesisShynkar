"""Admin endpoints: user management, audit logs."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.schemas.audit import AuditLogListResponse
from app.schemas.user import UserAdminCreate, UserListResponse, UserOut, UserUpdate
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = await AdminService(db).list_users(skip=skip, limit=page_size)
    return UserListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    data: UserAdminCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService(db).create_user(data)


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AdminService(db).update_user(user_id, data, admin)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await AdminService(db).delete_user(user_id, admin)


@router.get("/audit", response_model=AuditLogListResponse)
async def list_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: UUID | None = None,
    action: str | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = await AuditRepository(db).list(
        user_id=user_id, action=action, skip=skip, limit=page_size
    )
    return AuditLogListResponse(items=items, total=total, page=page, page_size=page_size)
