from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.notification_service import NotificationService

router = APIRouter()


def _get_notification_service() -> NotificationService:
    return NotificationService()


@router.get("/notifications")
def get_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    event_type: Optional[str] = Query(None),
):
    svc = _get_notification_service()
    return svc.list_notifications(
        limit=limit, offset=offset,
        unread_only=unread_only, event_type=event_type,
    )


@router.get("/notifications/stats")
def get_notification_stats():
    svc = _get_notification_service()
    return svc.stats()


@router.get("/notifications/{notification_id}")
def get_notification(notification_id: int):
    svc = _get_notification_service()
    result = svc.get_notification(notification_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")
    return result


@router.put("/notifications/{notification_id}/read")
def mark_read(notification_id: int):
    svc = _get_notification_service()
    if not svc.mark_read(notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.put("/notifications/read-all")
def mark_all_read(event_type: Optional[str] = Query(None)):
    svc = _get_notification_service()
    count = svc.mark_all_read(event_type=event_type)
    return {"success": True, "marked_count": count}


@router.delete("/notifications/{notification_id}")
def delete_notification(notification_id: int):
    svc = _get_notification_service()
    if not svc.delete_notification(notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.delete("/notifications/read-all")
def delete_all_read():
    svc = _get_notification_service()
    count = svc.delete_all_read()
    return {"success": True, "deleted_count": count}
