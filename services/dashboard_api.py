import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.cache import TTLCache
from core.dashboard import DashboardService
from core.engine import DecisionEngine
from core.health import HealthChecker
from dto.models import (
    DashboardOverviewDTO, DashboardDTO, MarketOverviewDTO,
    DashboardMetricsDTO, WidgetDTO, KPIDTO,
)
from decision.trade_memory import TradeMemoryStore
from services.portfolio_service import PortfolioService
from services.intelligence_service import IntelligenceService
from services.notification_service import NotificationService


class DashboardAPI:
    def __init__(
        self,
        engine: DecisionEngine,
        health: HealthChecker,
        trade_memory: Optional[TradeMemoryStore] = None,
        portfolio_service: Optional[PortfolioService] = None,
        intelligence_service: Optional[IntelligenceService] = None,
        notification_service: Optional[NotificationService] = None,
        cache_ttl: float = 15.0,
    ):
        self._engine = engine
        self._health = health
        self._trade_memory = trade_memory or TradeMemoryStore()
        self._dashboard_core = DashboardService(
            engine=engine, health=health, trade_memory=self._trade_memory,
        )
        self._portfolio = portfolio_service or PortfolioService(trade_memory=self._trade_memory)
        self._intel = intelligence_service or IntelligenceService(engine=engine)
        self._notifications = notification_service or NotificationService()
        self._cache = TTLCache(default_ttl=cache_ttl)
        self._diagnostics: Dict[str, Any] = {
            "total_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "last_refresh": "",
        }

    def get_overview(self, force_refresh: bool = False) -> DashboardOverviewDTO:
        self._diagnostics["total_calls"] += 1
        if not force_refresh:
            cached = self._cache.get("overview")
            if cached is not None:
                self._diagnostics["cache_hits"] += 1
                return cached
        self._diagnostics["cache_misses"] += 1
        try:
            dashboard = self._dashboard_core.get_dashboard(force_refresh=force_refresh)
            portfolio = self._portfolio.get_portfolio(force_refresh=force_refresh)
            intel = self._intel.get_intelligence(force_refresh=force_refresh)
            alert = self._notifications.get_alert_summary()
            perf = self._dashboard_core.get_performance_summary()
            overview = DashboardOverviewDTO(
                portfolio=portfolio.summary.to_dict(),
                intelligence=intel.summary.to_dict(),
                risk=dashboard.risk.to_dict(),
                monitoring=dashboard.monitoring.to_dict(),
                notifications=alert.to_dict(),
                performance=perf,
            )
            self._cache.set("overview", overview)
            self._diagnostics["last_refresh"] = datetime.now(timezone.utc).isoformat()
            return overview
        except Exception:
            self._diagnostics["errors"] += 1
            cached = self._cache.get("overview")
            if cached is not None:
                return cached
            return DashboardOverviewDTO()

    def get_widgets(self) -> List[Dict[str, Any]]:
        overview = self.get_overview()
        widgets = [
            WidgetDTO(id="total_trades", type="metric", title="Total Trades",
                      value=overview.portfolio.get("total_trades", 0), color="blue"),
            WidgetDTO(id="win_rate", type="percentage", title="Win Rate",
                      value=overview.portfolio.get("win_rate", 0), color="green"),
            WidgetDTO(id="total_pnl", type="currency", title="Total PnL",
                      value=overview.portfolio.get("total_pnl", 0), color="emerald"),
            WidgetDTO(id="risk_score", type="gauge", title="Risk Score",
                      value=overview.risk.get("risk_score", 0), color="red"),
            WidgetDTO(id="unified_score", type="gauge", title="AI Confidence",
                      value=overview.intelligence.get("unified_score", 50), color="purple"),
            WidgetDTO(id="open_trades", type="metric", title="Open Positions",
                      value=overview.portfolio.get("open_trades", 0), color="amber"),
            WidgetDTO(id="unread_alerts", type="metric", title="Unread Alerts",
                      value=overview.notifications.get("unread", 0), color="rose"),
            WidgetDTO(id="active_modules", type="metric", title="Active Modules",
                      value=overview.monitoring.get("modules_active", 0), color="cyan"),
        ]
        return [w.to_dict() for w in widgets]

    def get_kpis(self) -> Dict[str, Any]:
        overview = self.get_overview()
        return {
            "total_trades": KPIDTO(label="Total Trades", value=overview.portfolio.get("total_trades", 0), trend="neutral").to_dict(),
            "win_rate": KPIDTO(label="Win Rate", value=overview.portfolio.get("win_rate", 0), unit="%", trend="up" if overview.portfolio.get("win_rate", 0) >= 50 else "down").to_dict(),
            "total_pnl": KPIDTO(label="Total PnL", value=overview.portfolio.get("total_pnl", 0), trend="up" if overview.portfolio.get("total_pnl", 0) >= 0 else "down").to_dict(),
            "risk_score": KPIDTO(label="Risk Score", value=overview.risk.get("risk_score", 0), unit="%", trend="down" if overview.risk.get("risk_score", 0) <= 50 else "up").to_dict(),
            "ai_confidence": KPIDTO(label="AI Confidence", value=overview.intelligence.get("unified_score", 50), unit="%", trend="up").to_dict(),
            "open_trades": KPIDTO(label="Open Positions", value=overview.portfolio.get("open_trades", 0), trend="neutral").to_dict(),
            "unread_alerts": KPIDTO(label="Unread Alerts", value=overview.notifications.get("unread", 0), trend="down" if overview.notifications.get("unread", 0) == 0 else "up").to_dict(),
        }

    def get_intelligence_overview(self) -> Dict[str, Any]:
        intel = self._intel.get_intelligence()
        return intel.summary.to_dict()

    def get_market_overview(self) -> Dict[str, Any]:
        market = self._dashboard_core.get_market_overview()
        intel = self._intel.get_intelligence()
        market["unified_score"] = intel.summary.unified_score
        market["market_regime"] = intel.market_regime.regime
        return market

    def get_risk_overview(self) -> Dict[str, Any]:
        dashboard = self._dashboard_core.get_dashboard()
        return dashboard.risk.to_dict()

    def get_portfolio_overview(self) -> Dict[str, Any]:
        detail = self._portfolio.get_portfolio()
        return detail.to_dict()

    def get_notification_overview(self) -> Dict[str, Any]:
        summary = self._notifications.get_alert_summary()
        recent = self._notifications.get_history(limit=5, unread_only=True)
        return {
            "summary": summary.to_dict(),
            "recent_unread": [n.to_dict() for n in recent],
        }

    def get_monitoring_overview(self) -> Dict[str, Any]:
        dashboard = self._dashboard_core.get_dashboard()
        return dashboard.monitoring.to_dict()

    def get_performance_overview(self) -> Dict[str, Any]:
        return self._dashboard_core.get_performance_summary()

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            **self._diagnostics,
            "cache_size": self._cache.size,
        }

    def get_metrics(self) -> DashboardMetricsDTO:
        return DashboardMetricsDTO(
            cache_hits=self._diagnostics["cache_hits"],
            cache_misses=self._diagnostics["cache_misses"],
            cache_size=self._cache.size,
            total_calls=self._diagnostics["total_calls"],
            errors=self._diagnostics["errors"],
            last_refresh=self._diagnostics["last_refresh"],
        )

    def invalidate_cache(self) -> None:
        self._cache.invalidate("overview")
