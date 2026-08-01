from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from database import Trade, Watchlist, Notification, UserSettings
from dto.preferences import UserPreferencesDTO, ThemeConfigDTO, LayoutConfigDTO
from dto.watchlists import WatchlistDTO, WatchlistCreateDTO, WatchlistUpdateDTO
from dto.notifications_detail import NotificationDetailDTO, NotificationStatsDTO
from dto.portfolio_detail import PortfolioSummaryDTO, PortfolioDistributionDTO, PortfolioPerformanceDTO, PortfolioRiskDTO


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
        from services.portfolio_service import PortfolioService
        svc = PortfolioService(session_factory=lambda: db_session)
        s = svc.summary()
        assert s["total_trades"] == 0
        assert s["open_trades"] == 0

    def test_portfolio_with_trades(self, db_session):
        from services.portfolio_service import PortfolioService
        now = datetime.now(timezone.utc)
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

    def test_portfolio_distribution(self, db_session):
        from services.portfolio_service import PortfolioService
        now = datetime.now(timezone.utc)
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
        now = datetime.now(timezone.utc)
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

    def test_portfolio_full(self, db_session):
        from services.portfolio_service import PortfolioService
        svc = PortfolioService(session_factory=lambda: db_session)
        f = svc.full_portfolio()
        assert "summary" in f
        assert "distribution" in f
        assert "performance" in f
        assert "risk" in f


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
        created = svc.create_watchlist(name="Test", symbols=["BTCUSDT"])
        assert created["name"] == "Test"
        assert created["symbols"] == ["BTCUSDT"]
        got = svc.get_watchlist(created["id"])
        assert got is not None
        assert got["id"] == created["id"]

    def test_create_watchlist_defaults(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Default")
        assert created["symbols"] == []

    def test_update_watchlist_name(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Old")
        updated = svc.update_watchlist(created["id"], {"name": "New"})
        assert updated["name"] == "New"

    def test_add_symbol(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Test")
        updated = svc.add_symbol(created["id"], "ETHUSDT")
        assert "ETHUSDT" in updated["symbols"]

    def test_remove_symbol(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Test", symbols=["BTCUSDT", "ETHUSDT"])
        updated = svc.remove_symbol(created["id"], "BTCUSDT")
        assert "BTCUSDT" not in updated["symbols"]

    def test_delete_watchlist(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        created = svc.create_watchlist(name="Test")
        assert svc.delete_watchlist(created["id"]) is True
        assert svc.get_watchlist(created["id"]) is None

    def test_delete_nonexistent(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        assert svc.delete_watchlist(999) is False

    def test_add_symbol_nonexistent(self, db_session):
        from services.watchlist_service import WatchlistService
        svc = WatchlistService(session_factory=lambda: db_session)
        assert svc.add_symbol(999, "BTCUSDT") is None


class TestNotificationService:

    def test_list_notifications_empty(self, db_session):
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        result = svc.list_notifications()
        assert result["total"] == 0
        assert result["notifications"] == []

    def test_create_and_list(self, db_session):
        n = Notification(event_type="TRADE_OPENED", payload={"trade_id": 1})
        db_session.add(n)
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        result = svc.list_notifications()
        assert result["total"] == 1
        assert result["notifications"][0]["event_type"] == "TRADE_OPENED"

    def test_mark_read(self, db_session):
        n = Notification(event_type="TEST")
        db_session.add(n)
        db_session.flush()
        nid = n.id
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        assert svc.mark_read(nid) is True
        result = svc.get_notification(nid)
        assert result["read"] is True

    def test_mark_read_nonexistent(self, db_session):
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        assert svc.mark_read(999) is False

    def test_mark_all_read(self, db_session):
        for i in range(3):
            db_session.add(Notification(event_type="TEST"))
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        count = svc.mark_all_read()
        assert count == 3
        stats = svc.stats()
        assert stats["unread"] == 0

    def test_delete_notification(self, db_session):
        n = Notification(event_type="TEST")
        db_session.add(n)
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        assert svc.delete_notification(n.id) is True
        assert svc.get_notification(n.id) is None

    def test_delete_all_read(self, db_session):
        n = Notification(event_type="TEST", read=True)
        db_session.add(n)
        db_session.add(Notification(event_type="TEST", read=False))
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        count = svc.delete_all_read()
        assert count == 1
        result = svc.list_notifications()
        assert result["total"] == 1

    def test_stats(self, db_session):
        db_session.add(Notification(event_type="TRADE_OPENED"))
        db_session.add(Notification(event_type="TRADE_CLOSED"))
        db_session.add(Notification(event_type="TRADE_OPENED"))
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        stats = svc.stats()
        assert stats["total"] == 3
        assert stats["by_type"]["TRADE_OPENED"] == 2

    def test_list_with_filters(self, db_session):
        db_session.add(Notification(event_type="A"))
        db_session.add(Notification(event_type="B"))
        db_session.flush()
        from services.notification_service import NotificationService
        svc = NotificationService(session_factory=lambda: db_session)
        result = svc.list_notifications(event_type="A")
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
        now = datetime.now(timezone.utc)
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
