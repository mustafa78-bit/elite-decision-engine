from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


@dataclass
class User:
    username: str
    password_hash: str
    role: Role


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
