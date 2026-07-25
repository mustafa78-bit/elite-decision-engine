from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from database import Notification, get_session

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def list_notifications(
        self, limit: int = 50, offset: int = 0,
        unread_only: bool = False,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        session = self.session_factory()
        try:
            q = session.query(Notification)
            if user_id is not None:
                q = q.filter(Notification.user_id == user_id)
            if unread_only:
                q = q.filter(Notification.read == False)
            if event_type:
                q = q.filter(Notification.event_type == event_type)
            total = q.count()
            rows = q.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

            unread_q = session.query(Notification).filter(Notification.read == False)
            if user_id is not None:
                unread_q = unread_q.filter(Notification.user_id == user_id)
            unread_count = unread_q.count()

            return {
                "notifications": [self._to_dict(n) for n in rows],
                "total": total,
                "offset": offset,
                "limit": limit,
                "unread": unread_count,
            }
        finally:
            session.close()

    def get_notification(self, notification_id: int, user_id: Optional[int] = None) -> Optional[dict[str, Any]]:
        session = self.session_factory()
        try:
            q = session.query(Notification).filter(Notification.id == notification_id)
            if user_id is not None:
                q = q.filter(Notification.user_id == user_id)
            n = q.first()
            return self._to_dict(n) if n else None
        finally:
            session.close()

    def mark_read(self, notification_id: int, user_id: Optional[int] = None) -> bool:
        session = self.session_factory()
        try:
            q = session.query(Notification).filter(Notification.id == notification_id)
            if user_id is not None:
                q = q.filter(Notification.user_id == user_id)
            n = q.first()
            if not n:
                return False
            n.read = True
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def mark_all_read(self, event_type: Optional[str] = None, user_id: Optional[int] = None) -> int:
        session = self.session_factory()
        try:
            q = session.query(Notification).filter(Notification.read == False)
            if user_id is not None:
                q = q.filter(Notification.user_id == user_id)
            if event_type:
                q = q.filter(Notification.event_type == event_type)
            count = q.count()
            q.update({"read": True}, synchronize_session='fetch')
            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_notification(self, notification_id: int, user_id: Optional[int] = None) -> bool:
        session = self.session_factory()
        try:
            q = session.query(Notification).filter(Notification.id == notification_id)
            if user_id is not None:
                q = q.filter(Notification.user_id == user_id)
            n = q.first()
            if not n:
                return False
            session.delete(n)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_all_read(self, user_id: Optional[int] = None) -> int:
        session = self.session_factory()
        try:
            q = session.query(Notification).filter(Notification.read == True)
            if user_id is not None:
                q = q.filter(Notification.user_id == user_id)
            count = q.count()
            q.delete(synchronize_session='fetch')
            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def stats(self, user_id: Optional[int] = None) -> dict[str, Any]:
        session = self.session_factory()
        try:
            q_total = session.query(Notification)
            q_unread = session.query(Notification).filter(Notification.read == False)
            if user_id is not None:
                q_total = q_total.filter(Notification.user_id == user_id)
                q_unread = q_unread.filter(Notification.user_id == user_id)

            total = q_total.count()
            unread = q_unread.count()

            from sqlalchemy import func
            by_type_q = session.query(
                Notification.event_type, func.count(Notification.id)
            )
            if user_id is not None:
                by_type_q = by_type_q.filter(Notification.user_id == user_id)
            by_type_rows = by_type_q.group_by(Notification.event_type).all()
            by_type = {row[0]: row[1] for row in by_type_rows}

            from datetime import datetime, timezone, timedelta
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            recent_q = session.query(Notification).filter(
                Notification.created_at >= seven_days_ago
            )
            if user_id is not None:
                recent_q = recent_q.filter(Notification.user_id == user_id)
            recent = recent_q.count()

            return {
                "total": total,
                "unread": unread,
                "by_type": by_type,
                "last_seven_days": recent,
            }
        finally:
            session.close()

    def _to_dict(self, n: Notification) -> dict[str, Any]:
        return {
            "id": n.id,
            "user_id": n.user_id,
            "event_type": n.event_type,
            "payload": n.payload,
            "read": n.read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
