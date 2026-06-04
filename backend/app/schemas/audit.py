"""Pydantic schemas for audit logs."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict
    ip_address: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int
