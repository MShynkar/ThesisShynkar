"""Document endpoints: list, upload, get, update, delete."""
import json
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.rate_limit import limiter
from app.repositories.document_repo import ChunkRepository
from app.core.permissions import AccessLevel
from app.db.session import AsyncSessionLocal, get_db
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.schemas.document import (
    DocumentCreate,
    DocumentListResponse,
    DocumentOut,
    DocumentUpdate,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


async def _process_in_background(document_id: UUID) -> None:
    """Process a document in a fresh DB session (background tasks don't share request session)."""
    async with AsyncSessionLocal() as session:
        service = DocumentService(session)
        await service.process(document_id)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    tag: str | None = None,
    owned_only: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    items, total = await DocumentService(db).list_for_user(
        user=user,
        category=category,
        tag=tag,
        owned_only=owned_only,
        skip=skip,
        limit=page_size,
    )
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=DocumentOut, status_code=201)
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    access_level: AccessLevel = Form(AccessLevel.INTERNAL),
    category: str | None = Form(None),
    tags: str = Form("[]"),
    doc_metadata: str = Form("{}"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a new document. Tags and metadata are JSON-encoded form strings
    because multipart forms don't natively support nested types.
    """
    try:
        parsed_tags = json.loads(tags) if tags else []
        if not isinstance(parsed_tags, list):
            raise ValueError("tags must be a JSON array")
        parsed_metadata = json.loads(doc_metadata) if doc_metadata else {}
        if not isinstance(parsed_metadata, dict):
            raise ValueError("doc_metadata must be a JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid form data: {e}")

    meta = DocumentCreate(
        title=title,
        access_level=access_level,
        category=category,
        tags=parsed_tags,
        doc_metadata=parsed_metadata,
    )
    service = DocumentService(db)
    doc = await service.upload(file, meta, user)
    await AuditRepository(db).log(
        action="document.upload",
        user_id=user.id,
        resource_type="document",
        resource_id=str(doc.id),
        details={"title": doc.title, "size": doc.file_size},
        ip_address=request.client.host if request.client else None,
    )
    # The DB session commits when the request finishes (see get_db).
    # Schedule processing only after that commit succeeds.
    background_tasks.add_task(_process_in_background, doc.id)
    return doc


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await DocumentService(db).get_for_user(document_id, user)
    await AuditRepository(db).log(
        action="document.view",
        user_id=user.id,
        resource_type="document",
        resource_id=str(doc.id),
        ip_address=request.client.host if request.client else None,
    )
    return doc


@router.patch("/{document_id}", response_model=DocumentOut)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await DocumentService(db).update(document_id, data, user)
    await AuditRepository(db).log(
        action="document.update",
        user_id=user.id,
        resource_type="document",
        resource_id=str(doc.id),
        details=data.model_dump(exclude_unset=True, mode="json"),
        ip_address=request.client.host if request.client else None,
    )
    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await DocumentService(db).delete(document_id, user)
    await AuditRepository(db).log(
        action="document.delete",
        user_id=user.id,
        resource_type="document",
        resource_id=str(document_id),
        ip_address=request.client.host if request.client else None,
    )
    return None


@router.post("/{document_id}/reprocess", response_model=DocumentOut)
async def reprocess_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-run extraction + embedding (useful after config changes or failures)."""
    doc = await DocumentService(db).get_for_user(document_id, user)
    # Clear existing chunks
    await ChunkRepository(db).delete_by_document(doc.id)
    doc.chunk_count = 0
    doc.status = "pending"
    doc.error_message = None
    await db.flush()
    background_tasks.add_task(_process_in_background, doc.id)
    return doc
