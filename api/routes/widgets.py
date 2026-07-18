from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.cache import cached
from services.widget_service import WidgetService

router = APIRouter()


def _get_widget_service() -> WidgetService:
    return WidgetService()


@router.get("/widgets")
@cached(ttl=15)
def list_widgets():
    svc = _get_widget_service()
    return svc.get_all_widgets()


@router.get("/widgets/{widget_type}")
@cached(ttl=15)
def get_widget(widget_type: str, limit: int = Query(10, ge=1, le=100)):
    svc = _get_widget_service()
    result = svc.get_widget(widget_type, limit=limit)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/widgets/kpi/detail")
@cached(ttl=15)
def kpi_widget_detail():
    svc = _get_widget_service()
    return svc.get_widget("kpi")


@router.get("/widgets/portfolio/summary")
@cached(ttl=15)
def portfolio_widget_summary():
    svc = _get_widget_service()
    return svc.get_widget("portfolio")


@router.get("/widgets/monitoring/status")
@cached(ttl=10)
def monitoring_widget_status():
    svc = _get_widget_service()
    return svc.get_widget("monitoring")


@router.get("/widgets/notifications/recent")
@cached(ttl=10)
def notifications_widget_recent():
    svc = _get_widget_service()
    return svc.get_widget("notifications")
