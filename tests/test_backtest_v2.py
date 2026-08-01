"""Tests for BacktestEngineV2."""

from datetime import datetime, timedelta, timezone

from scoring.backtest_v2 import BacktestEngineV2, BacktestResult


class TestBacktestV2:
    def test_empty(self, session_factory):
        engine = BacktestEngineV2(session_factory=session_factory)
        result = engine.run(limit=10)
        assert result.total_trades == 0
        assert result.win_rate == 0.0

    def test_with_session(self, db_session):
        from database import Trade

        now = datetime.now(timezone.utc)
        db_session.add_all([
            Trade(symbol="BTC", side="LONG", entry=100, status="CLOSED", pnl=50, close_reason="TP_HIT", created_at=now),
            Trade(symbol="ETH", side="SHORT", entry=200, status="CLOSED", pnl=-20, close_reason="SL_HIT", created_at=now),
            Trade(symbol="BTC", side="LONG", entry=150, status="CLOSED", pnl=30, close_reason="TP_HIT", created_at=now),
        ])
        db_session.flush()

        engine = BacktestEngineV2(session=db_session)
        result = engine.run(limit=100)
        assert result.total_trades == 3
        assert result.wins == 2
        assert result.losses == 1
        assert result.win_rate == 66.7
        assert result.total_pnl == 60.0

    def test_advanced_metrics(self, db_session):
        from database import Trade

        now = datetime.now(timezone.utc)
        db_session.add_all([
            Trade(symbol="A", side="LONG", entry=100, status="CLOSED", pnl=100, close_reason="TP_HIT", created_at=now),
            Trade(symbol="B", side="LONG", entry=100, status="CLOSED", pnl=200, close_reason="TP_HIT", created_at=now),
            Trade(symbol="C", side="SHORT", entry=100, status="CLOSED", pnl=-50, close_reason="SL_HIT", created_at=now),
            Trade(symbol="D", side="SHORT", entry=100, status="CLOSED", pnl=-30, close_reason="SL_HIT", created_at=now),
            Trade(symbol="E", side="LONG", entry=100, status="CLOSED", pnl=150, close_reason="TP_HIT", created_at=now),
        ])
        db_session.flush()

        engine = BacktestEngineV2(session=db_session)
        result = engine.run(limit=100)
        assert result.total_trades == 5
        assert result.sortino > 0
        assert result.calmar > 0
        assert result.expectancy > 0
        assert "LONG" in result.win_rate_by_direction
        assert "SHORT" in result.win_rate_by_direction

    def test_strategy_filter(self, db_session):
        from database import Trade

        now = datetime.now(timezone.utc)
        db_session.add_all([
            Trade(symbol="A", side="LONG", entry=100, status="CLOSED", pnl=50, close_reason="TP_HIT", created_at=now),
            Trade(symbol="B", side="SHORT", entry=200, status="CLOSED", pnl=-10, close_reason="SL_HIT", created_at=now),
        ])
        db_session.flush()

        engine = BacktestEngineV2(session=db_session)
        longs = engine.run(strategy="long", limit=100)
        assert longs.total_trades == 1
        assert longs.wins == 1

        shorts = engine.run(strategy="short", limit=100)
        assert shorts.total_trades == 1
        assert shorts.losses == 1

    def test_monthly_pnl(self, db_session):
        from database import Trade

        jan = datetime(2025, 1, 15, tzinfo=timezone.utc)
        feb = datetime(2025, 2, 15, tzinfo=timezone.utc)
        db_session.add_all([
            Trade(symbol="A", side="LONG", entry=100, status="CLOSED", pnl=100, close_reason="TP_HIT", created_at=jan),
            Trade(symbol="B", side="LONG", entry=100, status="CLOSED", pnl=200, close_reason="TP_HIT", created_at=feb),
        ])
        db_session.flush()

        engine = BacktestEngineV2(session=db_session)
        result = engine.run(limit=100)
        assert "2025-01" in result.monthly_pnl
        assert "2025-02" in result.monthly_pnl
        assert result.monthly_pnl["2025-01"] == 100.0
        assert result.monthly_pnl["2025-02"] == 200.0

    def test_walk_forward_empty(self, session_factory):
        engine = BacktestEngineV2(session_factory=session_factory)
        wf = engine.walk_forward()
        assert len(wf.windows) == 0

    def test_walk_forward(self, db_session):
        from database import Trade
        import random

        random.seed(42)
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for i in range(400):
            pnl = random.gauss(5, 15)
            db_session.add(
                Trade(
                    symbol="BTC", side="LONG", entry=100,
                    status="CLOSED", pnl=round(pnl, 2),
                    close_reason="TP_HIT" if pnl > 0 else "SL_HIT",
                    created_at=start + timedelta(hours=i),
                )
            )
        db_session.flush()

        engine = BacktestEngineV2(session=db_session)
        wf = engine.walk_forward(window_size_days=5, test_size_days=1, step_days=1, max_windows=3)
        assert len(wf.windows) <= 3
        assert wf.avg_train_sharpe != 0
        assert wf.avg_test_sharpe != 0

    def test_walk_forward_too_short(self, session_factory):
        engine = BacktestEngineV2(session_factory=session_factory)
        wf = engine.walk_forward()
        assert wf.combined_test_pnl == 0.0
