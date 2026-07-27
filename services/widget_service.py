from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from database import FINAL_STATUSES, Signal, Trade, Notification, get_session
from dto.widgets import (
    DashboardWidgetDTO,
    KPIDashboardWidgetDTO,
    PortfolioDashboardWidgetDTO,
    MonitoringDashboardWidgetDTO,
    NotificationDashboardWidgetDTO,
)

logger = logging.getLogger(__name__)


class WidgetService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def get_widget(self, widget_type: str, **params) -> dict[str, Any]:
        factory = {
            "kpi": self._kpi_widget,
            "portfolio": self._portfolio_widget,
            "monitoring": self._monitoring_widget,
            "notifications": self._notifications_widget,
        }
        handler = factory.get(widget_type)
        if not handler:
            return {"error": f"Unknown widget type: {widget_type}"}
        return handler(**params)

    def get_all_widgets(self) -> dict[str, Any]:
        session = self.session_factory()
        try:
            # Optimize: reuse a single session across widget computations to eliminate duplicate database connection overhead.
            # Use a wrapper proxy that ignores `.close()` calls so sub-services (like KPIService) do not prematurely close it.
            class _NoCloseSession:
                def __init__(self, s):
                    self._s = s
                def __getattr__(self, name):
                    return getattr(self._s, name)
                def close(self):
                    pass

            no_close_session = _NoCloseSession(session)
            sf = lambda: no_close_session
            return {
                "kpi": self._kpi_widget(session_factory=sf),
                "portfolio": self._portfolio_widget(session_factory=sf),
                "monitoring": self._monitoring_widget(session_factory=sf),
                "notifications": self._notifications_widget(session_factory=sf),
            }
        finally:
            session.close()

    def _kpi_widget(self, **kwargs) -> dict[str, Any]:
        from services.kpi_service import KPIService
        sf = kwargs.get("session_factory") or self.session_factory
        kpi_svc = KPIService(session_factory=sf)
        kpis = kpi_svc.get_kpis()
        return KPIDashboardWidgetDTO(
            kpis=[k.to_dict() for k in kpis],
            period="all",
        ).to_dict()

    def _portfolio_widget(self, **kwargs) -> dict[str, Any]:
        sf = kwargs.get("session_factory") or self.session_factory
        session = sf()
        try:
            trades = session.query(Trade).all()
            closed = [t for t in trades if t.status in FINAL_STATUSES]
            open_t = [t for t in trades if t.status == "OPEN"]
            wins = [t for t in closed if t.pnl and t.pnl > 0]
            total_pnl = sum(t.pnl or 0 for t in closed)
            wr = (len(wins) / len(closed) * 100) if closed else 0
            return PortfolioDashboardWidgetDTO(
                total_pnl=round(total_pnl, 2),
                total_trades=len(closed),
                open_trades=len(open_t),
                win_rate=round(wr, 1),
                equity=0.0,
                max_drawdown=0.0,
            ).to_dict()
        finally:
            # Only close session if it's the default (locally opened) session
            if sf == self.session_factory:
                session.close()

    def _monitoring_widget(self, **kwargs) -> dict[str, Any]:
        from monitoring.health import HealthService
        sf = kwargs.get("session_factory") or self.session_factory
        session = sf()
        try:
            db_ok = True
            try:
                session.execute(session.bind.dialect.statement_compiler(session.bind.dialect, None).__class__.__module__)
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
            if sf == self.session_factory:
                session.close()

    def _notifications_widget(self, limit: int = 10, **kwargs) -> dict[str, Any]:
        sf = kwargs.get("session_factory") or self.session_factory
        session = sf()
        try:
            recent = session.query(Notification).order_by(Notification.created_at.desc()).limit(limit).all()
            unread = session.query(Notification).filter(Notification.read == False).count()
            total = session.query(Notification).count()
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
            if sf == self.session_factory:
                session.close()
