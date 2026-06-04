"""Router-level unit tests via FastAPI TestClient with dependency overrides.

The DB session, current user, and service classes are mocked so these tests
cover routing, schema validation, and dependency wiring without needing a real
DB or Ollama. End-to-end behaviour against the live stack is covered by
test_rbac_integration.py.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.rate_limit import limiter
from app.db.session import get_db
from app.main import app
from app.models.user import User

# Disable the per-IP rate limiter during unit tests so 10+ /login calls don't 429.
limiter.enabled = False


def _user(role: str = "admin") -> User:
    u = User()
    u.id = uuid4()
    u.email = f"{role}@test.com"
    u.username = role
    u.full_name = role.title()
    u.hashed_password = "x"
    u.role = role
    u.is_active = True
    u.created_at = datetime.now(timezone.utc)
    return u


@pytest.fixture
def client_as(monkeypatch):
    """Return a factory that builds a TestClient with get_current_user pinned
    to the given role (or None for an unauthenticated client)."""
    def _factory(role: str | None = "admin"):
        async def _db():
            yield AsyncMock()
        app.dependency_overrides[get_db] = _db
        if role is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            user = _user(role)
            async def _user_dep():
                return user
            app.dependency_overrides[get_current_user] = _user_dep
        return TestClient(app)
    yield _factory
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Health / root
# ---------------------------------------------------------------------------

class TestHealthRoot:
    def test_root_returns_metadata(self, client_as):
        r = client_as(None).get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["name"] and body["api"].startswith("/api/v1")

    def test_app_health_unauthenticated(self, client_as):
        r = client_as(None).get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_v1_health_reports_components(self, client_as):
        # Patch OllamaClient.health so we don't need a real Ollama server.
        with patch("app.api.v1.health.OllamaClient") as MockClient:
            MockClient.return_value.health = AsyncMock(return_value=True)
            r = client_as("admin").get("/api/v1/health")
        assert r.status_code == 200
        body = r.json()
        assert body["components"]["ollama"] == "ok"
        assert "database" in body["components"]

    def test_v1_health_marks_ollama_unreachable(self, client_as):
        with patch("app.api.v1.health.OllamaClient") as MockClient:
            MockClient.return_value.health = AsyncMock(return_value=False)
            r = client_as("admin").get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["components"]["ollama"] == "unreachable"


# ---------------------------------------------------------------------------
# Auth router
# ---------------------------------------------------------------------------

class TestAuthRouter:
    def test_login_success_returns_tokens(self, client_as):
        c = client_as(None)
        user = _user("admin")
        with (
            patch("app.api.v1.auth.AuthService") as MockSvc,
            patch("app.api.v1.auth.AuditRepository") as MockAudit,
        ):
            MockSvc.return_value.authenticate = AsyncMock(return_value=user)
            MockSvc.return_value.issue_tokens = lambda u: {
                "access_token": "a", "refresh_token": "r", "token_type": "bearer"
            }
            MockAudit.return_value.log = AsyncMock()
            r = c.post("/api/v1/auth/login/json",
                       json={"username": "admin", "password": "p"})
        assert r.status_code == 200
        assert r.json()["access_token"] == "a"

    def test_login_missing_fields_422(self, client_as):
        r = client_as(None).post("/api/v1/auth/login/json", json={"username": "x"})
        assert r.status_code == 422

    def test_login_wrong_password_propagates_401(self, client_as):
        from fastapi import HTTPException, status as st
        with patch("app.api.v1.auth.AuthService") as MockSvc:
            MockSvc.return_value.authenticate = AsyncMock(
                side_effect=HTTPException(st.HTTP_401_UNAUTHORIZED, "Bad credentials")
            )
            r = client_as(None).post("/api/v1/auth/login/json",
                                     json={"username": "x", "password": "y"})
        assert r.status_code == 401

    def test_me_returns_current_user(self, client_as):
        r = client_as("manager").get("/api/v1/auth/me")
        assert r.status_code == 200
        assert r.json()["role"] == "manager"


# ---------------------------------------------------------------------------
# Documents router
# ---------------------------------------------------------------------------

class TestDocumentsRouter:
    def test_list_documents_dispatches_to_service(self, client_as):
        with patch("app.api.v1.documents.DocumentService") as MockSvc:
            MockSvc.return_value.list_for_user = AsyncMock(return_value=([], 0))
            r = client_as("user").get("/api/v1/documents")
        assert r.status_code == 200
        body = r.json()
        assert body["items"] == [] and body["total"] == 0

    def test_upload_invalid_tags_json_400(self, client_as):
        c = client_as("user")
        r = c.post(
            "/api/v1/documents",
            files={"file": ("x.txt", b"hi", "text/plain")},
            data={"title": "T", "access_level": "public", "tags": "not-json"},
        )
        assert r.status_code == 400
        assert "Invalid form data" in r.json()["detail"]

    def test_upload_tags_must_be_array_400(self, client_as):
        c = client_as("user")
        r = c.post(
            "/api/v1/documents",
            files={"file": ("x.txt", b"hi", "text/plain")},
            data={"title": "T", "access_level": "public", "tags": "{\"not\":\"a list\"}"},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Admin router — admin-only guard
# ---------------------------------------------------------------------------

class TestAdminRouter:
    def test_non_admin_cannot_list_users(self, client_as):
        r = client_as("user").get("/api/v1/admin/users")
        assert r.status_code == 403

    def test_admin_can_list_users(self, client_as):
        with patch("app.api.v1.admin.AdminService") as MockSvc:
            MockSvc.return_value.list_users = AsyncMock(return_value=([], 0))
            r = client_as("admin").get("/api/v1/admin/users")
        assert r.status_code == 200
        assert r.json() == {"items": [], "total": 0, "page": 1, "page_size": 50}

    def test_admin_create_user_dispatches(self, client_as):
        new = _user("manager")
        with patch("app.api.v1.admin.AdminService") as MockSvc:
            MockSvc.return_value.create_user = AsyncMock(return_value=new)
            r = client_as("admin").post("/api/v1/admin/users", json={
                "email": "a@b.com", "username": "newuser", "password": "password1!",
                "role": "manager",
            })
        assert r.status_code == 201
        assert r.json()["username"] == "manager"

    def test_pagination_clamped_by_query_params(self, client_as):
        # page_size > 200 should fail validation
        r = client_as("admin").get("/api/v1/admin/users?page_size=999")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Search router — schema validation
# ---------------------------------------------------------------------------

class TestSearchRouter:
    def test_empty_query_422(self, client_as):
        r = client_as("user").post("/api/v1/search", json={"query": ""})
        assert r.status_code == 422

    def test_too_long_query_422(self, client_as):
        r = client_as("user").post("/api/v1/search", json={"query": "a" * 2001})
        assert r.status_code == 422

    def test_top_k_out_of_range_422(self, client_as):
        r = client_as("user").post("/api/v1/search",
                                   json={"query": "ok", "top_k": 100})
        assert r.status_code == 422

    def test_search_dispatches_to_rag_service(self, client_as):
        from app.schemas.search import SearchResponse
        fake = SearchResponse(query="q", answer="a", sources=[], elapsed_ms=1)
        with (
            patch("app.api.v1.search.RAGService") as MockSvc,
            patch("app.api.v1.search.AuditRepository") as MockAudit,
        ):
            MockSvc.return_value.search = AsyncMock(return_value=fake)
            MockAudit.return_value.log = AsyncMock()
            r = client_as("user").post("/api/v1/search", json={"query": "q"})
        assert r.status_code == 200
        assert r.json()["query"] == "q"
