import os
from datetime import datetime, timedelta, timezone

import jwt

from config import API_ENV

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

_SECRET_KEY: str | None = None


def _get_secret() -> str:
    global _SECRET_KEY
    if _SECRET_KEY is not None:
        return _SECRET_KEY
    value = os.getenv("JWT_SECRET", "")
    if not value:
        if API_ENV == "production":
            raise RuntimeError("JWT_SECRET is required in production mode")
        value = "dev-secret-change-in-production"
    _SECRET_KEY = value
    return _SECRET_KEY


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _get_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
