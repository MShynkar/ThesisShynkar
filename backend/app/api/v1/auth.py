"""Auth endpoints: register, login, refresh, me."""
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.rate_limit import limiter
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.schemas.user import LoginRequest, RefreshRequest, Token, UserOut, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(request: Request, data: UserRegister, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(data)
    await AuditRepository(db).log(
        action="user.register",
        user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.post("/login", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2-compatible login (form-encoded), so the Swagger UI works."""
    service = AuthService(db)
    user = await service.authenticate(form_data.username, form_data.password)
    tokens = service.issue_tokens(user)
    await AuditRepository(db).log(
        action="user.login",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return tokens


@router.post("/login/json", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login_json(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """JSON-body login convenience endpoint for the frontend."""
    service = AuthService(db)
    user = await service.authenticate(data.username, data.password)
    tokens = service.issue_tokens(user)
    await AuditRepository(db).log(
        action="user.login",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return tokens


@router.post("/refresh", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh(request: Request, data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).refresh(data.refresh_token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
