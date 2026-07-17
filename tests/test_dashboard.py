import pytest
from unittest.mock import MagicMock, patch

from core.dashboard import DashboardService, DashboardAggregator
from core.engine import DecisionEngine
from core.health import HealthChecker
from decision.trade_memory import TradeMemoryStore
from decision.models import TradeOutcome
from dto.models import NotificationDTO


class TestDashboardService:

    def _make_service(self):
        engine = DecisionEngine()
        health = HealthChecker(engine=engine)
        memory = TradeMemoryStore()
        return DashboardService(engine=engine, health=health, trade_memory=memory)

    def test_get_dashboard(self):
        svc = self._make_service()
        dashboard = svc.get_dashboard()
        assert dashboard.portfolio.total_trades == 0
        assert dashboard.intelligence.unified_score >= 0
        assert dashboard.monitoring.evaluate_calls >= 0
        assert dashboard.recent_decisions == []

    def test_get_dashboard_with_trades(self):
        svc = self._make_service()
        svc._trade_memory.store(TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000,
            exit_price=55000, pnl=5000, pnl_pct=10.0,
        ))
        dashboard = svc.get_dashboard()
        assert dashboard.portfolio.total_trades == 1
        assert dashboard.portfolio.win_rate == 100.0

    def test_add_notification(self):
        svc = self._make_service()
        notif = NotificationDTO(type="info", title="test", message="hello", severity="low")
        svc.add_notification(notif)
        dashboard = svc.get_dashboard()
        assert len(dashboard.recent_notifications) == 1
        assert dashboard.recent_notifications[0].title == "test"

    def test_cache_hit(self):
        svc = self._make_service()
        svc.get_dashboard()
        svc.get_dashboard()
        assert svc._diagnostics["cache_hits"] >= 1

    def test_force_refresh(self):
        svc = self._make_service()
        svc.get_dashboard()
        hits_before = svc._diagnostics["cache_hits"]
        svc.get_dashboard(force_refresh=True)
        assert svc._diagnostics["cache_hits"] == hits_before

    def test_invalidate_cache(self):
        svc = self._make_service()
        svc.get_dashboard()
        svc.invalidate_cache()
        hits_before = svc._diagnostics["cache_hits"]
        svc.get_dashboard()
        assert svc._diagnostics["cache_hits"] == hits_before

    def test_get_dashboard_error_fallback(self):
        svc = self._make_service()
        svc.get_dashboard()
        with patch.object(svc._engine.intelligence, "evaluate", side_effect=Exception("fail")):
            dashboard = svc.get_dashboard()
            assert dashboard.portfolio.total_trades >= 0

    def test_get_performance_summary_empty(self):
        svc = self._make_service()
        perf = svc.get_performance_summary()
        assert perf["total_trades"] == 0

    def test_get_performance_summary(self):
        svc = self._make_service()
        svc._trade_memory.store(TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000,
            exit_price=55000, pnl=5000, pnl_pct=10.0,
        ))
        perf = svc.get_performance_summary()
        assert perf["total_trades"] == 1
        assert perf["best_trade"] == 5000

    def test_get_market_overview(self):
        svc = self._make_service()
        overview = svc.get_market_overview()
        assert "total_signals" in overview
        assert "active_modules" in overview
        assert "module_health" in overview

    def test_get_trade_history(self):
        svc = self._make_service()
        svc._trade_memory.store(TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000,
            exit_price=55000, pnl=5000, pnl_pct=10.0,
        ))
        history = svc.get_trade_history()
        assert len(history) == 1
        assert history[0]["symbol"] == "BTC"

    def test_get_active_positions_empty(self):
        svc = self._make_service()
        positions = svc.get_active_positions()
        assert positions == []

    def test_get_cache_stats(self):
        svc = self._make_service()
        stats = svc.get_cache_stats()
        assert "cache_size" in stats
        assert "cache_ttl" in stats

    def test_get_diagnostics(self):
        svc = self._make_service()
        diag = svc.get_diagnostics()
        assert "total_calls" in diag
        assert "cache_hits" in diag
        assert "active_notifications" in diag
        assert "trade_count" in diag

    def test_risk_aggregation_empty(self):
        svc = self._make_service()
        risk = svc._build_risk()
        assert risk.risk_score == 0.0
        assert risk.sharpe_ratio == 0.0

    def test_risk_aggregation(self):
        svc = self._make_service()
        svc._trade_memory.store(TradeOutcome(symbol="BTC", side="LONG", entry_price=100, exit_price=200, pnl=100, pnl_pct=100.0))
        svc._trade_memory.store(TradeOutcome(symbol="ETH", side="SHORT", entry_price=100, exit_price=50, pnl=-50, pnl_pct=-50.0))
        risk = svc._build_risk()
        assert risk.risk_score > 0
        assert risk.at_risk_trades > 0


class TestDashboardAggregatorBackwardCompat:

    def test_alias_exists(self):
        assert DashboardAggregator is DashboardService
