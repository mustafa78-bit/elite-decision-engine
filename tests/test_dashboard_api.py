import pytest
from unittest.mock import MagicMock, patch

from core.engine import DecisionEngine
from core.health import HealthChecker
from decision.trade_memory import TradeMemoryStore
from decision.models import TradeOutcome
from services.dashboard_api import DashboardAPI
from dto.models import DashboardOverviewDTO, DashboardMetricsDTO, WidgetDTO, KPIDTO


class TestDashboardAPI:

    def _make_api(self):
        engine = DecisionEngine()
        health = HealthChecker(engine=engine)
        memory = TradeMemoryStore()
        return DashboardAPI(engine=engine, health=health, trade_memory=memory)

    def test_get_overview_empty(self):
        api = self._make_api()
        overview = api.get_overview()
        assert overview.portfolio.get("total_trades", 0) == 0
        assert overview.intelligence.get("unified_score", 50) >= 0

    def test_get_overview_with_trades(self):
        api = self._make_api()
        api._trade_memory.store(TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000,
            exit_price=55000, pnl=5000, pnl_pct=10.0,
        ))
        overview = api.get_overview(force_refresh=True)
        assert overview.portfolio.get("total_trades") == 1
        assert overview.portfolio.get("win_rate") == 100.0

    def test_get_overview_cache(self):
        api = self._make_api()
        api.get_overview()
        api.get_overview()
        assert api.get_diagnostics()["cache_hits"] >= 1

    def test_get_overview_force_refresh(self):
        api = self._make_api()
        api.get_overview()
        hits_before = api.get_diagnostics()["cache_hits"]
        api.get_overview(force_refresh=True)
        assert api.get_diagnostics()["cache_hits"] == hits_before

    def test_get_overview_error_fallback(self):
        api = self._make_api()
        api.get_overview()
        with patch.object(api._engine.intelligence, "evaluate", side_effect=Exception("fail")):
            overview = api.get_overview(force_refresh=True)
            assert isinstance(overview, DashboardOverviewDTO)

    def test_get_widgets(self):
        api = self._make_api()
        widgets = api.get_widgets()
        assert len(widgets) == 8
        ids = [w["id"] for w in widgets]
        assert "total_trades" in ids
        assert "win_rate" in ids
        assert "total_pnl" in ids
        assert "risk_score" in ids
        assert "unified_score" in ids
        assert "open_trades" in ids
        assert "unread_alerts" in ids
        assert "active_modules" in ids

    def test_get_widgets_with_trades(self):
        api = self._make_api()
        api._trade_memory.store(TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000,
            exit_price=55000, pnl=5000, pnl_pct=10.0,
        ))
        widgets = api.get_widgets()
        trades_widget = next(w for w in widgets if w["id"] == "total_trades")
        assert trades_widget["value"] == 1

    def test_get_kpis(self):
        api = self._make_api()
        kpis = api.get_kpis()
        assert "total_trades" in kpis
        assert "win_rate" in kpis
        assert "total_pnl" in kpis
        assert "risk_score" in kpis
        assert "ai_confidence" in kpis
        assert "open_trades" in kpis
        assert "unread_alerts" in kpis

    def test_get_intelligence_overview(self):
        api = self._make_api()
        data = api.get_intelligence_overview()
        assert "unified_score" in data

    def test_get_market_overview(self):
        api = self._make_api()
        data = api.get_market_overview()
        assert "total_signals" in data
        assert "active_modules" in data
        assert "unified_score" in data
        assert "market_regime" in data

    def test_get_risk_overview(self):
        api = self._make_api()
        data = api.get_risk_overview()
        assert "risk_score" in data
        assert "max_drawdown" in data
        assert "sharpe_ratio" in data

    def test_get_portfolio_overview(self):
        api = self._make_api()
        data = api.get_portfolio_overview()
        assert "summary" in data
        assert "equity_curve" in data

    def test_get_notification_overview(self):
        api = self._make_api()
        data = api.get_notification_overview()
        assert "summary" in data
        assert "recent_unread" in data
        assert data["summary"]["total"] == 0

    def test_get_monitoring_overview(self):
        api = self._make_api()
        data = api.get_monitoring_overview()
        assert "evaluate_calls" in data
        assert "modules_active" in data
        assert "uptime_hours" in data

    def test_get_performance_overview(self):
        api = self._make_api()
        data = api.get_performance_overview()
        assert "total_trades" in data
        assert data["total_trades"] == 0

    def test_get_diagnostics(self):
        api = self._make_api()
        diag = api.get_diagnostics()
        assert "total_calls" in diag
        assert "cache_hits" in diag
        assert "cache_size" in diag

    def test_get_metrics(self):
        api = self._make_api()
        metrics = api.get_metrics()
        assert isinstance(metrics, DashboardMetricsDTO)
        assert metrics.total_calls == 0

    def test_invalidate_cache(self):
        api = self._make_api()
        api.get_overview()
        api.invalidate_cache()
        hits_before = api.get_diagnostics()["cache_hits"]
        api.get_overview()
        assert api.get_diagnostics()["cache_hits"] == hits_before
