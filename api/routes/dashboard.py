from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from database import Signal, Trade, get_session
from dto.widgets import (
    DashboardWidgetDTO,
    ExplanationDashboardWidgetDTO,
    KPIDashboardWidgetDTO,
    MonitoringDashboardWidgetDTO,
    NotificationDashboardWidgetDTO,
    PortfolioDashboardWidgetDTO,
    TimelineDashboardWidgetDTO,
)
from services.kpi_service import KPIService

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_explanation_service():
    from services.explanation_service import ExplanationService
    return ExplanationService()


def _get_analytics_service():
    from services.analytics_service import AnalyticsService
    return AnalyticsService()


@router.get("/dashboard/overview")
def dashboard_overview(request: Request):
    try:
        kpi_service = KPIService()
        analytics_service = _get_analytics_service()

        kpis = kpi_service.get_kpis()
        analytics = analytics_service.full_analytics(limit=100)

        widgets: list[dict[str, Any]] = [
            KPIDashboardWidgetDTO(
                kpis=[k.to_dict() for k in kpis],
                period="all",
            ).to_dict(),
        ]

        if analytics.win_loss:
            widgets.append({
                "widget_id": "win-loss",
                "widget_type": "win_loss",
                "title": "Win/Loss Analysis",
                "data": analytics.win_loss.to_dict(),
            })

        if analytics.drawdown:
            widgets.append({
                "widget_id": "drawdown",
                "widget_type": "drawdown",
                "title": "Drawdown Analysis",
                "data": analytics.drawdown.to_dict(),
            })

        return {"widgets": widgets}
    except Exception as e:
        logger.error("Dashboard overview failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/dashboard/kpi")
def dashboard_kpi(request: Request):
    try:
        service = KPIService()
        kpis = service.get_kpis()
        widget = KPIDashboardWidgetDTO(
            kpis=[k.to_dict() for k in kpis],
            period="all",
        )
        return widget.to_dict()
    except Exception as e:
        logger.error("Dashboard KPI failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/dashboard/explanation/{signal_id}")
def dashboard_explanation(signal_id: int, request: Request):
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            return JSONResponse(status_code=404, content={"error": f"Signal {signal_id} not found"})

        service = _get_explanation_service()
        explanation = service.explain_signal(signal)

        reasoning = explanation.reasoning
        widget = ExplanationDashboardWidgetDTO(
            signal_id=signal_id,
            decision=reasoning.decision if reasoning else "",
            confidence=reasoning.confidence_breakdown.confidence if reasoning and reasoning.confidence_breakdown else 0,
            breakdown={
                "trend": reasoning.confidence_breakdown.trend_score if reasoning and reasoning.confidence_breakdown else 0,
                "volume": reasoning.confidence_breakdown.volume_score if reasoning and reasoning.confidence_breakdown else 0,
                "btc": reasoning.confidence_breakdown.btc_score if reasoning and reasoning.confidence_breakdown else 0,
                "mtf": reasoning.confidence_breakdown.mtf_score if reasoning and reasoning.confidence_breakdown else 0,
                "risk": reasoning.confidence_breakdown.risk_score if reasoning and reasoning.confidence_breakdown else 0,
            },
            human_readable=reasoning.human_readable if reasoning else "",
        )
        return widget.to_dict()
    except Exception as e:
        logger.error("Dashboard explanation failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@router.get("/dashboard/timeline/{signal_id}")
def dashboard_timeline(signal_id: int, request: Request):
    session = get_session()
    try:
        signal = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal is None:
            return JSONResponse(status_code=404, content={"error": f"Signal {signal_id} not found"})

        service = _get_explanation_service()
        explanation = service.explain_signal(signal)

        widget = TimelineDashboardWidgetDTO(
            events=explanation.timeline.events if explanation.timeline else [],
            total_duration_ms=explanation.timeline.total_duration_ms if explanation.timeline else 0,
        )
        return widget.to_dict()
    except Exception as e:
        logger.error("Dashboard timeline failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@router.get("/dashboard/portfolio")
def dashboard_portfolio(request: Request):
    session = get_session()
    try:
        trades = session.query(Trade).all()
        closed = [t for t in trades if t.status in ("TP_HIT", "SL_HIT", "CLOSED")]
        open_trades = [t for t in trades if t.status == "OPEN"]
        total_pnl = sum(t.pnl or 0 for t in closed)
        wins = [t for t in closed if t.pnl and t.pnl > 0]

        pnls = [t.pnl or 0 for t in closed]
        peak = 0.0
        max_dd = 0.0
        cumulative = 0.0
        for p in pnls:
            cumulative += p
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

        from config import ACCOUNT_EQUITY

        widget = PortfolioDashboardWidgetDTO(
            total_pnl=round(total_pnl, 2),
            total_trades=len(closed),
            open_trades=len(open_trades),
            win_rate=round((len(wins) / len(closed) * 100), 1) if closed else 0,
            equity=round(ACCOUNT_EQUITY + total_pnl, 2),
            max_drawdown=round(max_dd, 2),
        )
        return widget.to_dict()
    except Exception as e:
        logger.error("Dashboard portfolio failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()


@router.get("/dashboard/monitoring")
def dashboard_monitoring(request: Request):
    try:
        from monitoring.health import HealthService

        health = HealthService.full()
        hs = HealthService()

        from api.main import manager

        widget = MonitoringDashboardWidgetDTO(
            status=health.get("status", "unknown"),
            uptime_seconds=hs.uptime(),
            database_status=health.get("database", {}).get("status", "unknown"),
            collector_status=health.get("collector", {}).get("status", "unknown"),
            websocket_clients=len(getattr(manager, "_clients", set())),
            last_error=health.get("errors"),
        )
        return widget.to_dict()
    except Exception as e:
        logger.error("Dashboard monitoring failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/dashboard/notifications")
def dashboard_notifications(request: Request):
    session = get_session()
    try:
        from database import Notification

        unread = session.query(Notification).filter(Notification.read == False).count()
        recent = (
            session.query(Notification)
            .order_by(Notification.created_at.desc())
            .limit(10)
            .all()
        )
        widget = NotificationDashboardWidgetDTO(
            unread_count=unread,
            recent=[
                {
                    "id": n.id,
                    "event_type": n.event_type,
                    "payload": n.payload,
                    "read": n.read,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in recent
            ],
        )
        return widget.to_dict()
    except Exception as e:
        logger.error("Dashboard notifications failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()
