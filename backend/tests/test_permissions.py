"""Unit tests for the role/access-level matrix."""
import pytest

from app.core.permissions import AccessLevel, Role, allowed_levels_for_role


def test_admin_sees_everything():
    levels = allowed_levels_for_role(Role.ADMIN)
    assert set(levels) == {l.value for l in AccessLevel}


def test_guest_sees_only_public():
    levels = allowed_levels_for_role(Role.GUEST)
    assert levels == [AccessLevel.PUBLIC.value]


def test_user_sees_public_and_internal():
    levels = allowed_levels_for_role(Role.USER)
    assert set(levels) == {AccessLevel.PUBLIC.value, AccessLevel.INTERNAL.value}


def test_manager_sees_up_to_confidential():
    levels = allowed_levels_for_role(Role.MANAGER)
    assert set(levels) == {
        AccessLevel.PUBLIC.value,
        AccessLevel.INTERNAL.value,
        AccessLevel.CONFIDENTIAL.value,
    }
    assert AccessLevel.RESTRICTED.value not in levels


def test_string_role_input():
    """Strings should be accepted and behave the same as enums."""
    assert allowed_levels_for_role("admin") == allowed_levels_for_role(Role.ADMIN)
