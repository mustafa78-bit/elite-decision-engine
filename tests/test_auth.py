"""Tests for user registration and login."""

import pytest
from auth.service import register_user, login_user


class TestRegister:
    def test_register_success(self, db_session):
        result = register_user("testuser", "test@example.com", "password123")
        assert result["success"] is True
        assert "token" in result
        assert result["user"]["username"] == "testuser"
        assert result["user"]["email"] == "test@example.com"

    def test_register_duplicate_username(self, db_session):
        register_user("dupuser", "first@example.com", "password123")
        result = register_user("dupuser", "second@example.com", "password123")
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_register_duplicate_email(self, db_session):
        register_user("user1", "dup@example.com", "password123")
        result = register_user("user2", "dup@example.com", "password123")
        assert result["success"] is False
        assert "already exists" in result["error"]


class TestLogin:
    def test_login_success(self, db_session):
        register_user("logintest", "login@example.com", "securepass")
        result = login_user("logintest", "securepass")
        assert result["success"] is True
        assert "token" in result

    def test_login_invalid_password(self, db_session):
        register_user("logintest2", "login2@example.com", "securepass")
        result = login_user("logintest2", "wrongpass")
        assert result["success"] is False

    def test_login_nonexistent_user(self, db_session):
        result = login_user("nobody", "password")
        assert result["success"] is False


class TestJWT:
    def test_token_roundtrip(self):
        from auth.jwt import create_access_token, decode_access_token
        token = create_access_token({"sub": "1", "username": "test"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["username"] == "test"

    def test_invalid_token(self):
        from auth.jwt import decode_access_token
        assert decode_access_token("invalid.token.here") is None
