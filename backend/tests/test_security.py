"""Unit tests for password hashing and JWT token handling."""
import time

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_round_trip():
    hashed = hash_password("super-secret-123")
    assert verify_password("super-secret-123", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_round_trip():
    token = create_access_token("user-id-1", role="admin")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_refresh_token_type():
    token = create_refresh_token("user-id-1")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-1"
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    with pytest.raises(JWTError):
        decode_token("not.a.token")


def test_tokens_are_distinct():
    access = create_access_token("u")
    refresh = create_refresh_token("u")
    assert access != refresh
    assert decode_token(access)["type"] == "access"
    assert decode_token(refresh)["type"] == "refresh"
