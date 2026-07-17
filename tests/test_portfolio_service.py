import pytest

from decision.trade_memory import TradeMemoryStore
from decision.models import TradeOutcome
from services.portfolio_service import PortfolioService


class TestPortfolioService:

    def _make_service(self, initial_equity=10000.0):
        memory = TradeMemoryStore()
        return PortfolioService(trade_memory=memory, initial_equity=initial_equity), memory

    def test_get_portfolio_empty(self):
        svc, _ = self._make_service()
        detail = svc.get_portfolio()
        assert detail.summary.total_trades == 0
        assert detail.summary.win_rate == 0.0
        assert detail.summary.total_pnl == 0.0
        assert detail.daily_pnl == 0.0
        assert detail.profit_factor == 0.0
        assert detail.exposure == 0.0

    def test_get_portfolio_with_trades(self):
        svc, memory = self._make_service()
        memory.store(TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000,
            exit_price=55000, pnl=5000, pnl_pct=10.0,
        ))
        memory.store(TradeOutcome(
            symbol="ETH", side="SHORT", entry_price=3000,
            exit_price=2800, pnl=200, pnl_pct=6.7,
        ))
        detail = svc.get_portfolio()
        assert detail.summary.total_trades == 2
        assert detail.summary.win_rate == 100.0
        assert detail.summary.total_pnl == 5200.0
        assert detail.profit_factor > 0
        assert detail.asset_allocation != {}

    def test_get_portfolio_with_losses(self):
        svc, memory = self._make_service()
        memory.store(TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000,
            exit_price=40000, pnl=-10000, pnl_pct=-20.0,
        ))
        memory.store(TradeOutcome(
            symbol="ETH", side="LONG", entry_price=3000,
            exit_price=3500, pnl=500, pnl_pct=16.7,
        ))
        detail = svc.get_portfolio()
        assert detail.summary.total_trades == 2
        assert detail.summary.win_rate == 50.0
        assert detail.summary.largest_loss == -10000.0
        assert detail.summary.largest_win == 500.0
        assert detail.profit_factor > 0

    def test_cache_hit(self):
        svc, _ = self._make_service()
        svc.get_portfolio()
        svc.get_portfolio()
        assert svc.get_diagnostics()["cache_hits"] >= 1

    def test_force_refresh(self):
        svc, _ = self._make_service()
        svc.get_portfolio()
        hits_before = svc.get_diagnostics()["cache_hits"]
        svc.get_portfolio(force_refresh=True)
        assert svc.get_diagnostics()["cache_hits"] == hits_before

    def test_invalidate_cache(self):
        svc, _ = self._make_service()
        svc.get_portfolio()
        svc.invalidate_cache()
        hits_before = svc.get_diagnostics()["cache_hits"]
        svc.get_portfolio()
        assert svc.get_diagnostics()["cache_hits"] == hits_before

    def test_equity_curve_empty(self):
        svc, _ = self._make_service()
        curve = svc.get_equity_curve()
        assert curve == []

    def test_equity_curve_with_trades(self):
        svc, memory = self._make_service()
        memory.store(TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000,
            exit_price=55000, pnl=5000, pnl_pct=10.0,
        ))
        svc.get_portfolio()
        curve = svc.get_equity_curve()
        assert len(curve) == 1
        assert curve[0]["equity"] == 15000.0

    def test_equity_curve_limit(self):
        svc, memory = self._make_service()
        for i in range(10):
            memory.store(TradeOutcome(
                symbol=f"X{i}", side="LONG", entry_price=100,
                exit_price=101, pnl=1, pnl_pct=1.0,
            ))
            svc.get_portfolio(force_refresh=True)
        curve = svc.get_equity_curve(limit=5)
        assert len(curve) == 5

    def test_portfolio_summary(self):
        svc, memory = self._make_service()
        memory.store(TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000,
            exit_price=55000, pnl=5000, pnl_pct=10.0,
        ))
        summary = svc.get_portfolio_summary()
        assert summary.total_trades == 1
        assert summary.total_pnl == 5000.0

    def test_get_diagnostics(self):
        svc, _ = self._make_service()
        diag = svc.get_diagnostics()
        assert "total_calls" in diag
        assert "cache_hits" in diag
        assert "equity_points" in diag
        assert "trade_count" in diag

    def test_asset_allocation(self):
        svc, memory = self._make_service()
        memory.store(TradeOutcome(symbol="BTC", side="LONG", entry_price=100, exit_price=200, pnl=100, pnl_pct=100.0))
        memory.store(TradeOutcome(symbol="ETH", side="SHORT", entry_price=100, exit_price=50, pnl=-50, pnl_pct=-50.0))
        detail = svc.get_portfolio()
        assert "BTC" in detail.asset_allocation
        assert "ETH" in detail.asset_allocation

    def test_profit_factor_no_losses(self):
        svc, memory = self._make_service()
        memory.store(TradeOutcome(symbol="BTC", side="LONG", entry_price=100, exit_price=200, pnl=100, pnl_pct=100.0))
        detail = svc.get_portfolio()
        assert detail.profit_factor > 0

    def test_position_summary(self):
        svc, memory = self._make_service()
        memory.store(TradeOutcome(symbol="BTC", side="LONG", entry_price=100, exit_price=200, pnl=100, pnl_pct=100.0))
        detail = svc.get_portfolio()
        assert detail.position_summary["open_count"] == 0
        assert detail.position_summary["closed_count"] == 1
