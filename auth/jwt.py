import hashlib
import secrets
from datetime import UTC, datetime, timedelta, timezone

import jwt

from config import JWT_SECRET

ALGORITHM = "HS256"
# Short-lived on purpose -- long-lived sessions are now the REFRESH_TOKEN's
# job (see below), not the access token's. Previously this was 24h with no
# separate refresh credential at all, meaning a stolen access token could
# renew itself indefinitely via /auth/refresh (see api/routes/auth.py).
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not configured")

_SECRET_KEY: str = JWT_SECRET


def _get_secret() -> str:
    return _SECRET_KEY


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _get_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


def generate_refresh_token() -> str:
    """A cryptographically random opaque string -- deliberately not a JWT.
    The server is the only party that ever needs to look this up (by its
    hash, see hash_refresh_token()), so there's no need for it to be
    self-describing/decodable the way the access token is."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hex digest -- only the hash is ever persisted (database.py's
    RefreshToken.token_hash), matching this app's existing password-hashing
    hygiene. Deterministic (unlike bcrypt) is fine and required here: it's
    used as an exact-match DB lookup key, not verified against a single
    known plaintext the way a login password is."""
    return hashlib.sha256(token.encode()).hexdigest()
