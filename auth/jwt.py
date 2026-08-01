from datetime import datetime, timedelta, timezone

import jwt

from config import JWT_SECRET

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not configured")

_SECRET_KEY: str = JWT_SECRET


def _get_secret() -> str:
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
