from datetime import datetime, timezone
import logging
from typing import Optional, List

import database
from enterprise.models import AuditLog

logger = logging.getLogger(__name__)

def log_action(
    action: str,
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> dict:
    """Insert a compliance audit record to trace platform actions securely."""
    session = database.get_session()
    try:
        log_entry = AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        session.add(log_entry)
        session.commit()

        logger.info("Audit Logged | action=%s | user_id=%s | org_id=%s", action, user_id, organization_id)
        return {
            "success": True,
            "id": log_entry.id,
            "action": log_entry.action,
            "created_at": log_entry.created_at.isoformat() if log_entry.created_at else None
        }
    except Exception as e:
        session.rollback()
        logger.error("Failed to write audit log action %s: %s", action, e)
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def search_audit_logs(
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    action: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[dict]:
    """Retrieve and filter audit logs for enterprise security compliance."""
    session = database.get_session()
    try:
        query = session.query(AuditLog)

        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if organization_id is not None:
            query = query.filter(AuditLog.organization_id == organization_id)
        if action is not None:
            query = query.filter(AuditLog.action.ilike(f"%{action}%"))

        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from)
                query = query.filter(AuditLog.created_at >= dt_from)
            except ValueError:
                pass
        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to)
                query = query.filter(AuditLog.created_at <= dt_to)
            except ValueError:
                pass

        rows = query.order_by(AuditLog.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "user_id": r.user_id,
                "organization_id": r.organization_id,
                "action": r.action,
                "details": r.details,
                "ip_address": r.ip_address,
                "user_agent": r.user_agent,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in rows
        ]
    finally:
        session.close()
