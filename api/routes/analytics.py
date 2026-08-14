from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from api.dependencies import require_user_id
from dto.analytics import AnalyticsDTO

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_analytics_service():
    from services.analytics_service import AnalyticsService
    return AnalyticsService()


@router.get("/analytics")
def get_analytics(
    request: Request,
    limit: int = Query(1000, description="Number of trades to analyze"),
):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=limit, user_id=user_id)
        return analytics.to_dict()
    except Exception as e:
        logger.error("Analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/daily")
def get_daily_analytics(
    request: Request,
    days: int = Query(30, description="Number of days"),
):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000, user_id=user_id)
        return {"daily": [d.to_dict() for d in analytics.daily[:days]]}
    except Exception as e:
        logger.error("Daily analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/weekly")
def get_weekly_analytics(
    request: Request,
    weeks: int = Query(12, description="Number of weeks"),
):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000, user_id=user_id)
        return {"weekly": [w.to_dict() for w in analytics.weekly[:weeks]]}
    except Exception as e:
        logger.error("Weekly analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/monthly")
def get_monthly_analytics(
    request: Request,
    months: int = Query(12, description="Number of months"),
):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000, user_id=user_id)
        return {"monthly": [m.to_dict() for m in analytics.monthly[:months]]}
    except Exception as e:
        logger.error("Monthly analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/win-loss")
def get_win_loss_analytics(request: Request):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000, user_id=user_id)
        if analytics.win_loss:
            return analytics.win_loss.to_dict()
        return {}
    except Exception as e:
        logger.error("Win/loss analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/symbols")
def get_symbol_analytics(request: Request):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000, user_id=user_id)
        return {"symbols": [s.to_dict() for s in analytics.by_symbol]}
    except Exception as e:
        logger.error("Symbol analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/risk")
def get_risk_analytics(request: Request):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000, user_id=user_id)
        if analytics.risk:
            return analytics.risk.to_dict()
        return {}
    except Exception as e:
        logger.error("Risk analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/drawdown")
def get_drawdown_analytics(request: Request):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000, user_id=user_id)
        if analytics.drawdown:
            return analytics.drawdown.to_dict()
        return {}
    except Exception as e:
        logger.error("Drawdown analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/heatmap")
def get_heatmap_data(request: Request):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000, user_id=user_id)
        return {"heatmap": [h.to_dict() for h in analytics.heatmap]}
    except Exception as e:
        logger.error("Heatmap data failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/trends")
def get_performance_trends(request: Request):
    user_id = require_user_id(request)
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000, user_id=user_id)
        return {"trends": [t.to_dict() for t in analytics.trends]}
    except Exception as e:
        logger.error("Performance trends failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
