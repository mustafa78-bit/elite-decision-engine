from __future__ import annotations

import hashlib
import logging
from typing import Optional

from auth.jwt import create_access_token, create_refresh_token, verify_refresh_token
from auth.models import LoginRequest, Role, TokenResponse, User

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


class AuthService:
    def __init__(self) -> None:
        self._users: dict[str, User] = {
            "admin": User(
                username="admin",
                password_hash=_hash_password("admin"),
                role=Role.ADMIN,
            ),
            "operator": User(
                username="operator",
                password_hash=_hash_password("operator"),
                role=Role.OPERATOR,
            ),
            "viewer": User(
                username="viewer",
                password_hash=_hash_password("viewer"),
                role=Role.VIEWER,
            ),
        }

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self._users.get(username)
        if user is None:
            return None
        if not _verify_password(password, user.password_hash):
            return None
        return user

    def create_tokens(self, user: User) -> TokenResponse:
        payload = {"sub": user.username, "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(payload),
            refresh_token=create_refresh_token(payload),
        )

    def refresh_access_token(self, refresh_token_str: str) -> Optional[TokenResponse]:
        payload = verify_refresh_token(refresh_token_str)
        if payload is None:
            return None
        username = payload.get("sub")
        if username is None or username not in self._users:
            return None
        user = self._users[username]
        return self.create_tokens(user)

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username)
