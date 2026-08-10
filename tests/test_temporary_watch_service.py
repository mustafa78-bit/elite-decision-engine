"""Tests for TemporaryWatchService -- the manually-fed, auto-expiring
watchlist that feeds scanner/core.py's OpportunityScanner alongside
config.FIXED_COIN_UNIVERSE.
"""

from datetime import UTC, datetime, timedelta

from services.temporary_watch_service import TemporaryWatchService


class TestTemporaryWatchService:

    def test_add_symbol_then_list_active(self, session_factory):
        svc = TemporaryWatchService(session_factory=session_factory)
        svc.add_symbol("PEPEUSDT", days=7, note="TradingView breakout setup")

        active = svc.list_active()
        assert len(active) == 1
        assert active[0]["symbol"] == "PEPEUSDT"
        assert active[0]["note"] == "TradingView breakout setup"

    def test_active_symbols_returns_plain_deduplicated_list(self, session_factory):
        svc = TemporaryWatchService(session_factory=session_factory)
        svc.add_symbol("PEPEUSDT")
        svc.add_symbol("WIFUSDT")

        assert sorted(svc.active_symbols()) == ["PEPEUSDT", "WIFUSDT"]

    def test_add_symbol_normalizes_to_uppercase(self, session_factory):
        svc = TemporaryWatchService(session_factory=session_factory)
        svc.add_symbol("pepeusdt")
        assert svc.active_symbols() == ["PEPEUSDT"]

    def test_expired_watch_excluded_from_active_symbols(self, session_factory, db_session):
        from database import TemporaryWatch

        svc = TemporaryWatchService(session_factory=session_factory)
        expired = TemporaryWatch(
            symbol="OLDCOINUSDT",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        db_session.add(expired)
        db_session.commit()

        assert svc.active_symbols() == []
        assert svc.list_active() == []

    def test_add_symbol_on_already_active_symbol_refreshes_not_duplicates(self, session_factory):
        # Regression guard for the upsert semantics the sprint doc requires:
        # re-adding a symbol that's still active must extend its expiry,
        # not create a second row (which active_symbols() would then have
        # to de-dup around, and list_active() would show twice).
        svc = TemporaryWatchService(session_factory=session_factory)
        svc.add_symbol("PEPEUSDT", days=1)
        first = svc.list_active()
        assert len(first) == 1
        first_id = first[0]["id"]

        svc.add_symbol("PEPEUSDT", days=30)
        second = svc.list_active()
        assert len(second) == 1
        assert second[0]["id"] == first_id
        assert second[0]["expires_at"] > first[0]["expires_at"]

    def test_remove_symbol(self, session_factory):
        svc = TemporaryWatchService(session_factory=session_factory)
        svc.add_symbol("PEPEUSDT")
        assert svc.remove_symbol("PEPEUSDT") is True
        assert svc.active_symbols() == []

    def test_remove_symbol_not_found_returns_false(self, session_factory):
        svc = TemporaryWatchService(session_factory=session_factory)
        assert svc.remove_symbol("NOPEUSDT") is False
