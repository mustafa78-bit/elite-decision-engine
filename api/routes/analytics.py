from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import JSONResponse

from dto.analytics import AnalyticsDTO
from database import get_session

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
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=limit)
        return analytics.to_dict()
    except Exception as e:
        logger.error("Analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/daily")
def get_daily_analytics(
    request: Request,
    days: int = Query(30, description="Number of days"),
):
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000)
        return {"daily": [d.to_dict() for d in analytics.daily[:days]]}
    except Exception as e:
        logger.error("Daily analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/weekly")
def get_weekly_analytics(
    request: Request,
    weeks: int = Query(12, description="Number of weeks"),
):
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000)
        return {"weekly": [w.to_dict() for w in analytics.weekly[:weeks]]}
    except Exception as e:
        logger.error("Weekly analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/monthly")
def get_monthly_analytics(
    request: Request,
    months: int = Query(12, description="Number of months"),
):
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000)
        return {"monthly": [m.to_dict() for m in analytics.monthly[:months]]}
    except Exception as e:
        logger.error("Monthly analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/win-loss")
def get_win_loss_analytics(request: Request):
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000)
        if analytics.win_loss:
            return analytics.win_loss.to_dict()
        return {}
    except Exception as e:
        logger.error("Win/loss analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/symbols")
def get_symbol_analytics(request: Request):
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000)
        return {"symbols": [s.to_dict() for s in analytics.by_symbol]}
    except Exception as e:
        logger.error("Symbol analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/risk")
def get_risk_analytics(request: Request):
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000)
        if analytics.risk:
            return analytics.risk.to_dict()
        return {}
    except Exception as e:
        logger.error("Risk analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/drawdown")
def get_drawdown_analytics(request: Request):
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000)
        if analytics.drawdown:
            return analytics.drawdown.to_dict()
        return {}
    except Exception as e:
        logger.error("Drawdown analytics failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/heatmap")
def get_heatmap_data(request: Request):
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000)
        return {"heatmap": [h.to_dict() for h in analytics.heatmap]}
    except Exception as e:
        logger.error("Heatmap data failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/trends")
def get_performance_trends(request: Request):
    try:
        service = _get_analytics_service()
        analytics = service.full_analytics(limit=1000)
        return {"trends": [t.to_dict() for t in analytics.trends]}
    except Exception as e:
        logger.error("Performance trends failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/analytics/product")
def get_product_analytics():
    """Endpoint for internal Product Analytics layer metrics."""
    session = get_session()
    from database import TelemetryEvent
    try:
        events = session.query(TelemetryEvent).all()
        if not events:
            return {
                "daily_active_days": 0,
                "workflow_completion_rate": 0.0,
                "drop_off_points": {
                    "morning_brief": 0,
                    "scanner": 0,
                    "decision_center": 0,
                    "execution": 0,
                    "journal": 0,
                    "replay": 0,
                    "end_of_day": 0,
                },
                "avg_decision_time_seconds": 0.0,
                "avg_journal_completion_seconds": 0.0,
                "replay_usage_count": 0,
                "personal_insights_usage_count": 0,
                "ai_recommendation_acceptance_rate": 0.0,
            }

        # Daily active days
        active_days = set()
        for e in events:
            if e.timestamp:
                day_str = e.timestamp.strftime("%Y-%m-%d")
                active_days.add(day_str)
        daily_active_days = len(active_days)

        # Drop-off points & Step counts
        drop_off = {
            "morning_brief": len([e for e in events if "morning" in e.screen or "morning" in e.action]),
            "scanner": len([e for e in events if "scanner" in e.screen or "scanner" in e.action]),
            "decision_center": len([e for e in events if "decision" in e.screen or "decision" in e.action]),
            "execution": len([e for e in events if "execution" in e.screen or "trade" in e.action]),
            "journal": len([e for e in events if "journal" in e.screen or "journal" in e.action]),
            "replay": len([e for e in events if "replay" in e.screen or "replay" in e.action]),
            "end_of_day": len([e for e in events if "end_of_day" in e.screen or "end_of_day" in e.action]),
        }

        # Avg decision time
        decision_durations = [e.duration for e in events if "decision" in e.action and e.duration is not None]
        avg_decision_time = sum(decision_durations) / len(decision_durations) if decision_durations else 0.0

        # Avg journal completion time
        journal_durations = [e.duration for e in events if "journal" in e.action and e.duration is not None]
        avg_journal_completion = sum(journal_durations) / len(journal_durations) if journal_durations else 0.0

        # Replay and insights count
        replay_usage = len([e for e in events if "replay" in e.action])
        personal_insights_usage = len([e for e in events if "personal_insights" in e.screen or "personal" in e.action])

        # AI recommendation acceptance rate
        decision_count = len([e for e in events if "decision" in e.action])
        trade_count = len([e for e in events if "trade" in e.action or "execution" in e.screen])
        ai_acceptance = round((trade_count / decision_count * 100), 2) if decision_count > 0 else 0.0
        ai_acceptance = min(100.0, ai_acceptance)

        # Workflow completion rate
        # For each active day, check if vital steps are performed.
        required_actions = ["morning_brief_opened", "decision_opened", "trade_executed", "journal_written", "end_of_day_completed"]
        day_completion_rates = []
        for day in active_days:
            day_events = [e for e in events if e.timestamp and e.timestamp.strftime("%Y-%m-%d") == day]
            day_actions = {f"{e.screen}_{e.action}" for e in day_events}
            completed_count = sum(1 for req in required_actions if any(req in act for act in day_actions))
            rate = (completed_count / len(required_actions)) * 100
            day_completion_rates.append(rate)
        workflow_rate = round(sum(day_completion_rates) / len(day_completion_rates), 2) if day_completion_rates else 0.0

        return {
            "daily_active_days": daily_active_days,
            "workflow_completion_rate": workflow_rate,
            "drop_off_points": drop_off,
            "avg_decision_time_seconds": round(avg_decision_time, 2),
            "avg_journal_completion_seconds": round(avg_journal_completion, 2),
            "replay_usage_count": replay_usage,
            "personal_insights_usage_count": personal_insights_usage,
            "ai_recommendation_acceptance_rate": ai_acceptance,
        }
    except Exception as e:
        logger.error("Failed to compute product analytics: %s", e)
        raise HTTPException(status_code=500, detail="Failed to calculate product analytics")
    finally:
        session.close()
