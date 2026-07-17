import pytest
from services.user_service import UserService, UserPreferencesDTO, LayoutConfigDTO, PresetDTO


class TestUserPreferences:

    def test_get_preferences_creates_default(self):
        svc = UserService()
        prefs = svc.get_preferences("user1")
        assert prefs.theme == "dark"
        assert prefs.language == "en"
        assert prefs.notifications_enabled is True
        assert prefs.favorite_symbols == []
        assert prefs.watchlist == []

    def test_get_preferences_returns_same_instance(self):
        svc = UserService()
        p1 = svc.get_preferences("user1")
        p2 = svc.get_preferences("user1")
        assert p1 is p2

    def test_update_preferences(self):
        svc = UserService()
        svc.update_preferences("user1", {"theme": "light", "language": "fr"})
        prefs = svc.get_preferences("user1")
        assert prefs.theme == "light"
        assert prefs.language == "fr"

    def test_update_preferences_favorites(self):
        svc = UserService()
        svc.update_preferences("user1", {"favorite_symbols": ["BTC", "ETH"]})
        prefs = svc.get_preferences("user1")
        assert prefs.favorite_symbols == ["BTC", "ETH"]

    def test_update_preferences_watchlist(self):
        svc = UserService()
        svc.update_preferences("user1", {"watchlist": ["BTC", "SOL"]})
        prefs = svc.get_preferences("user1")
        assert prefs.watchlist == ["BTC", "SOL"]


class TestTheme:

    def test_set_theme_dark(self):
        svc = UserService()
        assert svc.set_theme("user1", "dark") is True
        assert svc.get_preferences("user1").theme == "dark"

    def test_set_theme_light(self):
        svc = UserService()
        assert svc.set_theme("user1", "light") is True
        assert svc.get_preferences("user1").theme == "light"

    def test_set_theme_system(self):
        svc = UserService()
        assert svc.set_theme("user1", "system") is True

    def test_set_theme_invalid(self):
        svc = UserService()
        assert svc.set_theme("user1", "neon") is False
        assert svc.get_preferences("user1").theme == "dark"


class TestLanguage:

    def test_set_language(self):
        svc = UserService()
        svc.set_language("user1", "de")
        assert svc.get_preferences("user1").language == "de"

    def test_set_language_truncated(self):
        svc = UserService()
        svc.set_language("user1", "verylongcode")
        assert len(svc.get_preferences("user1").language) <= 10


class TestNotificationPreferences:

    def test_toggle_enabled(self):
        svc = UserService()
        svc.set_notification_preferences("user1", enabled=False)
        assert svc.get_preferences("user1").notifications_enabled is False

    def test_update_types(self):
        svc = UserService()
        svc.set_notification_preferences("user1", enabled=True, types={"trade": False})
        assert svc.get_preferences("user1").notification_types["trade"] is False
        assert svc.get_preferences("user1").notification_types["signal"] is True


class TestLayouts:

    def test_save_layout(self):
        svc = UserService()
        layout = svc.save_layout("user1", "My Layout", [{"id": "widget1"}])
        assert layout.name == "My Layout"
        assert layout.id != ""
        assert layout.is_default is True

    def test_get_layouts(self):
        svc = UserService()
        svc.save_layout("user1", "Layout A", [])
        svc.save_layout("user1", "Layout B", [])
        layouts = svc.get_layouts("user1")
        assert len(layouts) == 2

    def test_delete_layout(self):
        svc = UserService()
        l1 = svc.save_layout("user1", "A", [])
        svc.save_layout("user1", "B", [])
        assert svc.delete_layout("user1", l1.id) is True
        assert svc.delete_layout("user1", "nonexistent") is False

    def test_layouts_isolated_per_user(self):
        svc = UserService()
        svc.save_layout("user1", "A", [])
        svc.save_layout("user2", "B", [])
        assert len(svc.get_layouts("user1")) == 1
        assert len(svc.get_layouts("user2")) == 1


class TestPresets:

    def test_get_presets(self):
        svc = UserService()
        presets = svc.get_presets()
        assert len(presets) >= 4
        names = [p["name"] for p in presets]
        assert "Default" in names
        assert "Trader" in names
        assert "Analyst" in names
        assert "Minimal" in names

    def test_set_active_preset(self):
        svc = UserService()
        assert svc.set_active_preset("user1", "trader") is True
        assert svc.get_preferences("user1").dashboard_preset == "trader"

    def test_set_active_preset_invalid(self):
        svc = UserService()
        assert svc.set_active_preset("user1", "nonexistent") is False
        assert svc.get_preferences("user1").dashboard_preset == "default"


