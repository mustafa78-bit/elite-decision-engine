from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.cache import cached
from api.dependencies import require_user_id
from services.widget_service import WidgetService

router = APIRouter()


def _get_widget_service() -> WidgetService:
    return WidgetService()


@router.get("/widgets")
@cached(ttl=15)
def list_widgets(user_id: int = Depends(require_user_id)):
    svc = _get_widget_service()
    return svc.get_all_widgets(user_id=user_id)


@router.get("/widgets/{widget_type}")
@cached(ttl=15)
def get_widget(widget_type: str, user_id: int = Depends(require_user_id), limit: int = Query(10, ge=1, le=100)):
    svc = _get_widget_service()
    result = svc.get_widget(widget_type, user_id=user_id, limit=limit)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/widgets/kpi/detail")
@cached(ttl=15)
def kpi_widget_detail(user_id: int = Depends(require_user_id)):
    svc = _get_widget_service()
    return svc.get_widget("kpi", user_id=user_id)


@router.get("/widgets/portfolio/summary")
@cached(ttl=15)
def portfolio_widget_summary(user_id: int = Depends(require_user_id)):
    svc = _get_widget_service()
    return svc.get_widget("portfolio", user_id=user_id)


@router.get("/widgets/monitoring/status")
@cached(ttl=10)
def monitoring_widget_status(user_id: int = Depends(require_user_id)):
    svc = _get_widget_service()
    return svc.get_widget("monitoring", user_id=user_id)


@router.get("/widgets/notifications/recent")
@cached(ttl=10)
def notifications_widget_recent(user_id: int = Depends(require_user_id)):
    svc = _get_widget_service()
    return svc.get_widget("notifications", user_id=user_id)
