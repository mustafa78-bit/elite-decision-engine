"""Unit tests for the PortfolioEngine — covers all 14 metrics."""

from datetime import datetime, timedelta, timezone

import pytest
from database import Trade
from portfolio_engine import PortfolioEngine, PortfolioStats


def _seed(session, pnl=0.0, status="OPEN", entry=50000.0, closed_at=None):
    t = Trade(
        symbol="BTCUSDT",
        side="LONG",
        entry=entry,
        stop=entry * 0.98,
        tp1=entry * 1.02,
        rr=1.5,
        status=status,
        pnl=pnl,
        closed_at=closed_at,
    )
    session.add(t)
    session.flush()
    return t


class TestPortfolioEngine:

    def test_empty_portfolio(self, db_session, session_factory):
        engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.total_trades == 0
        assert stats.open_trades == 0
        assert stats.closed_trades == 0
        assert stats.winning_trades == 0
        assert stats.losing_trades == 0
        assert stats.win_rate == 0.0
        assert stats.total_pnl == 0.0
        assert stats.daily_pnl == 0.0
        assert stats.average_win == 0.0
        assert stats.average_loss == 0.0
        assert stats.profit_factor == 0.0
        assert stats.max_drawdown == 0.0
        assert stats.current_open_exposure == 0.0
        assert stats.equity_curve == [10000.0]

    def test_only_wins(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=100.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=200.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=300.0, status="TP_HIT", closed_at=now)

        engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.total_trades == 3
        assert stats.closed_trades == 3
        assert stats.winning_trades == 3
        assert stats.win_rate == 100.0
        assert stats.profit_factor == 999.99

    def test_only_losses(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=-100.0, status="SL_HIT", closed_at=now)
        _seed(db_session, pnl=-200.0, status="SL_HIT", closed_at=now)
        _seed(db_session, pnl=-300.0, status="SL_HIT", closed_at=now)

        engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.total_trades == 3
        assert stats.closed_trades == 3
        assert stats.losing_trades == 3
        assert stats.win_rate == 0.0
        assert stats.profit_factor == 0.0
        assert stats.total_pnl == -600.0

    def test_mixed_wins_and_losses(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=200.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=300.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=-100.0, status="SL_HIT", closed_at=now)

        engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.total_trades == 3
        assert stats.winning_trades == 2
        assert stats.losing_trades == 1
        assert stats.win_rate == pytest.approx(66.67, abs=0.01)
        assert stats.total_pnl == 400.0
        assert stats.average_win == 250.0
        assert stats.average_loss == -100.0
        assert stats.profit_factor == 5.0

    def test_drawdown(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=500.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=1000.0, status="TP_HIT", closed_at=now + timedelta(seconds=1))
        _seed(db_session, pnl=-800.0, status="SL_HIT", closed_at=now + timedelta(seconds=2))
        _seed(db_session, pnl=-200.0, status="SL_HIT", closed_at=now + timedelta(seconds=3))

        engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.closed_trades == 4
        assert stats.max_drawdown == pytest.approx(8.7, abs=0.1)

    def test_equity_curve(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=500.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=1000.0, status="TP_HIT", closed_at=now + timedelta(seconds=1))
        _seed(db_session, pnl=-800.0, status="SL_HIT", closed_at=now + timedelta(seconds=2))

        engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.equity_curve == [10000.0, 10500.0, 11500.0, 10700.0]

    def test_daily_pnl(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        _seed(db_session, pnl=100.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=200.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=300.0, status="TP_HIT", closed_at=yesterday)

        engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.daily_pnl == 300.0
        assert stats.total_pnl == 600.0

    def test_open_trades_exposure(self, db_session, session_factory):
        _seed(db_session, status="OPEN", entry=50000.0)
        _seed(db_session, status="OPEN", entry=30000.0)
        _seed(db_session, status="TP_HIT", pnl=100.0, closed_at=datetime.now(timezone.utc))

        engine = PortfolioEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.total_trades == 3
        assert stats.open_trades == 2
        assert stats.closed_trades == 1
        assert stats.current_open_exposure == 80000.0
