"""Tests for Sprint 39-43 routes."""

import pytest

from api.routes.backtest import router as backtest_router
from api.routes.journal import router as journal_router
from api.routes.regime import router as regime_router
from api.routes.signals_ranking import router as signals_ranking_router


class TestRegimeRoute:
    def test_regime_router_exists(self):
        assert len(regime_router.routes) == 1

    def test_regime_path(self):
        route = regime_router.routes[0]
        assert route.path == "/regime"
        assert "GET" in route.methods


class TestSignalsRankingRoute:
    def test_ranking_router_exists(self):
        assert len(signals_ranking_router.routes) == 1

    def test_ranking_path(self):
        route = signals_ranking_router.routes[0]
        assert route.path == "/signals/ranking"
        assert "GET" in route.methods


class TestJournalRoute:
    def test_journal_router_exists(self):
        assert len(journal_router.routes) >= 1

    def test_journal_paths(self):
        paths = {r.path for r in journal_router.routes}
        assert "/journal" in paths
        assert "/journal/{entry_id}" in paths


class TestBacktestRoute:
    def test_backtest_router_exists(self):
        assert len(backtest_router.routes) == 1

    def test_backtest_path(self):
        route = backtest_router.routes[0]
        assert route.path == "/backtest"
        assert "GET" in route.methods


class TestJournalDB:
    def test_create_and_list_journal(self, db_session):
        from database import JournalEntry

        entry = JournalEntry(
            symbol="BTC",
            side="LONG",
            entry_price=50000.0,
            score=0.85,
            confidence=90.0,
            entry_reason="Bullish breakout",
            result="PENDING",
        )
        db_session.add(entry)
        db_session.flush()

        rows = db_session.query(JournalEntry).all()
        assert len(rows) == 1
        assert rows[0].symbol == "BTC"
        assert rows[0].entry_price == 50000.0

    def test_journal_pnl_update(self, db_session):
        from database import JournalEntry

        entry = JournalEntry(
            symbol="ETH",
            side="SHORT",
            entry_price=3000.0,
            exit_price=2800.0,
            pnl=200.0,
            result="WIN",
            entry_reason="Overbought",
        )
        db_session.add(entry)
        db_session.flush()

        rows = db_session.query(JournalEntry).all()
        assert len(rows) == 1
        assert rows[0].pnl == 200.0
        assert rows[0].result == "WIN"

    def test_delete_journal(self, db_session):
        from database import JournalEntry

        entry = JournalEntry(symbol="SOL", side="LONG", entry_price=100.0)
        db_session.add(entry)
        db_session.flush()
        assert db_session.query(JournalEntry).count() == 1

        db_session.delete(entry)
        db_session.flush()
        assert db_session.query(JournalEntry).count() == 0


@pytest.fixture(autouse=True)
def _patch_sessions(monkeypatch, session_factory):
    monkeypatch.setattr("api.routes.journal.get_session", session_factory)
    monkeypatch.setattr("api.routes.backtest.get_session", session_factory)
    monkeypatch.setattr("api.routes.signals_ranking.get_session", session_factory)
