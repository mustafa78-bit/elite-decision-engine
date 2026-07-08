from fastapi import APIRouter, HTTPException, Query

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


@router.put("/notifications/{notification_id}/read")
def mark_read(notification_id: int):
    session = get_session()
    try:
        notif = session.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found")
        notif.read = True
        session.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()
