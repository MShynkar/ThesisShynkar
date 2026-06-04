"""Unit tests for AuthService — реєстрація, логін, видача токенів, оновлення."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.security import decode_token, hash_password
from app.models.user import User


def _active_user(role: str = "user") -> User:
    u = User()
    u.id = uuid4()
    u.role = role
    u.is_active = True
    u.email = "test@example.com"
    u.username = "testuser"
    u.hashed_password = hash_password("correct-password")
    return u


class TestAuthenticate:
    @pytest.mark.asyncio
    async def test_success(self):
        from app.services.auth_service import AuthService

        svc = AuthService(AsyncMock())
        user = _active_user()
        with patch.object(svc.users, "get_by_identifier", new_callable=AsyncMock, return_value=user):
            result = await svc.authenticate("testuser", "correct-password")
        assert result.id == user.id

    @pytest.mark.asyncio
    async def test_wrong_password_raises_401(self):
        from fastapi import HTTPException
        from app.services.auth_service import AuthService

        svc = AuthService(AsyncMock())
        user = _active_user()
        with patch.object(svc.users, "get_by_identifier", new_callable=AsyncMock, return_value=user):
            with pytest.raises(HTTPException) as exc:
                await svc.authenticate("testuser", "wrong-password")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_unknown_user_raises_401(self):
        from fastapi import HTTPException
        from app.services.auth_service import AuthService

        svc = AuthService(AsyncMock())
        with patch.object(svc.users, "get_by_identifier", new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc:
                await svc.authenticate("nobody", "any-pass")
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_inactive_user_raises_403(self):
        from fastapi import HTTPException
        from app.services.auth_service import AuthService

        svc = AuthService(AsyncMock())
        user = _active_user()
        user.is_active = False
        with patch.object(svc.users, "get_by_identifier", new_callable=AsyncMock, return_value=user):
            with pytest.raises(HTTPException) as exc:
                await svc.authenticate("testuser", "correct-password")
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_login_by_email_works(self):
        """Логін можливий як за username, так і за email."""
        from app.services.auth_service import AuthService

        svc = AuthService(AsyncMock())
        user = _active_user()
        with patch.object(svc.users, "get_by_identifier", new_callable=AsyncMock, return_value=user):
            result = await svc.authenticate("test@example.com", "correct-password")
        assert result.id == user.id


class TestIssueTokens:
    def test_access_token_contains_role(self):
        from app.services.auth_service import AuthService

        svc = AuthService(AsyncMock())
        user = _active_user(role="manager")
        tokens = svc.issue_tokens(user)

        payload = decode_token(tokens.access_token)
        assert payload["role"] == "manager"
        assert payload["type"] == "access"
        assert payload["sub"] == str(user.id)

    def test_refresh_token_has_no_role(self):
        from app.services.auth_service import AuthService

        svc = AuthService(AsyncMock())
        tokens = svc.issue_tokens(_active_user())

        payload = decode_token(tokens.refresh_token)
        assert payload["type"] == "refresh"
        assert "role" not in payload

    def test_access_and_refresh_are_distinct(self):
        from app.services.auth_service import AuthService

        svc = AuthService(AsyncMock())
        tokens = svc.issue_tokens(_active_user())
        assert tokens.access_token != tokens.refresh_token


class TestRefresh:
    @pytest.mark.asyncio
    async def test_valid_refresh_issues_new_tokens(self):
        from app.services.auth_service import AuthService
        from app.core.security import create_refresh_token

        svc = AuthService(AsyncMock())
        user = _active_user()
        refresh_tok = create_refresh_token(str(user.id))

        with patch.object(svc.users, "get", new_callable=AsyncMock, return_value=user):
            tokens = await svc.refresh(refresh_tok)

        assert decode_token(tokens.access_token)["type"] == "access"

    @pytest.mark.asyncio
    async def test_access_token_used_as_refresh_raises_401(self):
        from fastapi import HTTPException
        from app.services.auth_service import AuthService
        from app.core.security import create_access_token

        svc = AuthService(AsyncMock())
        access_tok = create_access_token(str(uuid4()), role="user")

        with pytest.raises(HTTPException) as exc:
            await svc.refresh(access_tok)
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        from fastapi import HTTPException
        from app.services.auth_service import AuthService

        svc = AuthService(AsyncMock())
        with pytest.raises(HTTPException) as exc:
            await svc.refresh("not.a.token")
        assert exc.value.status_code == 401
