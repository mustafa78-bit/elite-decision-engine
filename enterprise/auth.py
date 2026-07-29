import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import logging

import database
from database import User
from auth.jwt import create_access_token

logger = logging.getLogger(__name__)

LOCKOUT_DURATION_MINUTES = 15
MAX_FAILED_ATTEMPTS = 5

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def register_enterprise_user(username: str, email: str, password: str, role: str = "Viewer") -> dict:
    session = database.get_session()
    try:
        existing = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return {"success": False, "error": "Username or email already exists"}

        verification_token = secrets.token_hex(32)
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_verified=False,
            verification_token=verification_token,
            failed_login_attempts=0
        )
        session.add(user)
        session.commit()

        return {
            "success": True,
            "verification_token": verification_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_verified": user.is_verified
            }
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def verify_email(token: str) -> dict:
    session = database.get_session()
    try:
        user = session.query(User).filter(User.verification_token == token).first()
        if not user:
            return {"success": False, "error": "Invalid verification token"}

        user.is_verified = True
        user.verification_token = None
        session.commit()
        return {"success": True, "message": "Email verified successfully"}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def login_enterprise_user(username: str, password: str, user_agent: str = "", ip_address: str = "") -> dict:
    session = database.get_session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return {"success": False, "error": "Invalid username or password"}

        now = datetime.now(timezone.utc)

        # Check account lockout
        if user.locked_until:
            locked_until_utc = user.locked_until.replace(tzinfo=timezone.utc)
            if now < locked_until_utc:
                remaining = int((locked_until_utc - now).total_seconds())
                return {
                    "success": False,
                    "error": f"Account is locked. Please try again in {remaining} seconds.",
                    "is_locked": True
                }

        # Check password
        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                session.commit()
                return {
                    "success": False,
                    "error": f"Too many failed login attempts. Account locked for {LOCKOUT_DURATION_MINUTES} minutes.",
                    "is_locked": True
                }
            session.commit()
            return {"success": False, "error": "Invalid username or password"}

        # Verification check (simulated / required based on settings)
        # SPRINT 22: allow unverified login but flag it

        # Success: reset attempts
        user.failed_login_attempts = 0
        user.locked_until = None

        refresh_token = secrets.token_hex(64)
        user.refresh_token = refresh_token
        session.commit()

        access_token = create_access_token({
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        })

        # Record device session
        device_session = {
            "user_id": user.id,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "timestamp": now.isoformat()
        }

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "device_session": device_session,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_verified": user.is_verified
            }
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def refresh_access_token(refresh_token: str) -> dict:
    session = database.get_session()
    try:
        user = session.query(User).filter(User.refresh_token == refresh_token).first()
        if not user:
            return {"success": False, "error": "Invalid or expired refresh token"}

        # Issue new tokens (rotation)
        new_refresh_token = secrets.token_hex(64)
        user.refresh_token = new_refresh_token
        session.commit()

        access_token = create_access_token({
            "sub": str(user.id),
            "username": user.username,
            "role": user.role
        })

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": new_refresh_token
        }
    finally:
        session.close()

def recover_password_request(email: str) -> dict:
    session = database.get_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            # Avoid enumeration attacks: return generic success
            return {"success": True, "message": "Password recovery instructions sent if email exists"}

        # Generate a recovery token (stored in verification_token column for simplicity)
        token = secrets.token_hex(32)
        user.verification_token = f"recovery_{token}"
        session.commit()

        return {
            "success": True,
            "message": "Password recovery instructions sent if email exists",
            "recovery_token": token
        }
    finally:
        session.close()

def reset_password_with_token(token: str, new_password: str) -> dict:
    session = database.get_session()
    try:
        user = session.query(User).filter(User.verification_token == f"recovery_{token}").first()
        if not user:
            return {"success": False, "error": "Invalid or expired recovery token"}

        user.hashed_password = hash_password(new_password)
        user.verification_token = None
        session.commit()
        return {"success": True, "message": "Password reset successfully"}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()
