"""Tests for performance intelligence."""

from datetime import datetime, timezone

import pytest

from scoring.performance_intelligence import PerformanceIntelligence


@pytest.fixture
def pi(db_session):
    return PerformanceIntelligence(session=db_session)


@pytest.fixture
def sample_trades(db_session):
    from database import Trade

    trades = [
            Trade(symbol="BTC", side="LONG", entry=100.0, status="CLOSED",
                  pnl=50.0, close_reason="TP_HIT", created_at=datetime.now(timezone.utc)),
            Trade(symbol="ETH", side="SHORT", entry=200.0, status="CLOSED",
                  pnl=-30.0, close_reason="SL_HIT", created_at=datetime.now(timezone.utc)),
            Trade(symbol="BTC", side="LONG", entry=150.0, status="CLOSED",
                  pnl=20.0, close_reason="TP_HIT", created_at=datetime.now(timezone.utc)),
            Trade(symbol="ETH", side="LONG", entry=250.0, status="OPEN",
                  pnl=None, created_at=datetime.now(timezone.utc)),
            Trade(symbol="SOL", side="SHORT", entry=50.0, status="CLOSED",
                  pnl=-10.0, close_reason="SL_HIT", created_at=datetime.now(timezone.utc)),
    ]
    for t in trades:
        db_session.add(t)
    db_session.flush()
    return trades


class TestPerformanceIntelligence:
    def test_empty_analyze(self, pi):
        result = pi.analyze(limit=100)
        assert result["strategy_comparison"] == []
        assert result["best_conditions"] == []
        assert result["failure_analysis"].get("total_losses", 0) == 0

    def test_strategy_comparison(self, pi, sample_trades, db_session):
        result = pi.analyze(limit=100)
        comps = result["strategy_comparison"]
        assert len(comps) >= 2
        longs = [c for c in comps if c["name"] == "LONG"]
        shorts = [c for c in comps if c["name"] == "SHORT"]
        assert len(longs) == 1
        assert shorts[0]["losses"] >= 1

    def test_best_conditions(self, pi, sample_trades, db_session):
        result = pi.analyze(limit=100)
        conditions = result["best_conditions"]
        assert len(conditions) >= 1
        assert any(c["condition"] == "TP_HIT" for c in conditions)

    def test_failure_analysis(self, pi, sample_trades, db_session):
        result = pi.analyze(limit=100)
        failure = result["failure_analysis"]
        assert failure["total_losses"] >= 2
        assert failure["avg_loss"] > 0

    def test_summary(self, pi, sample_trades, db_session):
        result = pi.analyze(limit=100)
        summary = result["summary"]
        assert summary["total_trades"] >= 5
        assert summary["closed_trades"] >= 4
        assert summary["wins"] >= 2
        assert summary["losses"] >= 2
        assert summary["total_pnl"] != 0
        assert summary["profit_factor"] > 0

    def test_max_drawdown(self, pi):
        pnls = [10.0, -5.0, 20.0, -15.0, 5.0]
        dd = pi._max_drawdown(pnls)
        assert dd >= 0

    def test_sharpe(self, pi):
        pnls = [1.0, 2.0, 1.5, -0.5, 0.0]
        s = pi._sharpe(pnls)
        assert s != 0.0

    def test_sharpe_insufficient(self, pi):
        assert pi._sharpe([1.0]) == 0.0
        assert pi._sharpe([]) == 0.0

    def test_profit_factor(self, pi, db_session):
        from database import Trade

        wins = [Trade(pnl=100), Trade(pnl=50)]
        losses = [Trade(pnl=-30), Trade(pnl=-20)]
        pf = pi._profit_factor(wins, losses)
        assert pf == 3.0
