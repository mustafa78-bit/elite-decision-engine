from datetime import UTC, datetime, timedelta

import bcrypt

import database
from auth.jwt import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from database import RefreshToken, User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _issue_refresh_token(session, user_id: int) -> str:
    """Create and persist a new refresh token for user_id, returning the
    raw (unhashed) value -- the only time it's ever available in plaintext.
    """
    raw_token = generate_refresh_token()
    session.add(RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    session.commit()
    return raw_token


def register_user(username: str, email: str, password: str) -> dict:
    session = database.get_session()
    try:
        existing = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return {"success": False, "error": "Username or email already exists"}

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
        )
        session.add(user)
        session.commit()

        token = create_access_token({"sub": str(user.id), "username": username})
        refresh_token = _issue_refresh_token(session, user.id)
        return {
            "success": True,
            "token": token,
            "refresh_token": refresh_token,
            "user": {"id": user.id, "username": username, "email": email},
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()


def login_user(username: str, password: str) -> dict:
    session = database.get_session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return {"success": False, "error": "Invalid username or password"}

        if not verify_password(password, user.hashed_password):
            return {"success": False, "error": "Invalid username or password"}

        token = create_access_token({"sub": str(user.id), "username": user.username})
        refresh_token = _issue_refresh_token(session, user.id)
        return {
            "success": True,
            "token": token,
            "refresh_token": refresh_token,
            "user": {"id": user.id, "username": user.username, "email": user.email},
        }
    finally:
        session.close()


def refresh_session(raw_refresh_token: str) -> dict:
    """Redeem a refresh token for a new access token + a rotated refresh
    token. The presented token is always revoked as part of this call
    (whether it turns out valid or not) -- rotation only issues a fresh
    replacement when it was.

    Reuse detection: a refresh token is only ever valid to redeem once. If
    the presented (hashed) token matches a row that's already revoked, that
    means either a legitimate prior rotation already consumed it, or an
    attacker replayed a stolen token after the real client already rotated
    past it -- either way, this token must never grant access again, and
    since we can't tell those two cases apart, treat it as a compromise
    signal and revoke every refresh token this user currently holds,
    forcing every session to re-authenticate.
    """
    session = database.get_session()
    try:
        token_hash = hash_refresh_token(raw_refresh_token)
        record = session.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

        if record is None:
            return {"success": False, "error": "Invalid refresh token"}

        if record.revoked_at is not None:
            session.query(RefreshToken).filter(
                RefreshToken.user_id == record.user_id,
                RefreshToken.revoked_at.is_(None),
            ).update({"revoked_at": datetime.now(UTC)})
            session.commit()
            return {"success": False, "error": "Refresh token already used -- all sessions revoked"}

        now = datetime.now(UTC)
        expires_at = record.expires_at if record.expires_at.tzinfo else record.expires_at.replace(tzinfo=UTC)
        if expires_at < now:
            return {"success": False, "error": "Refresh token expired"}

        user = session.query(User).filter(User.id == record.user_id).first()
        if user is None:
            return {"success": False, "error": "User not found"}

        record.revoked_at = now
        session.commit()

        new_access_token = create_access_token({"sub": str(user.id), "username": user.username})
        new_refresh_token = _issue_refresh_token(session, user.id)
        return {
            "success": True,
            "token": new_access_token,
            "refresh_token": new_refresh_token,
            "user": {"id": user.id, "username": user.username, "email": user.email},
        }
    finally:
        session.close()


def revoke_refresh_token(raw_refresh_token: str) -> None:
    """Best-effort logout: revoke one refresh token. Silently no-ops on an
    already-invalid/unknown token -- logging out is idempotent from the
    client's perspective, there's nothing meaningful to report back."""
    session = database.get_session()
    try:
        token_hash = hash_refresh_token(raw_refresh_token)
        session.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        ).update({"revoked_at": datetime.now(UTC)})
        session.commit()
    finally:
        session.close()
