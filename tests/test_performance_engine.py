"""Unit tests for the PerformanceEngine — every metric verified."""

from datetime import datetime, timedelta, timezone

import pytest
from database import Trade
from performance_engine import PerformanceEngine, PerformanceStats


def _seed(session, entry=50000.0, stop=49250.0, side="LONG", pnl=0.0,
          status="OPEN", created_at=None, closed_at=None):
    t = Trade(
        symbol="BTCUSDT",
        side=side,
        entry=entry,
        stop=stop,
        tp1=entry * 1.02,
        rr=1.5,
        status=status,
        pnl=pnl,
        closed_at=closed_at,
    )
    session.add(t)
    session.flush()
    return t


class TestPerformanceEngine:

    def test_empty_portfolio(self, db_session, session_factory):
        engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.sharpe_ratio == 0.0
        assert stats.sortino_ratio == 0.0
        assert stats.profit_factor == 0.0
        assert stats.expectancy == 0.0
        assert stats.recovery_factor == 0.0
        assert stats.calmar_ratio == 0.0
        assert stats.average_r_multiple == 0.0
        assert stats.average_holding_hours == 0.0
        assert stats.consecutive_wins == 0
        assert stats.consecutive_losses == 0
        assert stats.best_trade == 0.0
        assert stats.worst_trade == 0.0

    def test_all_winners(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=1000.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=2000.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=3000.0, status="TP_HIT", closed_at=now)

        engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.sharpe_ratio == pytest.approx(2.0, abs=0.01)
        assert stats.sortino_ratio == 999.99
        assert stats.profit_factor == 999.99
        assert stats.consecutive_wins == 3
        assert stats.consecutive_losses == 0
        assert stats.best_trade == 3000.0
        assert stats.worst_trade == 1000.0

    def test_all_losers(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=-1000.0, status="SL_HIT", closed_at=now)
        _seed(db_session, pnl=-2000.0, status="SL_HIT", closed_at=now)
        _seed(db_session, pnl=-3000.0, status="SL_HIT", closed_at=now)

        engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.sharpe_ratio == pytest.approx(-2.0, abs=0.01)
        assert stats.sortino_ratio == pytest.approx(-0.93, abs=0.02)
        assert stats.profit_factor == 0.0
        assert stats.consecutive_wins == 0
        assert stats.consecutive_losses == 3
        assert stats.best_trade == -1000.0
        assert stats.worst_trade == -3000.0

    def test_mixed_trades(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=500.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=-200.0, status="SL_HIT", closed_at=now)
        _seed(db_session, pnl=300.0, status="TP_HIT", closed_at=now)

        engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        # Returns: [500/50000=0.01, -200/50000=-0.004, 300/50000=0.006]
        # mean = (0.01 - 0.004 + 0.006)/3 = 0.004
        # stdev ≈ 0.0072
        assert stats.sharpe_ratio == pytest.approx(0.55, abs=0.05)
        # Profit Factor = 800 / 200 = 4.0
        assert stats.profit_factor == 4.0
        # Expectancy = (2/3 * 400) - (1/3 * 200) = 266.67 - 66.67 = 200.0
        assert stats.expectancy == pytest.approx(200.0, abs=0.01)
        assert stats.consecutive_wins == 1
        assert stats.best_trade == 500.0
        assert stats.worst_trade == -200.0

    def test_expectancy(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=1000.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=1000.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=-500.0, status="SL_HIT", closed_at=now)
        _seed(db_session, pnl=-500.0, status="SL_HIT", closed_at=now)

        engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        # win_rate = 2/4 = 0.5, loss_rate = 2/4 = 0.5
        # avg_win = 1000, avg_loss = -500
        # expectancy = 0.5 * 1000 - 0.5 * 500 = 500 - 250 = 250
        assert stats.expectancy == 250.0

    def test_r_multiple(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        # risk = abs(50000 - 49250) = 750
        _seed(db_session, entry=50000.0, stop=49250.0, pnl=1500.0,
              status="TP_HIT", closed_at=now)  # R = 1500/750 = 2.0
        _seed(db_session, entry=50000.0, stop=49250.0, pnl=-375.0,
              status="SL_HIT", closed_at=now)   # R = -375/750 = -0.5
        _seed(db_session, entry=50000.0, stop=49250.0, pnl=750.0,
              status="TP_HIT", closed_at=now)   # R = 750/750 = 1.0

        engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        # avg_r = (2.0 - 0.5 + 1.0) / 3 = 2.5 / 3 = 0.833...
        assert stats.average_r_multiple == pytest.approx(0.83, abs=0.01)

    def test_holding_time(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        created = now - timedelta(hours=24)
        _seed(db_session, pnl=500.0, status="TP_HIT",
              closed_at=now)
        # Manually set created_at via query since the fixture autocreates it
        trade = db_session.query(Trade).first()
        trade.created_at = created
        db_session.flush()

        engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.average_holding_hours == pytest.approx(24.0, abs=0.1)

    def test_consecutive_streaks(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        # pattern: W, W, L, L, L, W
        _seed(db_session, pnl=100.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=200.0, status="TP_HIT",
              closed_at=now + timedelta(seconds=1))
        _seed(db_session, pnl=-100.0, status="SL_HIT",
              closed_at=now + timedelta(seconds=2))
        _seed(db_session, pnl=-200.0, status="SL_HIT",
              closed_at=now + timedelta(seconds=3))
        _seed(db_session, pnl=-300.0, status="SL_HIT",
              closed_at=now + timedelta(seconds=4))
        _seed(db_session, pnl=400.0, status="TP_HIT",
              closed_at=now + timedelta(seconds=5))

        engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        assert stats.consecutive_wins == 2
        assert stats.consecutive_losses == 3

    def test_recovery_and_calmar(self, db_session, session_factory):
        now = datetime.now(timezone.utc)
        _seed(db_session, pnl=2000.0, status="TP_HIT", closed_at=now)
        _seed(db_session, pnl=3000.0, status="TP_HIT",
              closed_at=now + timedelta(seconds=1))
        _seed(db_session, pnl=-4000.0, status="SL_HIT",
              closed_at=now + timedelta(seconds=2))
        _seed(db_session, pnl=1000.0, status="TP_HIT",
              closed_at=now + timedelta(seconds=3))

        engine = PerformanceEngine(session_factory=session_factory, initial_equity=10000)
        stats = engine.stats()
        # cum pnl: [2000, 5000, 1000, 2000]
        # peak pnl: 2000→5000→5000→5000
        # dd dollars: 0→0→4000→3000, max_dd=4000
        # recovery = 2000/4000 = 0.5
        assert stats.recovery_factor == 0.5
        # equity: [10000, 12000, 15000, 11000, 12000]
        # peak_eq: 10000→12000→15000→15000→15000
        # dd_pct: 0→0→0→0.267→0.2, max_dd_pct=0.267
        # total_return_pct = 2000/10000*100 = 20%
        # calmar = 20 / (0.267*100) = 20/26.7 = 0.75
        assert stats.calmar_ratio == pytest.approx(0.75, abs=0.02)
