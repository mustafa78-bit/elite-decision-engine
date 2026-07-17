import pytest

from services.notification_service import NotificationService


class TestNotificationService:

    def _make_service(self):
        return NotificationService(max_history=100)

    def test_notify(self):
        svc = self._make_service()
        n = svc.notify(type="info", title="Test", message="Hello", severity="low")
        assert n.id != ""
        assert n.title == "Test"
        assert n.message == "Hello"
        assert n.read is False
        assert n.category == "general"
        assert n.priority == 0

    def test_notify_with_category(self):
        svc = self._make_service()
        n = svc.notify(type="signal", category="signal", title="Signal Alert", message="BTC long", severity="high", priority=4)
        assert n.category == "signal"
        assert n.priority == 4
        assert n.severity == "high"

    def test_notify_invalid_category_falls_back(self):
        svc = self._make_service()
        n = svc.notify(category="invalid_category")
        assert n.category == "general"

    def test_notify_clamps_priority(self):
        svc = self._make_service()
        n = svc.notify(priority=100)
        assert n.priority == 5
        n2 = svc.notify(priority=-10)
        assert n2.priority == 0

    def test_get_history_empty(self):
        svc = self._make_service()
        history = svc.get_history()
        assert history == []

    def test_get_history(self):
        svc = self._make_service()
        svc.notify(title="A")
        svc.notify(title="B")
        history = svc.get_history()
        assert len(history) == 2

    def test_get_history_limit(self):
        svc = self._make_service()
        for i in range(10):
            svc.notify(title=f"Notification {i}")
        history = svc.get_history(limit=3)
        assert len(history) == 3

    def test_get_history_filter_category(self):
        svc = self._make_service()
        svc.notify(title="Trade Alert", category="trade")
        svc.notify(title="System Alert", category="system")
        trade_history = svc.get_history(category="trade")
        assert len(trade_history) == 1
        assert trade_history[0].title == "Trade Alert"

    def test_get_history_filter_unread(self):
        svc = self._make_service()
        svc.notify(title="A")
        svc.notify(title="B")
        svc.mark_read(svc._history[0].id)
        unread = svc.get_history(unread_only=True)
        assert len(unread) == 1

    def test_get_history_filter_min_priority(self):
        svc = self._make_service()
        svc.notify(title="Low", priority=0)
        svc.notify(title="High", priority=5)
        high_only = svc.get_history(min_priority=5)
        assert len(high_only) == 1
        assert high_only[0].title == "High"

    def test_mark_read(self):
        svc = self._make_service()
        n = svc.notify(title="Test")
        assert n.read is False
        result = svc.mark_read(n.id)
        assert result is True
        assert n.read is True

    def test_mark_read_not_found(self):
        svc = self._make_service()
        result = svc.mark_read("nonexistent")
        assert result is False

    def test_mark_read_already_read(self):
        svc = self._make_service()
        n = svc.notify(title="Test")
        svc.mark_read(n.id)
        result = svc.mark_read(n.id)
        assert result is False

    def test_mark_all_read(self):
        svc = self._make_service()
        svc.notify(title="A")
        svc.notify(title="B")
        svc.notify(title="C")
        count = svc.mark_all_read()
        assert count == 3
        assert svc.get_unread_count() == 0

    def test_alert_summary(self):
        svc = self._make_service()
        svc.notify(title="Info 1", severity="info")
        svc.notify(title="Warning 1", severity="warning")
        svc.notify(title="Critical 1", severity="critical")
        summary = svc.get_alert_summary()
        assert summary.total == 3
        assert summary.unread == 3
        assert summary.critical == 1
        assert summary.warning == 1
        assert summary.info == 1

    def test_alert_summary_cache(self):
        svc = self._make_service()
        svc.notify(title="Test")
        svc.get_alert_summary()
        cached = svc.get_alert_summary()
        assert svc.get_diagnostics()["cache_hits"] >= 1

    def test_alert_summary_by_category(self):
        svc = self._make_service()
        svc.notify(title="Trade", category="trade")
        svc.notify(title="System", category="system")
        summary = svc.get_alert_summary()
        assert summary.by_category.get("trade") == 1
        assert summary.by_category.get("system") == 1

    def test_get_categories(self):
        svc = self._make_service()
        cats = svc.get_categories()
        assert "general" in cats
        assert "trade" in cats
        assert "system" in cats

    def test_get_priority_levels(self):
        svc = self._make_service()
        levels = svc.get_priority_levels()
        assert levels == [0, 1, 2, 3, 4, 5]

    def test_get_unread_count(self):
        svc = self._make_service()
        assert svc.get_unread_count() == 0
        svc.notify(title="Test")
        assert svc.get_unread_count() == 1
        svc.mark_all_read()
        assert svc.get_unread_count() == 0

    def test_max_history(self):
        svc = NotificationService(max_history=5)
        for i in range(10):
            svc.notify(title=f"N{i}")
        assert len(svc._history) == 5

    def test_callback(self):
        svc = self._make_service()
        callback_called = []
        def cb(n):
            callback_called.append(n)
        svc.set_callback(cb)
        n = svc.notify(title="Test")
        assert len(callback_called) == 1
        assert callback_called[0].title == "Test"

    def test_get_diagnostics(self):
        svc = self._make_service()
        diag = svc.get_diagnostics()
        assert "total_created" in diag
        assert "total_read" in diag
        assert "history_size" in diag

    def test_invalidate_cache(self):
        svc = self._make_service()
        svc.notify(title="Test")
        svc.get_alert_summary()
        svc.invalidate_cache()
        hits_before = svc.get_diagnostics()["cache_hits"]
        svc.get_alert_summary()
        assert svc.get_diagnostics()["cache_hits"] == hits_before
