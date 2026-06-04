"""
RBAC tests — доводять, що фільтрація за роллю працює коректно
на рівні сервісного шару і що репозиторій отримує правильний allowed_levels.

Жодна зовнішня залежність (БД, Ollama) не потрібна: всі репозиторії замінені мок-ами.
"""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.permissions import AccessLevel, Role
from app.models.document import Document
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(role: str) -> User:
    u = User()
    u.id = uuid4()
    u.role = role
    u.is_active = True
    u.email = f"{role}@test.com"
    u.username = role
    u.hashed_password = "x"
    return u


def _doc(access_level: str) -> Document:
    d = Document()
    d.id = uuid4()
    d.access_level = access_level
    d.owner_id = uuid4()
    d.status = "ready"
    d.title = f"Doc [{access_level}]"
    d.filename = "test.txt"
    d.file_path = "/tmp/test.txt"
    d.file_size = 100
    d.mime_type = "text/plain"
    d.chunk_count = 1
    d.tags = []
    d.doc_metadata = {}
    d.category = None
    d.error_message = None
    return d


# ---------------------------------------------------------------------------
# DocumentService.get_for_user — перевірка доступу до одного документа
# ---------------------------------------------------------------------------

class TestDocumentServiceAccess:
    """
    Тести для DocumentService.get_for_user() після впровадження SQL pre-filter (C3).

    Архітектура: allowed_levels передаються в DocumentRepository.get(), де SQL
    фільтрує рядки. Якщо документ не проходить фільтр — повертається None → 404.
    Це безпечніше, ніж 403 (не розкриває існування документа).

    Тести перевіряють:
    1. Що репозиторій отримує правильний allowed_levels для кожної ролі.
    2. Що None від репозиторію (SQL відфільтрував) → 404.
    3. Що дозволений документ повертається без помилки.
    """

    @pytest.mark.asyncio
    async def test_guest_repo_called_with_public_only(self):
        """get() повинен отримати allowed_levels=['public'] для гостя."""
        from app.services.document_service import DocumentService

        svc = DocumentService(AsyncMock())
        doc = _doc(AccessLevel.PUBLIC.value)
        mock_get = AsyncMock(return_value=doc)
        with patch.object(svc.docs, "get", mock_get):
            await svc.get_for_user(doc.id, _user(Role.GUEST.value))
        mock_get.assert_called_once_with(doc.id, allowed_levels=[AccessLevel.PUBLIC.value])

    @pytest.mark.asyncio
    async def test_user_repo_called_with_public_and_internal(self):
        from app.services.document_service import DocumentService

        svc = DocumentService(AsyncMock())
        doc = _doc(AccessLevel.INTERNAL.value)
        mock_get = AsyncMock(return_value=doc)
        with patch.object(svc.docs, "get", mock_get):
            await svc.get_for_user(doc.id, _user(Role.USER.value))
        _, kwargs = mock_get.call_args
        assert set(kwargs["allowed_levels"]) == {
            AccessLevel.PUBLIC.value, AccessLevel.INTERNAL.value
        }

    @pytest.mark.asyncio
    async def test_admin_repo_called_with_all_levels(self):
        from app.services.document_service import DocumentService

        svc = DocumentService(AsyncMock())
        doc = _doc(AccessLevel.RESTRICTED.value)
        mock_get = AsyncMock(return_value=doc)
        with patch.object(svc.docs, "get", mock_get):
            await svc.get_for_user(doc.id, _user(Role.ADMIN.value))
        _, kwargs = mock_get.call_args
        assert set(kwargs["allowed_levels"]) == {lvl.value for lvl in AccessLevel}

    @pytest.mark.asyncio
    async def test_sql_filtered_doc_raises_404(self):
        """
        Коли SQL відфільтрував рядок (None), сервіс повертає 404.
        Це імітує ситуацію, коли гість намагається отримати internal документ.
        """
        from fastapi import HTTPException
        from app.services.document_service import DocumentService

        svc = DocumentService(AsyncMock())
        with patch.object(svc.docs, "get", new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc:
                await svc.get_for_user(uuid4(), _user(Role.GUEST.value))
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_allowed_doc_returned_successfully(self):
        from app.services.document_service import DocumentService

        svc = DocumentService(AsyncMock())
        doc = _doc(AccessLevel.PUBLIC.value)
        with patch.object(svc.docs, "get", new_callable=AsyncMock, return_value=doc):
            result = await svc.get_for_user(doc.id, _user(Role.GUEST.value))
        assert result.access_level == AccessLevel.PUBLIC.value

    @pytest.mark.asyncio
    async def test_nonexistent_document_raises_404(self):
        from fastapi import HTTPException
        from app.services.document_service import DocumentService

        svc = DocumentService(AsyncMock())
        with patch.object(svc.docs, "get", new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc:
                await svc.get_for_user(uuid4(), _user(Role.ADMIN.value))
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# RAGService.search — перевірка, що allowed_levels передається правильно
# ---------------------------------------------------------------------------

class TestRAGServiceAllowedLevels:
    """
    Ключовий тест для дипломної роботи:
    доводить, що ChunkRepository отримує ТІЛЬКИ ті рівні,
    які дозволені для ролі користувача.
    """

    async def _run_search_and_capture_levels(self, role: str) -> list[str]:
        from app.services.rag_service import RAGService
        from app.schemas.search import SearchRequest

        svc = RAGService(AsyncMock())
        req = SearchRequest(query="test query", generate_answer=False, hybrid=False)

        captured: list[str] = []

        async def _mock_semantic(**kwargs):
            captured.extend(kwargs.get("allowed_levels", []))
            return []

        with (
            patch.object(svc.chunks, "semantic_search", side_effect=_mock_semantic),
            patch.object(svc.ollama, "embed", new_callable=AsyncMock, return_value=[0.0] * 768),
            patch.object(svc.history, "add", new_callable=AsyncMock),
        ):
            await svc.search(req, _user(role))

        return captured

    @pytest.mark.asyncio
    async def test_guest_receives_only_public(self):
        levels = await self._run_search_and_capture_levels(Role.GUEST.value)
        assert levels == [AccessLevel.PUBLIC.value]
        assert AccessLevel.INTERNAL.value not in levels
        assert AccessLevel.CONFIDENTIAL.value not in levels
        assert AccessLevel.RESTRICTED.value not in levels

    @pytest.mark.asyncio
    async def test_user_receives_public_and_internal(self):
        levels = await self._run_search_and_capture_levels(Role.USER.value)
        assert set(levels) == {AccessLevel.PUBLIC.value, AccessLevel.INTERNAL.value}
        assert AccessLevel.CONFIDENTIAL.value not in levels

    @pytest.mark.asyncio
    async def test_manager_excludes_restricted(self):
        levels = await self._run_search_and_capture_levels(Role.MANAGER.value)
        assert AccessLevel.RESTRICTED.value not in levels
        assert AccessLevel.CONFIDENTIAL.value in levels

    @pytest.mark.asyncio
    async def test_admin_receives_all_levels(self):
        levels = await self._run_search_and_capture_levels(Role.ADMIN.value)
        all_values = {lvl.value for lvl in AccessLevel}
        assert set(levels) == all_values

    @pytest.mark.asyncio
    async def test_guest_hybrid_search_also_filtered(self):
        """hybrid=True повинен так само обмежувати allowed_levels."""
        from app.services.rag_service import RAGService
        from app.schemas.search import SearchRequest

        svc = RAGService(AsyncMock())
        req = SearchRequest(query="test", generate_answer=False, hybrid=True)

        captured: list[str] = []

        async def _mock_hybrid(**kwargs):
            captured.extend(kwargs.get("allowed_levels", []))
            return []

        with (
            patch.object(svc.chunks, "hybrid_search", side_effect=_mock_hybrid),
            patch.object(svc.ollama, "embed", new_callable=AsyncMock, return_value=[0.0] * 768),
            patch.object(svc.history, "add", new_callable=AsyncMock),
        ):
            await svc.search(req, _user(Role.GUEST.value))

        assert captured == [AccessLevel.PUBLIC.value]


# ---------------------------------------------------------------------------
# DocumentService.upload — заборона upload з access_level вище ролі
# ---------------------------------------------------------------------------

class TestDocumentServiceUploadAccessLevel:
    """Юзер не може завантажити документ з рівнем доступу вище своєї ролі."""

    @pytest.mark.asyncio
    async def test_user_cannot_upload_confidential(self):
        from fastapi import HTTPException, UploadFile
        from io import BytesIO
        from app.services.document_service import DocumentService
        from app.schemas.document import DocumentCreate

        svc = DocumentService(AsyncMock())
        file = AsyncMock(spec=UploadFile)
        file.filename = "doc.txt"
        file.content_type = "text/plain"
        file.read = AsyncMock(side_effect=[b"content", b""])

        meta = DocumentCreate(title="T", access_level=AccessLevel.CONFIDENTIAL)

        with pytest.raises(HTTPException) as exc:
            await svc.upload(file, meta, _user(Role.USER.value))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_user_cannot_upload_restricted(self):
        from fastapi import HTTPException, UploadFile
        from app.services.document_service import DocumentService
        from app.schemas.document import DocumentCreate

        svc = DocumentService(AsyncMock())
        file = AsyncMock(spec=UploadFile)
        file.filename = "doc.txt"
        file.content_type = "text/plain"
        file.read = AsyncMock(side_effect=[b"content", b""])

        meta = DocumentCreate(title="T", access_level=AccessLevel.RESTRICTED)

        with pytest.raises(HTTPException) as exc:
            await svc.upload(file, meta, _user(Role.USER.value))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_guest_cannot_upload_anything(self):
        from fastapi import HTTPException, UploadFile
        from app.services.document_service import DocumentService
        from app.schemas.document import DocumentCreate

        svc = DocumentService(AsyncMock())
        file = AsyncMock(spec=UploadFile)
        file.filename = "doc.txt"
        file.content_type = "text/plain"
        file.read = AsyncMock(side_effect=[b"content", b""])

        meta = DocumentCreate(title="T", access_level=AccessLevel.PUBLIC)

        with pytest.raises(HTTPException) as exc:
            await svc.upload(file, meta, _user(Role.GUEST.value))
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_manager_cannot_upload_restricted(self):
        from fastapi import HTTPException, UploadFile
        from app.services.document_service import DocumentService
        from app.schemas.document import DocumentCreate

        svc = DocumentService(AsyncMock())
        file = AsyncMock(spec=UploadFile)
        file.filename = "doc.txt"
        file.content_type = "text/plain"
        file.read = AsyncMock(side_effect=[b"content", b""])

        meta = DocumentCreate(title="T", access_level=AccessLevel.RESTRICTED)

        with pytest.raises(HTTPException) as exc:
            await svc.upload(file, meta, _user(Role.MANAGER.value))
        assert exc.value.status_code == 403