class TestFavorites:

    def test_add_favorite(self):
        svc = UserService()
        symbols = svc.add_favorite("user1", "btc")
        assert "BTC" in symbols

    def test_add_favorite_uppercases(self):
        svc = UserService()
        symbols = svc.add_favorite("user1", "eth")
        assert "ETH" in symbols

    def test_add_favorite_duplicate(self):
        svc = UserService()
        svc.add_favorite("user1", "BTC")
        symbols = svc.add_favorite("user1", "BTC")
        assert len(symbols) == 1

    def test_remove_favorite(self):
        svc = UserService()
        svc.add_favorite("user1", "BTC")
        symbols = svc.remove_favorite("user1", "BTC")
        assert "BTC" not in symbols

    def test_get_favorites(self):
        svc = UserService()
        svc.add_favorite("user1", "BTC")
        svc.add_favorite("user1", "ETH")
        syms = svc.get_favorites("user1")
        assert len(syms) == 2

    def test_get_favorites_empty(self):
        svc = UserService()
        assert svc.get_favorites("user1") == []


class TestWatchlist:

    def test_add_to_watchlist(self):
        svc = UserService()
        symbols = svc.add_to_watchlist("user1", "SOL")
        assert "SOL" in symbols

    def test_remove_from_watchlist(self):
        svc = UserService()
        svc.add_to_watchlist("user1", "SOL")
        symbols = svc.remove_from_watchlist("user1", "SOL")
        assert "SOL" not in symbols

    def test_get_watchlist(self):
        svc = UserService()
        svc.add_to_watchlist("user1", "SOL")
        svc.add_to_watchlist("user1", "AVAX")
        assert len(svc.get_watchlist("user1")) == 2


class TestRecentActivity:

    def test_record_activity(self):
        svc = UserService()
        act = svc.record_activity("user1", "login", "User logged in")
        assert act.action == "login"
        assert act.description == "User logged in"
        assert act.id != ""

    def test_get_recent_activity(self):
        svc = UserService()
        svc.record_activity("user1", "login", "Logged in")
        svc.record_activity("user1", "trade", "Executed trade")
        activities = svc.get_recent_activity()
        assert len(activities) == 2

    def test_get_recent_activity_limit(self):
        svc = UserService()
        for i in range(10):
            svc.record_activity("user1", "action", f"Action {i}")
        activities = svc.get_recent_activity(limit=3)
        assert len(activities) == 3

    def test_max_recent_activity(self):
        svc = UserService()
        for i in range(150):
            svc.record_activity("user1", "action", f"Action {i}")
        assert len(svc._recent_activity) == 100

    def test_activity_metadata(self):
        svc = UserService()
        act = svc.record_activity("user1", "trade", "Bought BTC", {"price": 50000})
        assert act.metadata["price"] == 50000

    def test_get_recent_activity_empty(self):
        svc = UserService()
        assert svc.get_recent_activity() == []


class TestSession:

    def test_create_session(self):
        svc = UserService()
        session = svc.create_session("user1", "10.0.0.1", "test-agent")
        assert session.session_id != ""
        assert session.ip_address == "10.0.0.1"
        assert session.user_agent == "test-agent"

    def test_get_session(self):
        svc = UserService()
        svc.create_session("user1")
        session = svc.get_session("user1")
        assert session is not None
        assert svc.get_session("nonexistent") is None

    def test_update_session_activity(self):
        svc = UserService()
        svc.create_session("user1")
        svc.update_session_activity("user1")
        session = svc.get_session("user1")
        assert session.request_count == 1

    def test_update_session_activity_nonexistent(self):
        svc = UserService()
        svc.update_session_activity("nobody")


class TestDiagnostics:

    def test_get_diagnostics(self):
        svc = UserService()
        svc.get_preferences("user1")
        svc.save_layout("user1", "L", [])
        svc.record_activity("user1", "test", "testing")
        diag = svc.get_diagnostics()
        assert "total_users" in diag
        assert "preferences_count" in diag
        assert "layouts_count" in diag
        assert "recent_activity_count" in diag
