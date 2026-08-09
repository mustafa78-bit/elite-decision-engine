from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from database import Notification, PaperTrade, Trade, UserSettings, Watchlist
from dto.notifications_detail import NotificationDetailDTO, NotificationStatsDTO
from dto.portfolio_detail import (
    PortfolioDistributionDTO,
    PortfolioPerformanceDTO,
    PortfolioRiskDTO,
    PortfolioSummaryDTO,
)
from dto.preferences import LayoutConfigDTO, ThemeConfigDTO, UserPreferencesDTO
from dto.watchlists import WatchlistCreateDTO, WatchlistDTO, WatchlistUpdateDTO


class TestBatch2DTOs:

    def test_user_preferences_to_dict(self):
        dto = UserPreferencesDTO(timezone="EST", theme="light")
        d = dto.to_dict()
        assert d["timezone"] == "EST"
        assert d["theme"] == "light"

    def test_theme_config_to_dict(self):
        dto = ThemeConfigDTO(theme="light")
        d = dto.to_dict()
        assert d["primary_color"] == "#3b82f6"

    def test_layout_config_to_dict(self):
        dto = LayoutConfigDTO(sidebar_collapsed=True)
        d = dto.to_dict()
        assert d["sidebar_collapsed"] is True

    def test_watchlist_dto(self):
        dto = WatchlistDTO(id=1, name="My List", symbols=["BTCUSDT", "ETHUSDT"])
        d = dto.to_dict()
        assert d["name"] == "My List"
        assert len(d["symbols"]) == 2

    def test_watchlist_create_dto(self):
        dto = WatchlistCreateDTO(name="Test", symbols=["SOLUSDT"])
        assert dto.name == "Test"

    def test_watchlist_update_dto(self):
        dto = WatchlistUpdateDTO(add_symbols=["ADAUSDT"])
        assert dto.add_symbols == ["ADAUSDT"]

    def test_notification_detail_dto(self):
        dto = NotificationDetailDTO(id=1, event_type="TRADE_OPENED", read=False)
        d = dto.to_dict()
        assert d["event_type"] == "TRADE_OPENED"

    def test_notification_stats_dto(self):
        dto = NotificationStatsDTO(total=10, unread=3)
        d = dto.to_dict()
        assert d["unread"] == 3

    def test_portfolio_summary_dto(self):
        dto = PortfolioSummaryDTO(total_pnl=1500.50, total_trades=25, win_rate=60.0)
        d = dto.to_dict()
        assert d["win_rate"] == 60.0

    def test_portfolio_distribution_dto(self):
        dto = PortfolioDistributionDTO(by_side={"LONG": 10, "SHORT": 5})
        d = dto.to_dict()
        assert d["by_side"]["LONG"] == 10

    def test_portfolio_performance_dto(self):
        dto = PortfolioPerformanceDTO(equity_curve=[])
        d = dto.to_dict()
        assert d["equity_curve"] == []

    def test_portfolio_risk_dto(self):
        dto = PortfolioRiskDTO(current_exposure=5000.0, var_95=-200.0)
        d = dto.to_dict()
        assert d["var_95"] == -200.0


