from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from database import Trade, Notification, Watchlist, UserSettings


class TestWidgetsAPI:

    def test_list_widgets(self, api_client):
        resp = api_client.get("/widgets")
        assert resp.status_code == 200
        data = resp.json()
        assert "kpi" in data
        assert "portfolio" in data
        assert "monitoring" in data
        assert "notifications" in data

    def test_get_kpi_widget(self, api_client):
        resp = api_client.get("/widgets/kpi")
        assert resp.status_code == 200
        data = resp.json()
        assert "kpis" in data

    def test_get_portfolio_widget(self, api_client):
        resp = api_client.get("/widgets/portfolio")
        assert resp.status_code == 200
        assert resp.json()["total_trades"] == 0

    def test_get_monitoring_widget(self, api_client):
        resp = api_client.get("/widgets/monitoring")
        assert resp.status_code == 200
        assert "status" in resp.json()

    def test_get_notifications_widget(self, api_client):
        resp = api_client.get("/widgets/notifications")
        assert resp.status_code == 200
        assert resp.json()["unread_count"] == 0

    def test_get_unknown_widget_returns_404(self, api_client):
        resp = api_client.get("/widgets/nonexistent")
        assert resp.status_code == 404

    def test_kpi_widget_detail(self, api_client):
        resp = api_client.get("/widgets/kpi/detail")
        assert resp.status_code == 200
        assert "kpis" in resp.json()

    def test_portfolio_widget_summary(self, api_client):
        resp = api_client.get("/widgets/portfolio/summary")
        assert resp.status_code == 200

    def test_monitoring_widget_status(self, api_client):
        resp = api_client.get("/widgets/monitoring/status")
        assert resp.status_code == 200

    def test_notifications_widget_recent(self, api_client):
        resp = api_client.get("/widgets/notifications/recent")
        assert resp.status_code == 200


class TestPreferencesAPI:

    def test_get_default_preferences(self, api_client):
        resp = api_client.get("/preferences/defaults")
        assert resp.status_code == 200
        data = resp.json()
        assert data["theme"] == "dark"

    def test_get_theme_config(self, api_client):
        resp = api_client.get("/preferences/theme-config?theme=light")
        assert resp.status_code == 200
        assert resp.json()["theme"] == "light"

    def test_get_preferences_nonexistent_user(self, api_client):
        resp = api_client.get("/preferences?user_id=999")
        assert resp.status_code == 200

    def test_upsert_preferences(self, api_client):
        resp = api_client.put("/preferences?user_id=1", json={"theme": "light"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["theme"] == "light"

    def test_update_theme(self, api_client):
        resp = api_client.put("/preferences/theme?user_id=1&theme=dark")
        assert resp.status_code == 200
        assert resp.json()["theme"] == "dark"

    def test_update_layout(self, api_client):
        resp = api_client.put("/preferences/layout?user_id=1", json={"sidebar_collapsed": True})
        assert resp.status_code == 200
        assert resp.json()["layout_config"]["sidebar_collapsed"] is True


class TestWatchlistsAPI:

    def test_list_watchlists_empty(self, api_client):
        resp = api_client.get("/watchlists")
        assert resp.status_code == 200
        assert resp.json()["watchlists"] == []

    def test_create_watchlist(self, api_client):
        resp = api_client.post("/watchlists?name=Test&symbols=BTCUSDT,ETHUSDT")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test"
        assert "BTCUSDT" in data["symbols"]
        return data["id"]

    def test_create_watchlist_defaults(self, api_client):
        resp = api_client.post("/watchlists?name=Default")
        assert resp.status_code == 200
        assert resp.json()["symbols"] == []

    def test_get_watchlist(self, api_client):
        resp = api_client.post("/watchlists?name=GetTest")
        wid = resp.json()["id"]
        resp2 = api_client.get(f"/watchlists/{wid}")
        assert resp2.status_code == 200
        assert resp2.json()["name"] == "GetTest"

    def test_get_nonexistent_watchlist(self, api_client):
        resp = api_client.get("/watchlists/999")
        assert resp.status_code == 404

    def test_update_watchlist(self, api_client):
        resp = api_client.post("/watchlists?name=UpdateTest")
        wid = resp.json()["id"]
        resp2 = api_client.put(f"/watchlists/{wid}", json={"name": "Updated"})
        assert resp2.status_code == 200
        assert resp2.json()["name"] == "Updated"

    def test_add_symbol(self, api_client):
        resp = api_client.post("/watchlists?name=AddSym")
        wid = resp.json()["id"]
        resp2 = api_client.post(f"/watchlists/{wid}/symbols?symbol=SOLUSDT")
        assert resp2.status_code == 200
        assert "SOLUSDT" in resp2.json()["symbols"]

    def test_remove_symbol(self, api_client):
        resp = api_client.post("/watchlists?name=RemSym&symbols=BTCUSDT,ETHUSDT")
        wid = resp.json()["id"]
        resp2 = api_client.delete(f"/watchlists/{wid}/symbols/BTCUSDT")
        assert resp2.status_code == 200
        assert "BTCUSDT" not in resp2.json()["symbols"]

    def test_delete_watchlist(self, api_client):
        resp = api_client.post("/watchlists?name=DelTest")
        wid = resp.json()["id"]
        resp2 = api_client.delete(f"/watchlists/{wid}")
        assert resp2.status_code == 200
        resp3 = api_client.get(f"/watchlists/{wid}")
        assert resp3.status_code == 404


class TestNotificationsAPI:

    def test_list_notifications_empty(self, api_client):
        resp = api_client.get("/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_notification_stats_empty(self, api_client):
        resp = api_client.get("/notifications/stats")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_get_nonexistent_notification(self, api_client):
        resp = api_client.get("/notifications/999")
        assert resp.status_code == 404

    def test_mark_read_nonexistent(self, api_client):
        resp = api_client.put("/notifications/999/read")
        assert resp.status_code == 404

    def test_mark_all_read_empty(self, api_client):
        resp = api_client.put("/notifications/read-all")
        assert resp.status_code == 200

    def test_delete_nonexistent(self, api_client):
        resp = api_client.delete("/notifications/999")
        assert resp.status_code == 404


class TestTimelineAPI:

    def test_signal_timeline_nonexistent(self, api_client):
        resp = api_client.get("/timeline/signal/999")
        assert resp.status_code == 404

    def test_trade_timeline_nonexistent(self, api_client):
        resp = api_client.get("/timeline/trade/999")
        assert resp.status_code == 404

    def test_global_timeline_empty(self, api_client):
        resp = api_client.get("/timeline")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestPortfolioDetailAPI:

    def test_portfolio_summary_empty(self, api_client):
        resp = api_client.get("/portfolio/summary")
        assert resp.status_code == 200
        assert resp.json()["total_trades"] == 0

    def test_portfolio_distribution_empty(self, api_client):
        resp = api_client.get("/portfolio/distribution")
        assert resp.status_code == 200

    def test_portfolio_performance_empty(self, api_client):
        resp = api_client.get("/portfolio/performance")
        assert resp.status_code == 200

    def test_portfolio_risk_empty(self, api_client):
        resp = api_client.get("/portfolio/risk")
        assert resp.status_code == 200

    def test_portfolio_full(self, api_client):
        resp = api_client.get("/portfolio/full")
        assert resp.status_code == 200
        assert "summary" in resp.json()
