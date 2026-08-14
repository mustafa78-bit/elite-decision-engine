from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Optional

from sqlalchemy import or_, text

from config import ACCOUNT_EQUITY
from database import FINAL_STATUSES, Notification, PaperTrade, Signal, Trade, get_session
from dto.widgets import (
    DashboardWidgetDTO,
    KPIDashboardWidgetDTO,
    MonitoringDashboardWidgetDTO,
    NotificationDashboardWidgetDTO,
    PortfolioDashboardWidgetDTO,
)

logger = logging.getLogger(__name__)


class WidgetService:
    def __init__(self, session_factory: Callable[[], Any] | None = None):
        self.session_factory = session_factory or get_session

    def get_widget(self, widget_type: str, user_id: int | None = None, **params) -> dict[str, Any]:
        factory = {
            "kpi": self._kpi_widget,
            "portfolio": self._portfolio_widget,
            "monitoring": self._monitoring_widget,
            "notifications": self._notifications_widget,
        }
        handler = factory.get(widget_type)
        if not handler:
            return {"error": f"Unknown widget type: {widget_type}"}
        return handler(user_id=user_id, **params)

    def get_all_widgets(self, user_id: int | None = None) -> dict[str, Any]:
        return {
            "kpi": self._kpi_widget(user_id=user_id),
            "portfolio": self._portfolio_widget(user_id=user_id),
            "monitoring": self._monitoring_widget(user_id=user_id),
            "notifications": self._notifications_widget(user_id=user_id),
        }

    def _kpi_widget(self, user_id: int | None = None, **kwargs) -> dict[str, Any]:
        from services.kpi_service import KPIService
        kpi_svc = KPIService(session_factory=self.session_factory)
        kpis = kpi_svc.get_kpis(user_id=user_id)
        return KPIDashboardWidgetDTO(
            kpis=[k.to_dict() for k in kpis],
            period="all",
        ).to_dict()

    def _portfolio_widget(self, user_id: int | None = None, **kwargs) -> dict[str, Any]:
        session = self.session_factory()
        try:
            query = session.query(Trade, PaperTrade).outerjoin(
                PaperTrade, PaperTrade.position_id == Trade.id
            )
            if user_id is not None:
                query = query.filter(or_(Trade.user_id == user_id, Trade.user_id.is_(None)))
            results = query.all()
            dollar_pnls = []
            for t, pt in results:
                qty = float(pt.quantity) if (pt is not None and pt.quantity is not None) else 1.0
                dollar_pnls.append((t, (t.pnl or 0.0) * qty))

            closed = [(t, pnl) for t, pnl in dollar_pnls if t.status in FINAL_STATUSES]
            open_t = [t for t, _ in dollar_pnls if t.status == "OPEN"]
            wins = [pnl for _, pnl in closed if pnl > 0]
            total_pnl = sum(pnl for _, pnl in closed)
            wr = (len(wins) / len(closed) * 100) if closed else 0
            return PortfolioDashboardWidgetDTO(
                total_pnl=round(total_pnl, 2),
                total_trades=len(closed),
                open_trades=len(open_t),
                win_rate=round(wr, 1),
                equity=round(ACCOUNT_EQUITY + total_pnl, 2),
                max_drawdown=round(self._max_drawdown(closed), 2),
            ).to_dict()
        finally:
            session.close()

    def _max_drawdown(self, closed: list[tuple[Trade, float]]) -> float:
        sorted_closed = sorted(closed, key=lambda pair: pair[0].closed_at or pair[0].created_at)
        peak = 0.0
        max_dd = 0.0
        running = 0.0
        for _, pnl in sorted_closed:
            running += pnl
            if running > peak:
                peak = running
            dd = peak - running
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def _monitoring_widget(self, **kwargs) -> dict[str, Any]:
        from monitoring.health import HealthService
        session = self.session_factory()
        try:
            db_ok = True
            try:
                session.execute(text("SELECT 1"))
            except Exception:
                db_ok = False
            return MonitoringDashboardWidgetDTO(
                status="healthy" if db_ok else "degraded",
                uptime_seconds=round(HealthService.uptime(), 2),
                database_status="connected" if db_ok else "error",
                collector_status="unknown",
                websocket_clients=0,
                last_error=None,
            ).to_dict()
        finally:
            session.close()

    def _notifications_widget(self, user_id: int | None = None, limit: int = 10) -> dict[str, Any]:
        session = self.session_factory()
        try:
            notif_scope = or_(Notification.user_id == user_id, Notification.user_id.is_(None))
            notif_query = session.query(Notification)
            if user_id is not None:
                notif_query = notif_query.filter(notif_scope)
            recent = notif_query.order_by(Notification.created_at.desc()).limit(limit).all()
            unread_query = session.query(Notification)
            if user_id is not None:
                unread_query = unread_query.filter(notif_scope)
            unread = unread_query.filter(Notification.read == False).count()  # noqa: E712 (SQLAlchemy filter expression, not a Python bool comparison)
            total_query = session.query(Notification)
            if user_id is not None:
                total_query = total_query.filter(notif_scope)
            total = total_query.count()
            return NotificationDashboardWidgetDTO(
                unread=unread,
                total=total,
                notifications=[{
                    "id": n.id, "event_type": n.event_type,
                    "payload": n.payload, "read": n.read,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                } for n in recent],
            ).to_dict()
        finally:
            session.close()
