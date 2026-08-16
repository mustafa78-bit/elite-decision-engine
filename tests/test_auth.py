"""Tests for user registration and login."""

from auth.service import login_user, refresh_session, register_user, revoke_refresh_token


class TestRegister:
    def test_register_success(self, db_session):
        result = register_user("testuser", "test@example.com", "password123")
        assert result["success"] is True
        assert "token" in result
        assert "refresh_token" in result
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
        assert "refresh_token" in result

    def test_login_invalid_password(self, db_session):
        register_user("logintest2", "login2@example.com", "securepass")
        result = login_user("logintest2", "wrongpass")
        assert result["success"] is False

    def test_login_nonexistent_user(self, db_session):
        result = login_user("nobody", "password")
        assert result["success"] is False


class TestRefreshSession:
    def test_refresh_issues_new_access_and_refresh_token(self, db_session):
        register_result = register_user("refreshuser", "refresh@example.com", "password123")
        old_refresh_token = register_result["refresh_token"]

        result = refresh_session(old_refresh_token)

        assert result["success"] is True
        assert "token" in result
        # Random secrets.token_urlsafe() output -- unlike the JWT access
        # token (whose content can legitimately collide when issued within
        # the same second), this is guaranteed different every issuance.
        assert result["refresh_token"] != old_refresh_token
        assert result["user"]["username"] == "refreshuser"

    def test_rotation_revokes_the_presented_token(self, db_session):
        register_result = register_user("rotateuser", "rotate@example.com", "password123")
        old_refresh_token = register_result["refresh_token"]

        first = refresh_session(old_refresh_token)
        assert first["success"] is True

        # The old token was consumed by the rotation above -- presenting it
        # again must not work.
        second = refresh_session(old_refresh_token)
        assert second["success"] is False

    def test_reused_revoked_token_revokes_all_sessions(self, db_session):
        register_result = register_user("reuseuser", "reuse@example.com", "password123")
        original_refresh_token = register_result["refresh_token"]

        rotated = refresh_session(original_refresh_token)
        assert rotated["success"] is True
        new_refresh_token = rotated["refresh_token"]

        # Replaying the already-rotated-away original token is treated as a
        # compromise signal -- it must revoke every refresh token this user
        # currently holds, including the legitimately-rotated new one.
        reuse_result = refresh_session(original_refresh_token)
        assert reuse_result["success"] is False
        assert "revoked" in reuse_result["error"].lower()

        blocked = refresh_session(new_refresh_token)
        assert blocked["success"] is False

    def test_unknown_token_fails(self, db_session):
        result = refresh_session("this-token-was-never-issued")
        assert result["success"] is False
        assert "invalid" in result["error"].lower()

    def test_expired_token_fails(self, db_session, monkeypatch):
        # auth.service imports REFRESH_TOKEN_EXPIRE_DAYS via `from auth.jwt
        # import ...` -- a bound-at-import-time name, so the patch must
        # target auth.service's own namespace, not auth.jwt's.
        monkeypatch.setattr("auth.service.REFRESH_TOKEN_EXPIRE_DAYS", -1)
        register_result = register_user("expireduser", "expired@example.com", "password123")

        result = refresh_session(register_result["refresh_token"])
        assert result["success"] is False
        assert "expired" in result["error"].lower()


class TestRevokeRefreshToken:
    def test_revoke_prevents_future_refresh(self, db_session):
        register_result = register_user("logoutuser", "logout@example.com", "password123")
        token = register_result["refresh_token"]

        revoke_refresh_token(token)

        result = refresh_session(token)
        assert result["success"] is False

    def test_revoking_unknown_token_does_not_raise(self, db_session):
        revoke_refresh_token("never-issued-token")


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
