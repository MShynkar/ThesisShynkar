"""Unit tests for AdminService (mocked UserRepository — no DB needed)."""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.permissions import Role
from app.models.user import User
from app.schemas.user import UserAdminCreate, UserUpdate


def _user(role: str = "admin") -> User:
    u = User()
    u.id = uuid4()
    u.email = f"{role}@test.com"
    u.username = role
    u.full_name = role.title()
    u.hashed_password = "x"
    u.role = role
    u.is_active = True
    return u


def _make_service():
    from app.services.admin_service import AdminService
    return AdminService(AsyncMock())


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------

class TestCreateUser:
    @pytest.mark.asyncio
    async def test_email_conflict_raises_409(self):
        svc = _make_service()
        data = UserAdminCreate(email="x@y.com", username="new", password="password1!", role=Role.USER)
        with patch.object(svc.users, "get_by_email", new_callable=AsyncMock, return_value=_user("user")):
            with pytest.raises(HTTPException) as exc:
                await svc.create_user(data)
        assert exc.value.status_code == 409
        assert "Email" in exc.value.detail

    @pytest.mark.asyncio
    async def test_username_conflict_raises_409(self):
        svc = _make_service()
        data = UserAdminCreate(email="x@y.com", username="taken", password="password1!", role=Role.USER)
        with (
            patch.object(svc.users, "get_by_email", new_callable=AsyncMock, return_value=None),
            patch.object(svc.users, "get_by_username", new_callable=AsyncMock, return_value=_user("user")),
        ):
            with pytest.raises(HTTPException) as exc:
                await svc.create_user(data)
        assert exc.value.status_code == 409
        assert "Username" in exc.value.detail

    @pytest.mark.asyncio
    async def test_success_hashes_password_and_persists_role(self):
        svc = _make_service()
        data = UserAdminCreate(
            email="new@x.com", username="newuser", password="password1!",
            full_name="New User", role=Role.MANAGER, is_active=True,
        )
        captured: list[User] = []

        async def _create(u):
            captured.append(u)
            return u

        with (
            patch.object(svc.users, "get_by_email", new_callable=AsyncMock, return_value=None),
            patch.object(svc.users, "get_by_username", new_callable=AsyncMock, return_value=None),
            patch.object(svc.users, "create", side_effect=_create),
        ):
            await svc.create_user(data)
        assert len(captured) == 1
        u = captured[0]
        assert u.email == "new@x.com"
        assert u.role == Role.MANAGER.value
        assert u.hashed_password != "password1!"     # actually hashed
        assert u.hashed_password.startswith("$2b$")  # bcrypt prefix


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------

class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_target_not_found_raises_404(self):
        svc = _make_service()
        with patch.object(svc.users, "get", new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc:
                await svc.update_user(uuid4(), UserUpdate(full_name="x"), _user("admin"))
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_admin_cannot_demote_themselves(self):
        svc = _make_service()
        actor = _user("admin")
        with patch.object(svc.users, "get", new_callable=AsyncMock, return_value=actor):
            with pytest.raises(HTTPException) as exc:
                await svc.update_user(actor.id, UserUpdate(role=Role.USER), actor)
        assert exc.value.status_code == 400
        assert "own role" in exc.value.detail

    @pytest.mark.asyncio
    async def test_admin_can_keep_own_role_admin(self):
        """Setting role=ADMIN on yourself is a no-op and must not raise."""
        svc = _make_service()
        actor = _user("admin")
        with (
            patch.object(svc.users, "get", new_callable=AsyncMock, return_value=actor),
            patch.object(svc.users, "update", new_callable=AsyncMock, return_value=actor),
        ):
            await svc.update_user(actor.id, UserUpdate(role=Role.ADMIN), actor)

    @pytest.mark.asyncio
    async def test_updates_other_user_role_and_active(self):
        svc = _make_service()
        actor = _user("admin")
        target = _user("user")
        with (
            patch.object(svc.users, "get", new_callable=AsyncMock, return_value=target),
            patch.object(svc.users, "update", new_callable=AsyncMock, side_effect=lambda u: u),
        ):
            result = await svc.update_user(
                target.id, UserUpdate(role=Role.MANAGER, is_active=False), actor
            )
        assert result.role == Role.MANAGER.value
        assert result.is_active is False


# ---------------------------------------------------------------------------
# delete_user
# ---------------------------------------------------------------------------

class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_cannot_delete_self(self):
        svc = _make_service()
        actor = _user("admin")
        with pytest.raises(HTTPException) as exc:
            await svc.delete_user(actor.id, actor)
        assert exc.value.status_code == 400
        assert "yourself" in exc.value.detail

    @pytest.mark.asyncio
    async def test_target_not_found_raises_404(self):
        svc = _make_service()
        actor = _user("admin")
        with patch.object(svc.users, "get", new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc:
                await svc.delete_user(uuid4(), actor)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_calls_repo(self):
        svc = _make_service()
        actor = _user("admin")
        target = _user("user")
        mock_delete = AsyncMock()
        with (
            patch.object(svc.users, "get", new_callable=AsyncMock, return_value=target),
            patch.object(svc.users, "delete", mock_delete),
        ):
            await svc.delete_user(target.id, actor)
        mock_delete.assert_awaited_once_with(target)
