import math
import time
from typing import Any, Dict, List, Optional

from core.engine import DecisionEngine
from core.health import HealthChecker
from core.cache import TTLCache
from dto.models import (
    DashboardDTO,
    PortfolioDTO,
    IntelligenceDTO,
    RiskDTO,
    MonitoringDTO,
    NotificationDTO,
)
from decision.trade_memory import TradeMemoryStore


class DashboardService:

    def __init__(
        self,
        engine: DecisionEngine,
        health: HealthChecker,
        trade_memory: Optional[TradeMemoryStore] = None,
        cache_ttl: float = 30.0,
    ):
        self._engine = engine
        self._health = health
        self._trade_memory = trade_memory or TradeMemoryStore()
        self._notifications: List[NotificationDTO] = []
        self._cache = TTLCache(default_ttl=cache_ttl)
        self._diagnostics: Dict[str, Any] = {
            "total_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
        }

    def get_dashboard(self, force_refresh: bool = False) -> DashboardDTO:
        self._diagnostics["total_calls"] += 1
        if not force_refresh:
            cached = self._cache.get("dashboard")
            if cached is not None:
                self._diagnostics["cache_hits"] += 1
                return cached
        self._diagnostics["cache_misses"] += 1

        try:
            metrics = self._health.get_metrics()
            health_status = self._health.check()

            dashboard = DashboardDTO(
                portfolio=self._build_portfolio(),
                intelligence=self._build_intelligence(),
                risk=self._build_risk(),
                monitoring=self._build_monitoring(metrics, health_status),
                recent_decisions=self._engine.get_decision_history(n=10),
                recent_notifications=list(self._notifications[-20:]),
            )
            self._cache.set("dashboard", dashboard)
            return dashboard
        except Exception:
            self._diagnostics["errors"] += 1
            cached = self._cache.get("dashboard")
            if cached is not None:
                return cached
            return DashboardDTO()

    def _build_portfolio(self) -> PortfolioDTO:
        all_trades = self._trade_memory.get_all()
        if not all_trades:
            return PortfolioDTO()
        wins = self._trade_memory.get_wins()
        losses = self._trade_memory.get_losses()
        return PortfolioDTO(
            total_trades=len(all_trades),
            win_rate=round(self._trade_memory.win_rate() * 100, 1),
            total_pnl=round(self._trade_memory.average_pnl() * len(all_trades), 2),
            average_pnl_pct=round(self._trade_memory.average_pnl_pct(), 2),
            open_trades=len([t for t in all_trades if getattr(t, "is_open", False)]),
            largest_win=round(max((t.pnl for t in wins), default=0), 2),
            largest_loss=round(min((t.pnl for t in losses), default=0), 2),
        )

    def _build_intelligence(self) -> IntelligenceDTO:
        try:
            result = self._engine.intelligence.evaluate()
            fusion = result.get("_fusion", {})
            report = self._engine.intelligence.get_fusion_report()
            health = fusion.get("health", {})
            return IntelligenceDTO(
                unified_score=fusion.get("unified_score", 50.0),
                whale_health=health.get("whale", False),
                liquidity_health=health.get("liquidity", False),
                orderflow_health=health.get("orderflow", False),
                ms_health=health.get("market_structure", False),
                news_health=health.get("news", False),
                sentiment_health=health.get("sentiment", False),
                macro_health=health.get("macro", False),
                module_scores=fusion.get("module_scores", {}),
                contribution_report=report,
            )
        except Exception:
            return IntelligenceDTO()

    def _build_risk(self) -> RiskDTO:
        all_trades = self._trade_memory.get_all()
        if not all_trades:
            return RiskDTO()
        pnls = [t.pnl for t in all_trades]
        returns = [t.pnl_pct for t in all_trades]
        total = len(pnls)
        wins = sum(1 for p in pnls if p > 0)
        losses = sum(1 for p in pnls if p < 0)
        win_rate = wins / total if total > 0 else 0
        avg_win = sum(p for p in pnls if p > 0) / wins if wins > 0 else 0
        avg_loss = abs(sum(p for p in pnls if p < 0) / losses) if losses > 0 else 1
        sharpe = (win_rate - (1 - win_rate)) / (avg_loss / (avg_win + 0.001)) if avg_loss > 0 else 0
        mean_return = sum(returns) / total if total > 0 else 0
        variance = sum((r - mean_return) ** 2 for r in returns) / total if total > 0 else 0
        volatility = math.sqrt(variance) if variance > 0 else 0
        current_drawdown = min(0, sum(pnls))
        return RiskDTO(
            risk_score=round((1 - win_rate) * 100, 1),
            max_drawdown=round(abs(current_drawdown), 2),
            volatility=round(volatility, 2),
            sharpe_ratio=round(sharpe, 2),
            at_risk_trades=losses,
        )

    def _build_monitoring(self, metrics, health_status) -> MonitoringDTO:
        return MonitoringDTO(
            evaluate_calls=metrics.evaluate_calls,
            modules_active=metrics.modules_active,
            decisions_today=metrics.decisions_made,
            uptime_hours=round(metrics.uptime_seconds / 3600, 2),
            last_evaluation=health_status.timestamp,
            memory_usage_mb=0.0,
        )

    def add_notification(self, notification: NotificationDTO) -> None:
        self._notifications.append(notification)
        self._cache.invalidate("dashboard")

    def invalidate_cache(self) -> None:
        self._cache.invalidate("dashboard")

    def get_performance_summary(self) -> Dict[str, Any]:
        all_trades = self._trade_memory.get_all()
        if not all_trades:
            return {"total_trades": 0, "avg_pnl": 0, "avg_pnl_pct": 0}
        return {
            "total_trades": len(all_trades),
            "avg_pnl": round(self._trade_memory.average_pnl(), 2),
            "avg_pnl_pct": round(self._trade_memory.average_pnl_pct(), 2),
            "win_rate": round(self._trade_memory.win_rate() * 100, 1),
            "best_trade": round(max(t.pnl for t in all_trades), 2),
            "worst_trade": round(min(t.pnl for t in all_trades), 2),
        }

    def get_market_overview(self) -> Dict[str, Any]:
        overview: Dict[str, Any] = {"total_signals": 0, "active_modules": 0, "module_health": {}}
        try:
            intelligence = self._engine.intelligence.evaluate()
            overview["total_signals"] = len(self._engine.get_decision_history(n=1000))
            for mod_key in ("whale", "liquidity", "orderflow", "market_structure"):
                mod_data = intelligence.get(mod_key, {})
                overview["module_health"][mod_key] = mod_data.get("ok", False)
            overview["active_modules"] = sum(1 for v in overview["module_health"].values() if v)
        except Exception:
            pass
        return overview

    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        all_trades = self._trade_memory.get_all()
        return [t.to_dict() for t in all_trades[-limit:]]

    def get_active_positions(self) -> List[Dict[str, Any]]:
        return [
            t.to_dict() for t in self._trade_memory.get_all()
            if getattr(t, "is_open", False)
        ]

    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "cache_size": self._cache.size,
            "cache_ttl": self._cache._default_ttl,
        }

    def get_diagnostics(self) -> Dict[str, Any]:
        metrics = self._health.get_metrics()
        return {
            **self._diagnostics,
            "active_notifications": len(self._notifications),
            "trade_count": self._trade_memory.count(),
            "cache_size": self._cache.size,
            "evaluate_calls": metrics.evaluate_calls,
            "modules_active": metrics.modules_active,
        }


DashboardAggregator = DashboardService
