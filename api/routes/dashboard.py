from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import or_

from api.dependencies import require_user_id
from database import OPEN, Signal, Trade, get_session
from dto.widgets import (
    DashboardWidgetDTO,
    ExplanationDashboardWidgetDTO,
    HeroBannerDTO,
    KPIDashboardWidgetDTO,
    MonitoringDashboardWidgetDTO,
    NotificationDashboardWidgetDTO,
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
    user_id = require_user_id(request)
    try:
        kpi_service = KPIService()
        analytics_service = _get_analytics_service()

        kpis = kpi_service.get_kpis(user_id=user_id)
        analytics = analytics_service.full_analytics(limit=100, user_id=user_id)

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
    user_id = require_user_id(request)
    try:
        service = KPIService()
        kpis = service.get_kpis(user_id=user_id)
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
    user_id = require_user_id(request)
    session = get_session()
    try:
        signal = (
            session.query(Signal)
            .filter(Signal.id == signal_id, or_(Signal.user_id == user_id, Signal.user_id.is_(None)))
            .first()
        )
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
    user_id = require_user_id(request)
    session = get_session()
    try:
        signal = (
            session.query(Signal)
            .filter(Signal.id == signal_id, or_(Signal.user_id == user_id, Signal.user_id.is_(None)))
            .first()
        )
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
    user_id = require_user_id(request)
    session = get_session()
    try:
        from database import Notification

        notif_scope = or_(Notification.user_id == user_id, Notification.user_id.is_(None))
        unread = session.query(Notification).filter(notif_scope, Notification.read == False).count()  # noqa: E712 (SQLAlchemy filter expression, not a Python bool comparison)
        recent = (
            session.query(Notification)
            .filter(notif_scope)
            .order_by(Notification.created_at.desc())
            .limit(10)
            .all()
        )
        total = session.query(Notification).filter(notif_scope).count()
        widget = NotificationDashboardWidgetDTO(
            unread=unread,
            total=total,
            notifications=[
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


def _live_prices_for_open_symbols(symbols: list[str]) -> dict[str, float]:
    """Best-effort current price per open-position symbol, for
    PortfolioEngine.snapshot()'s unrealized-PnL calc. Never raises --
    PortfolioEngine.snapshot() already falls back to each position's entry
    price for any symbol missing from this dict (delta=0, same as before
    this existed), so a fetch failure here degrades gracefully rather than
    breaking the whole hero banner.
    """
    prices: dict[str, float] = {}
    if not symbols:
        return prices
    try:
        from market.provider import get_shared_multi_provider
        collector = get_shared_multi_provider()
        for symbol in symbols:
            try:
                # Pass the full "XUSDT"-style symbol -- each underlying
                # provider (market/provider/hyperliquid.py etc.) strips the
                # "USDT" suffix itself internally; stripping it here too
                # would break MultiProvider._resolve()'s routing table
                # lookup (SYMBOL_PROVIDER_ASSIGNMENT is keyed by the full
                # "XUSDT" form).
                ticker = collector.get_ticker(symbol)
                price = ticker.get("price")
                if price:
                    prices[symbol] = float(price)
            except Exception:
                logger.warning("Failed to fetch live price for %s (hero banner unrealized PnL)", symbol, exc_info=True)
    except Exception:
        logger.warning("Failed to load market provider for hero banner live pricing", exc_info=True)
    return prices


@router.get("/dashboard/hero")
def dashboard_hero(request: Request):
    user_id = require_user_id(request)
    session = get_session()
    signal: Signal | None = None
    trade: Trade | None = None
    open_symbols: list[str] = []
    try:
        signal_scope = or_(Signal.user_id == user_id, Signal.user_id.is_(None))
        trade_scope = or_(Trade.user_id == user_id, Trade.user_id.is_(None))
        signal = session.query(Signal).filter(signal_scope).order_by(Signal.created_at.desc()).first()
        trade = (
            session.query(Trade)
            .filter(trade_scope, Trade.status == OPEN)
            .order_by(Trade.created_at.desc())
            .first()
        )
        open_symbols = [
            row[0] for row in
            session.query(Trade.symbol).filter(trade_scope, Trade.status == OPEN).distinct().all()
        ]
    finally:
        session.close()

    try:
        from performance.engine import PerformanceEngine
        from portfolio.engine import PortfolioEngine
        current_prices = _live_prices_for_open_symbols(open_symbols)
        snapshot = PortfolioEngine().snapshot(current_prices=current_prices, user_id=user_id)
        perf = PerformanceEngine().report(snapshot, user_id=user_id)

        market_regime = "UNKNOWN"
        try:
            from market.provider import get_shared_multi_provider
            from market_data.indicators import IndicatorEngine
            from scoring.regime_ai import get_regime_ai
            collector = get_shared_multi_provider()
            df = collector.get_ohlcv(symbol="BTC", timeframe="1h")
            if not df.empty:
                values = IndicatorEngine().calculate(df)
                reg = get_regime_ai().detect(values)
                market_regime = reg.get("regime", "UNKNOWN")
        except Exception:
            logger.warning("Failed to fetch market regime for hero banner", exc_info=True)

        from explain.core import ExplainInput, ExplainResult
        from explain.engine import ExplainEngine

        empty_result = ExplainResult()
        result = empty_result

        if signal:
            inp = ExplainInput(
                symbol=signal.symbol,
                side=signal.side,
                technical_score=signal.score or 0,
                whale_score=signal.funding_score or signal.oi_score or 0,
                news_score=signal.cvd_score or 0,
                risk_score=signal.risk_score or 0,
                trend_score=signal.trend_score or 0,
                portfolio_total_equity=snapshot.total_equity,
                portfolio_unrealized_pnl=snapshot.unrealized_pnl,
                portfolio_realized_pnl=snapshot.realized_pnl,
                portfolio_exposure=snapshot.exposure,
                portfolio_initial_capital=snapshot.initial_capital,
                performance_sharpe=perf.sharpe_ratio,
                performance_sortino=perf.sortino_ratio,
                performance_calmar=perf.calmar_ratio,
                performance_profit_factor=snapshot.profit_factor,
                performance_win_rate=snapshot.win_rate,
                performance_total_pnl=snapshot.total_pnl,
                performance_max_drawdown=snapshot.max_drawdown,
            )
            result = ExplainEngine().explain(inp)

        from datetime import datetime, timezone

        entry = float(trade.entry or 0) if trade else (float(signal.price or 0) if signal else 0.0)
        tp = float(trade.tp1 or 0) if trade else 0.0
        sl = float(trade.stop or 0) if trade else 0.0
        rr = float(trade.rr or 0) if trade else 0.0
        ts = signal.created_at.isoformat() if signal and signal.created_at else datetime.now(UTC).isoformat()

        widget = HeroBannerDTO(
            decision=result.decision,
            confidence=round(result.confidence, 1),
            risk=round(signal.risk_score or 0, 2) if signal else 0.0,
            summary=result.summary,
            reasons=result.reasons,
            warnings=result.warnings,
            risk_notes=result.risk_notes,
            supporting_signals=result.supporting_signals,
            entry=round(entry, 2),
            tp=round(tp, 2),
            sl=round(sl, 2),
            rr=round(rr, 2),
            timestamp=ts,
            market_regime=market_regime,
            signal_id=signal.id if signal else 0,
            symbol=signal.symbol if signal else "",
        )
        return widget.to_dict()
    except Exception as e:
        logger.error("Dashboard hero failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