class TestPortfolioService:

    def test_empty_portfolio_summary(self, db_session):
        from config import ACCOUNT_EQUITY
        from services.portfolio_service import PortfolioService
        svc = PortfolioService(session_factory=lambda: db_session)
        s = svc.summary()
        assert s["total_trades"] == 0
        assert s["open_trades"] == 0
        assert s["total_balance"] == round(ACCOUNT_EQUITY, 2)

    def test_portfolio_with_trades(self, db_session):
        from config import ACCOUNT_EQUITY
        from services.portfolio_service import PortfolioService
        now = datetime.now(UTC)
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                             tp1=52000, rr=2.0, status="TP_HIT", pnl=2000.0,
                             created_at=now - timedelta(days=2), closed_at=now - timedelta(days=2)))
        db_session.add(Trade(symbol="ETHUSDT", side="SHORT", entry=3000, stop=3100,
                             tp1=2800, rr=2.0, status="SL_HIT", pnl=-500.0,
                             created_at=now - timedelta(days=1), closed_at=now - timedelta(days=1)))
        db_session.flush()
        svc = PortfolioService(session_factory=lambda: db_session)
        s = svc.summary()
        assert s["total_trades"] == 2
        assert s["win_rate"] == 50.0
        assert s["total_pnl"] == 1500.0
        assert s["total_balance"] == round(ACCOUNT_EQUITY + 1500.0, 2)

    def test_portfolio_distribution(self, db_session):
        from services.portfolio_service import PortfolioService
        now = datetime.now(UTC)
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                             tp1=52000, rr=2.0, status="TP_HIT", pnl=2000.0, created_at=now))
        db_session.add(Trade(symbol="ETHUSDT", side="SHORT", entry=3000, stop=3100,
                             tp1=2800, rr=2.0, status="SL_HIT", pnl=-500.0, created_at=now))
        db_session.flush()
        svc = PortfolioService(session_factory=lambda: db_session)
        d = svc.distribution()
        assert len(d["by_symbol"]) == 2
        assert d["by_side"]["LONG"] == 1

    def test_portfolio_performance(self, db_session):
        from services.portfolio_service import PortfolioService
        now = datetime.now(UTC)
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                             tp1=52000, rr=2.0, status="TP_HIT", pnl=2000.0,
                             created_at=now - timedelta(days=2), closed_at=now - timedelta(days=2)))
        db_session.flush()
        svc = PortfolioService(session_factory=lambda: db_session)
        p = svc.performance()
        assert len(p["equity_curve"]) == 1
        assert len(p["daily_pnl"]) == 1

    def test_portfolio_risk_empty(self, db_session):
        from services.portfolio_service import PortfolioService
        svc = PortfolioService(session_factory=lambda: db_session)
        r = svc.risk_metrics()
        assert r["current_exposure"] == 0.0

    def test_portfolio_risk_exposure_and_average_risk_distance(self, db_session):
        from services.portfolio_service import PortfolioService
        # Add open trade to check exposure based on entry price
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", entry=50000.0, stop=49000.0,
                             status="OPEN", pnl=10.0)) # pnl should not be used for exposure
        # Add closed trades to check risk_per_trade distance calculation
        now = datetime.now(UTC)
        db_session.add(Trade(symbol="ETHUSDT", side="SHORT", entry=3000.0, stop=3100.0,
                             status="SL_HIT", pnl=-100.0, created_at=now, closed_at=now))
        db_session.add(Trade(symbol="SOLUSDT", side="LONG", entry=150.0, stop=140.0,
                             status="TP_HIT", pnl=200.0, created_at=now, closed_at=now))
        db_session.flush()

        svc = PortfolioService(session_factory=lambda: db_session)
        r = svc.risk_metrics()

        # Exposure should be entry price of the open trade: 50000.0
        assert r["current_exposure"] == 50000.0

        # Concentration should reflect absolute entry price (100% BTCUSDT since it's the only open trade)
        assert r["symbol_concentration"] == {"BTCUSDT": 1.0}

        # Average risk per trade should use abs(entry - stop) distances of the closed trades:
        # Trade 1: abs(3000.0 - 3100.0) = 100.0
        # Trade 2: abs(150.0 - 140.0) = 10.0
        # Average: (100.0 + 10.0) / 2 = 55.0
        assert r["risk_per_trade"] == 55.0

    def test_portfolio_full(self, db_session):
        from services.portfolio_service import PortfolioService
        svc = PortfolioService(session_factory=lambda: db_session)
        f = svc.full_portfolio()
        assert "summary" in f
        assert "distribution" in f
        assert "performance" in f
        assert "risk" in f

    def test_summary_uses_real_dollar_pnl_not_raw_per_unit_pnl(self, db_session):
        # Trade.pnl is a raw per-unit price delta, not a dollar amount (see
        # services/pnl.py) -- a trade with quantity=0.1 and a $50 per-unit
        # move has real dollar PnL of $5, not $50.
        from services.portfolio_service import PortfolioService
        now = datetime.now(UTC)
        trade = Trade(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                      tp1=52000, rr=2.0, status="TP_HIT", pnl=50.0,
                      created_at=now, closed_at=now)
        db_session.add(trade)
        db_session.flush()
        db_session.add(PaperTrade(
            position_id=trade.id, symbol="BTCUSDT", side="LONG",
            entry=50000, quantity=0.1, status="TP_HIT",
        ))
        db_session.flush()

        svc = PortfolioService(session_factory=lambda: db_session)
        s = svc.summary()

        assert s["total_pnl"] == 5.0
        assert s["realized_pnl"] == 5.0
        assert s["best_trade_pnl"] == 5.0

    def test_risk_exposure_uses_real_notional_not_raw_entry_price(self, db_session):
        # Same bug class in _compute_risk: an open trade's exposure should be
        # entry_price * real quantity, not the raw per-unit entry price.
        from services.portfolio_service import PortfolioService
        trade = Trade(symbol="BTCUSDT", side="LONG", entry=50000.0, stop=49000.0, status="OPEN")
        db_session.add(trade)
        db_session.flush()
        db_session.add(PaperTrade(
            position_id=trade.id, symbol="BTCUSDT", side="LONG",
            entry=50000.0, quantity=0.1, status="OPEN",
        ))
        db_session.flush()

        svc = PortfolioService(session_factory=lambda: db_session)
        r = svc.risk_metrics()

        assert r["current_exposure"] == 5000.0


