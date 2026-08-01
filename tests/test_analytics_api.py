from __future__ import annotations

import pytest
from database import Trade, Signal


class TestAnalyticsAPI:

    def test_analytics_empty(self, api_client):
        resp = api_client.get("/analytics")
        assert resp.status_code == 200
        body = resp.json()
        assert body["daily"] == []
        assert body["weekly"] == []
        assert body["monthly"] == []

    def test_analytics_with_data(self, api_client, db_session):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for pnl in [1000, 2000, -500]:
            db_session.add(Trade(
                symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                tp1=52000, rr=2.0,
                status="TP_HIT" if pnl > 0 else "SL_HIT",
                pnl=pnl, created_at=now,
            ))
        db_session.flush()

        resp = api_client.get("/analytics")
        assert resp.status_code == 200
        body = resp.json()
        assert body["win_loss"]["total_wins"] == 2
        assert body["win_loss"]["total_losses"] == 1

    def test_analytics_daily(self, api_client, db_session):
        from datetime import datetime, timezone
        db_session.add(Trade(
            symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
            tp1=52000, rr=2.0, status="TP_HIT", pnl=1000,
            created_at=datetime.now(timezone.utc),
        ))
        db_session.flush()
        resp = api_client.get("/analytics/daily?days=7")
        assert resp.status_code == 200
        body = resp.json()
        assert "daily" in body

    def test_analytics_weekly(self, api_client, db_session):
        resp = api_client.get("/analytics/weekly?weeks=4")
        assert resp.status_code == 200
        assert "weekly" in resp.json()

    def test_analytics_monthly(self, api_client, db_session):
        resp = api_client.get("/analytics/monthly?months=6")
        assert resp.status_code == 200
        assert "monthly" in resp.json()

    def test_analytics_win_loss(self, api_client, db_session):
        resp = api_client.get("/analytics/win-loss")
        assert resp.status_code == 200

    def test_analytics_symbols(self, api_client, db_session):
        from datetime import datetime, timezone
        db_session.add(Trade(
            symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
            tp1=52000, rr=2.0, status="TP_HIT", pnl=1000,
            created_at=datetime.now(timezone.utc),
        ))
        db_session.flush()
        resp = api_client.get("/analytics/symbols")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["symbols"]) == 1

    def test_analytics_risk(self, api_client, db_session):
        db_session.add(Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="REJECTED"))
        db_session.flush()
        resp = api_client.get("/analytics/risk")
        assert resp.status_code == 200

    def test_analytics_drawdown(self, api_client, db_session):
        resp = api_client.get("/analytics/drawdown")
        assert resp.status_code == 200

    def test_analytics_heatmap(self, api_client, db_session):
        resp = api_client.get("/analytics/heatmap")
        assert resp.status_code == 200
        assert "heatmap" in resp.json()

    def test_analytics_trends(self, api_client, db_session):
        resp = api_client.get("/analytics/trends")
        assert resp.status_code == 200
        assert "trends" in resp.json()
