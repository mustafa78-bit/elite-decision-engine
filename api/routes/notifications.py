from fastapi import APIRouter, Query

from database import Notification, get_session

router = APIRouter()


@router.get("/notifications")
def get_notifications(limit: int = Query(50, ge=1, le=200)):
    session = get_session()
    try:
        rows = (
            session.query(Notification)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": n.id,
                "event_type": n.event_type,
                "payload": n.payload,
                "read": n.read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in rows
        ]
    finally:
        session.close()