class TestTimelineService:

    def test_signal_timeline_nonexistent(self, db_session):
        from services.timeline_service import TimelineService
        svc = TimelineService(session_factory=lambda: db_session)
        events = svc.signal_timeline(999)
        assert events == []

    def test_global_timeline_empty(self, db_session):
        from services.timeline_service import TimelineService
        svc = TimelineService(session_factory=lambda: db_session)
        result = svc.global_timeline()
        assert result["total"] == 0
        assert result["events"] == []


class TestWidgetService:

    def test_widget_kpi(self, db_session):
        from services.widget_service import WidgetService
        svc = WidgetService(session_factory=lambda: db_session)
        result = svc.get_widget("kpi")
        assert "kpis" in result

    def test_widget_portfolio_empty(self, db_session):
        from services.widget_service import WidgetService
        svc = WidgetService(session_factory=lambda: db_session)
        result = svc.get_widget("portfolio")
        assert result["total_trades"] == 0

    def test_widget_monitoring(self, db_session):
        from services.widget_service import WidgetService
        svc = WidgetService(session_factory=lambda: db_session)
        result = svc.get_widget("monitoring")
        assert "status" in result

    def test_widget_notifications_empty(self, db_session):
        from services.widget_service import WidgetService
        svc = WidgetService(session_factory=lambda: db_session)
        result = svc.get_widget("notifications")
        assert result["unread"] == 0

    def test_widget_unknown_type(self, db_session):
        from services.widget_service import WidgetService
        svc = WidgetService(session_factory=lambda: db_session)
        result = svc.get_widget("nonexistent")
        assert "error" in result

    def test_get_all_widgets(self, db_session):
        from services.widget_service import WidgetService
        svc = WidgetService(session_factory=lambda: db_session)
        result = svc.get_all_widgets()
        assert "kpi" in result
        assert "portfolio" in result
        assert "monitoring" in result
        assert "notifications" in result


class TestPreferencesService:

    def test_get_preferences_nonexistent(self, db_session):
        from services.preferences_service import PreferencesService
        svc = PreferencesService(session_factory=lambda: db_session)
        result = svc.get_preferences(999)
        assert result is None

    def test_upsert_preferences(self, db_session):
        from services.preferences_service import PreferencesService
        svc = PreferencesService(session_factory=lambda: db_session)
        result = svc.upsert_preferences(1, {"theme": "light", "timezone": "EST"})
        assert result["theme"] == "light"
        assert result["timezone"] == "EST"

    def test_update_theme(self, db_session):
        from services.preferences_service import PreferencesService
        svc = PreferencesService(session_factory=lambda: db_session)
        result = svc.update_theme(1, "light")
        assert result["theme"] == "light"

    def test_update_layout(self, db_session):
        from services.preferences_service import PreferencesService
        svc = PreferencesService(session_factory=lambda: db_session)
        layout = {"sidebar_collapsed": True}
        result = svc.update_layout(1, layout)
        assert result["layout_config"]["sidebar_collapsed"] is True

    def test_get_preferences_after_upsert(self, db_session):
        from services.preferences_service import PreferencesService
        svc = PreferencesService(session_factory=lambda: db_session)
        svc.upsert_preferences(1, {"theme": "dark"})
        result = svc.get_preferences(1)
        assert result is not None
        assert result["theme"] == "dark"


