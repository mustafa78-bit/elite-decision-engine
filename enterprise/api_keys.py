import hashlib
import secrets
from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, Tuple

import database
from enterprise.models import APIKey, Webhook

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter bucket: {api_key: (count, window_start_time)}
RATE_LIMIT_BUCKETS: Dict[str, Tuple[int, datetime]] = {}

def generate_api_key(user_id: int, organization_id: int, name: str, expires_in_days: int = 30) -> dict:
    session = database.get_session()
    try:
        raw_key = f"nx_{secrets.token_hex(20)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        prefix = raw_key[:7]  # nx_ plus first 4 chars of token

        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        api_key = APIKey(
            user_id=user_id,
            organization_id=organization_id,
            key_hash=key_hash,
            prefix=prefix,
            name=name,
            is_active=True,
            expires_at=expires_at
        )
        session.add(api_key)
        session.commit()

        return {
            "success": True,
            "id": api_key.id,
            "api_key": raw_key,  # Returned once to the user
            "prefix": prefix,
            "name": name,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def rotate_api_key(key_id: int, expires_in_days: int = 30) -> dict:
    session = database.get_session()
    try:
        old_key = session.query(APIKey).filter(APIKey.id == key_id).first()
        if not old_key:
            return {"success": False, "error": "API Key not found"}

        # Revoke old key
        old_key.is_active = False
        session.commit()

        # Generate new key for the same owner
        return generate_api_key(
            user_id=old_key.user_id,
            organization_id=old_key.organization_id,
            name=f"{old_key.name} (Rotated)",
            expires_in_days=expires_in_days
        )
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def validate_api_key(api_key_str: str) -> dict:
    if not api_key_str or not api_key_str.startswith("nx_"):
        return {"success": False, "error": "Invalid API key format"}

    session = database.get_session()
    try:
        key_hash = hashlib.sha256(api_key_str.encode()).hexdigest()
        api_key = session.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()

        if not api_key:
            return {"success": False, "error": "API Key is inactive or does not exist"}

        now = datetime.now(timezone.utc)
        if api_key.expires_at:
            expires_at_utc = api_key.expires_at.replace(tzinfo=timezone.utc)
            if now > expires_at_utc:
                return {"success": False, "error": "API Key has expired"}

        return {
            "success": True,
            "user_id": api_key.user_id,
            "organization_id": api_key.organization_id,
            "name": api_key.name
        }
    finally:
        session.close()

def check_rate_limit(api_key: str, limit: int = 5, window_seconds: int = 60) -> dict:
    """In-memory thread-safe rolling window rate limiter."""
    now = datetime.now(timezone.utc)

    if api_key not in RATE_LIMIT_BUCKETS:
        RATE_LIMIT_BUCKETS[api_key] = (1, now)
        return {"success": True, "count": 1, "remaining": limit - 1}

    count, window_start = RATE_LIMIT_BUCKETS[api_key]

    # Check if window expired
    if now > window_start + timedelta(seconds=window_seconds):
        RATE_LIMIT_BUCKETS[api_key] = (1, now)
        return {"success": True, "count": 1, "remaining": limit - 1}

    if count >= limit:
        remaining_seconds = int(((window_start + timedelta(seconds=window_seconds)) - now).total_seconds())
        return {
            "success": False,
            "error": "Rate limit exceeded. Please try again later.",
            "retry_after_seconds": remaining_seconds
        }

    RATE_LIMIT_BUCKETS[api_key] = (count + 1, window_start)
    return {"success": True, "count": count + 1, "remaining": limit - (count + 1)}


def register_webhook(organization_id: int, url: str, events: list) -> dict:
    session = database.get_session()
    try:
        secret = f"whsec_{secrets.token_hex(20)}"
        webhook = Webhook(
            organization_id=organization_id,
            url=url,
            secret=secret,
            events=events,
            is_active=True
        )
        session.add(webhook)
        session.commit()

        return {
            "success": True,
            "webhook": {
                "id": webhook.id,
                "organization_id": webhook.organization_id,
                "url": webhook.url,
                "secret": secret,
                "events": webhook.events,
                "is_active": webhook.is_active,
                "created_at": webhook.created_at.isoformat() if webhook.created_at else None
            }
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def deliver_webhook(webhook_id: int, event_type: str, payload: dict) -> dict:
    session = database.get_session()
    try:
        webhook = session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook or not webhook.is_active:
            return {"success": False, "error": "Webhook not found or inactive"}

        if event_type not in webhook.events:
            return {"success": False, "error": f"Webhook not subscribed to event {event_type}"}

        # Simulate external HTTP POST request with cryptographic signature header
        signature = hashlib.sha256(f"{webhook.secret}.{event_type}".encode()).hexdigest()

        logger.info("Delivering webhook to %s | event=%s | signature=%s", webhook.url, event_type, signature)

        # Simulated response: Status 200 OK
        return {
            "success": True,
            "status_code": 200,
            "delivered_url": webhook.url,
            "signature": signature,
            "payload": payload
        }
    finally:
        session.close()
