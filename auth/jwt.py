from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv(
    "AUTH_SECRET_KEY",
    "dev-secret-key-do-not-use-in-production",
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4()), "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4()), "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
        )
        if payload.get("type") != "access":
            logger.warning("Token type is not access")
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Access token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid access token: %s", e)
        return None


def verify_refresh_token(token: str) -> Optional[dict[str, Any]]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
        )
        if payload.get("type") != "refresh":
            logger.warning("Token type is not refresh")
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Refresh token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid refresh token: %s", e)
        return None