class TestWatchlistService:

    def test_list_watchlists_empty(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        result = svc.list_watchlists()
        assert result == []

    def test_create_and_get_watchlist(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Test", user_id=1, symbols=["BTCUSDT"])
        assert created["name"] == "Test"
        assert created["symbols"] == ["BTCUSDT"]
        got = svc.get_watchlist(created["id"], user_id=1)
        assert got is not None
        assert got["id"] == created["id"]

    def test_create_watchlist_defaults(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Default", user_id=1)
        assert created["symbols"] == []

    def test_update_watchlist_name(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Old", user_id=1)
        updated = svc.update_watchlist(created["id"], user_id=1, data={"name": "New"})
        assert updated["name"] == "New"

    def test_add_symbol(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Test", user_id=1)
        updated = svc.add_symbol(created["id"], user_id=1, symbol="ETHUSDT")
        assert "ETHUSDT" in updated["symbols"]

    def test_remove_symbol(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Test", user_id=1, symbols=["BTCUSDT", "ETHUSDT"])
        updated = svc.remove_symbol(created["id"], user_id=1, symbol="BTCUSDT")
        assert "BTCUSDT" not in updated["symbols"]

    def test_delete_watchlist(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Test", user_id=1)
        assert svc.delete_watchlist(created["id"], user_id=1) is True
        assert svc.get_watchlist(created["id"], user_id=1) is None

    def test_delete_nonexistent(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        assert svc.delete_watchlist(999, user_id=1) is False

    def test_add_symbol_nonexistent(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        assert svc.add_symbol(999, user_id=1, symbol="BTCUSDT") is None

    def test_get_watchlist_owned_by_another_user_returns_none(self, db_session):
        # The IDOR this fix closes: user 2 must not be able to read user 1's
        # watchlist by ID alone.
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="User1's list", user_id=1)
        assert svc.get_watchlist(created["id"], user_id=2) is None

    def test_update_watchlist_owned_by_another_user_returns_none(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="User1's list", user_id=1)
        result = svc.update_watchlist(created["id"], user_id=2, data={"name": "Hijacked"})
        assert result is None
        # Confirm it was genuinely untouched, not silently updated then hidden.
        assert svc.get_watchlist(created["id"], user_id=1)["name"] == "User1's list"

    def test_delete_watchlist_owned_by_another_user_fails(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="User1's list", user_id=1)
        assert svc.delete_watchlist(created["id"], user_id=2) is False
        assert svc.get_watchlist(created["id"], user_id=1) is not None


class TestNotificationService:

    def test_list_notifications_empty(self, db_session):
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        result = svc.list_notifications(user_id=1)
        assert result["total"] == 0
        assert result["notifications"] == []

    def test_create_and_list(self, db_session):
        n = Notification(event_type="TRADE_OPENED", payload={"trade_id": 1}, user_id=1)
        db_session.add(n)
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        result = svc.list_notifications(user_id=1)
        assert result["total"] == 1
        assert result["notifications"][0]["event_type"] == "TRADE_OPENED"

    def test_list_notifications_excludes_other_users(self, db_session):
        db_session.add(Notification(event_type="TRADE_OPENED", user_id=1))
        db_session.add(Notification(event_type="TRADE_CLOSED", user_id=2))
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        result = svc.list_notifications(user_id=1)
        assert result["total"] == 1
        assert result["notifications"][0]["event_type"] == "TRADE_OPENED"

    def test_mark_read(self, db_session):
        n = Notification(event_type="TEST", user_id=1)
        db_session.add(n)
        db_session.flush()
        nid = n.id
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        assert svc.mark_read(nid, user_id=1) is True
        result = svc.get_notification(nid, user_id=1)
        assert result["read"] is True

    def test_mark_read_nonexistent(self, db_session):
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        assert svc.mark_read(999, user_id=1) is False

    def test_mark_read_wrong_user_returns_false(self, db_session):
        n = Notification(event_type="TEST", user_id=2)
        db_session.add(n)
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        assert svc.mark_read(n.id, user_id=1) is False

    def test_mark_all_read(self, db_session):
        for i in range(3):
            db_session.add(Notification(event_type="TEST", user_id=1))
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        count = svc.mark_all_read(user_id=1)
        assert count == 3
        stats = svc.stats(user_id=1)
        assert stats["unread"] == 0

    def test_delete_notification(self, db_session):
        n = Notification(event_type="TEST", user_id=1)
        db_session.add(n)
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        assert svc.delete_notification(n.id, user_id=1) is True
        assert svc.get_notification(n.id, user_id=1) is None

    def test_delete_all_read(self, db_session):
        n = Notification(event_type="TEST", read=True, user_id=1)
        db_session.add(n)
        db_session.add(Notification(event_type="TEST", read=False, user_id=1))
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        count = svc.delete_all_read(user_id=1)
        assert count == 1
        result = svc.list_notifications(user_id=1)
        assert result["total"] == 1

    def test_stats(self, db_session):
        db_session.add(Notification(event_type="TRADE_OPENED", user_id=1))
        db_session.add(Notification(event_type="TRADE_CLOSED", user_id=1))
        db_session.add(Notification(event_type="TRADE_OPENED", user_id=1))
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        stats = svc.stats(user_id=1)
        assert stats["total"] == 3
        assert stats["by_type"]["TRADE_OPENED"] == 2

    def test_list_with_filters(self, db_session):
        db_session.add(Notification(event_type="A", user_id=1))
        db_session.add(Notification(event_type="B", user_id=1))
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        result = svc.list_notifications(user_id=1, event_type="A")
        assert result["total"] == 1


class TestDashboardCache:

    def test_cache_set_get(self):
        from api.cache import DashboardCache
        cache = DashboardCache(default_ttl=60)
        cache.set("key1", {"data": 123})
        assert cache.get("key1") == {"data": 123}

    def test_cache_miss(self):
        from api.cache import DashboardCache
        cache = DashboardCache(default_ttl=60)
        assert cache.get("nonexistent") is None

    def test_cache_invalidate(self):
        from api.cache import DashboardCache
        cache = DashboardCache(default_ttl=60)
        cache.set("key1", "val1")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_cache_invalidate_all(self):
        from api.cache import DashboardCache
        cache = DashboardCache(default_ttl=60)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.invalidate_all()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_cache_ttl_expiry(self):
        from api.cache import DashboardCache
        cache = DashboardCache(default_ttl=0)
        cache.set("key1", "val1")
        import time
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_cache_honors_per_call_ttl_not_just_default(self):
        # set()'s ttl= param was previously accepted but silently discarded --
        # every entry cached for default_ttl regardless of what the caller
        # asked for.
        import time

        from api.cache import DashboardCache
        cache = DashboardCache(default_ttl=60)
        cache.set("short-lived", "val1", ttl=0)
        cache.set("long-lived", "val2", ttl=60)
        time.sleep(0.01)
        assert cache.get("short-lived") is None
        assert cache.get("long-lived") == "val2"


class TestKPIServiceEnhanced:

    def test_kpi_service_empty(self, db_session):
        from services.kpi_service import KPIService
        svc = KPIService(session_factory=lambda: db_session)
        kpis = svc.get_kpis()
        assert len(kpis) == 10
        names = [k.name for k in kpis]
        assert "Open PnL" in names
        assert "Open Trades" in names
        assert "Calmar" in names
        assert "Max Drawdown" in names

    def test_kpi_service_with_trades(self, db_session):
        from services.kpi_service import KPIService
        now = datetime.now(UTC)
        db_session.add(Trade(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                             tp1=52000, rr=2.0, status="TP_HIT", pnl=2000.0,
                             created_at=now - timedelta(days=2), closed_at=now - timedelta(days=2)))
        db_session.add(Trade(symbol="ETHUSDT", side="SHORT", entry=3000, stop=3100,
                             tp1=2800, rr=2.0, status="SL_HIT", pnl=-500.0,
                             created_at=now - timedelta(days=1), closed_at=now - timedelta(days=1)))
        db_session.flush()
        svc = KPIService(session_factory=lambda: db_session)
        kpis = svc.get_kpis()
        kpi_map = {k.name: k for k in kpis}
        assert kpi_map["Total PnL"].value == 1500.0
        assert kpi_map["Win Rate"].value == 50.0
