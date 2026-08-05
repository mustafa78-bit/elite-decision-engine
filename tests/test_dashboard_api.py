from __future__ import annotations

import pytest
from database import Trade, Signal, Notification
from datetime import datetime, timezone


class TestDashboardAPI:

    def test_dashboard_overview(self, api_client):
        resp = api_client.get("/dashboard/overview")
        assert resp.status_code == 200
        body = resp.json()
        assert "widgets" in body
        assert len(body["widgets"]) > 0

    def test_dashboard_kpi(self, api_client):
        resp = api_client.get("/dashboard/kpi")
        assert resp.status_code == 200
        body = resp.json()
        assert "kpis" in body

    def test_dashboard_portfolio_empty(self, api_client):
        resp = api_client.get("/dashboard/portfolio")
        assert resp.status_code == 200
        body = resp.json()
        assert "total_pnl" in body
        assert body["total_trades"] == 0

    def test_dashboard_portfolio_with_trades(self, api_client, db_session):
        now = datetime.now(timezone.utc)
        for pnl in [1000, 2000, -500]:
            db_session.add(Trade(
                symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                tp1=52000, rr=2.0,
                status="TP_HIT" if pnl > 0 else "SL_HIT",
                pnl=pnl, created_at=now,
            ))
        db_session.add(Trade(
            symbol="BTCUSDT", side="LONG", entry=51000, stop=50000,
            tp1=53000, rr=2.0, status="OPEN", pnl=0, created_at=now,
        ))
        db_session.flush()
        resp = api_client.get("/dashboard/portfolio")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_trades"] == 3
        assert body["open_trades"] == 1
        assert body["total_pnl"] == 2500.0

    def test_dashboard_monitoring(self, api_client):
        resp = api_client.get("/dashboard/monitoring")
        assert resp.status_code == 200
        body = resp.json()
        assert "status" in body
        assert "uptime_seconds" in body

    def test_dashboard_notifications(self, api_client):
        resp = api_client.get("/dashboard/notifications")
        assert resp.status_code == 200
        body = resp.json()
        assert "unread" in body
        assert "notifications" in body
        assert "total" in body

    def test_dashboard_notifications_with_data(self, api_client, db_session):
        for i in range(3):
            db_session.add(Notification(event_type="test_event", payload={"i": i}, read=False))
        db_session.flush()
        resp = api_client.get("/dashboard/notifications")
        assert resp.status_code == 200
        body = resp.json()
        assert body["unread"] == 3
        assert len(body["notifications"]) == 3
        assert body["total"] == 3

    def test_dashboard_explanation_nonexistent(self, api_client):
        resp = api_client.get("/dashboard/explanation/99999")
        assert resp.status_code == 404

    def test_dashboard_explanation(self, api_client, db_session):
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN", confidence=85.0, score=0.85)
        db_session.add(signal)
        db_session.flush()
        resp = api_client.get(f"/dashboard/explanation/{signal.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert "signal_id" in body
        assert "decision" in body
        assert "breakdown" in body

    def test_dashboard_timeline_nonexistent(self, api_client):
        resp = api_client.get("/dashboard/timeline/99999")
        assert resp.status_code == 404

    def test_dashboard_timeline(self, api_client, db_session):
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN", confidence=85.0, score=0.85)
        db_session.add(signal)
        db_session.flush()
        resp = api_client.get(f"/dashboard/timeline/{signal.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert "events" in body
        assert "total_duration_ms" in body

    def test_kpi_endpoint(self, api_client):
        resp = api_client.get("/kpi")
        assert resp.status_code == 200
        body = resp.json()
        assert "kpis" in body
        assert len(body["kpis"]) == 10

    def test_dashboard_hero_scores_flow(self, api_client, db_session):
        # 1. Test generate_signals copies scores from Opportunity to Signal
        from services.signal_generator import generate_signals
        from scanner.models import Opportunity

        opp = Opportunity(
            symbol="BTCUSDT",
            side="LONG",
            strategy="trend",
            score=0.8,
            confidence=85.0,
            price=60000.0,
            trend_score=0.75,
            funding_score=0.6,
            oi_score=0.5,
            cvd_score=0.8,
            risk_score=0.4,
        )

        num_created = generate_signals([opp], timeframe="1h", session=db_session)
        assert num_created == 1

        created_signal = db_session.query(Signal).filter(Signal.symbol == "BTCUSDT", Signal.status == "OPEN").first()
        assert created_signal is not None
        assert created_signal.trend_score == 0.75
        assert created_signal.funding_score == 0.6
        assert created_signal.oi_score == 0.5
        assert created_signal.cvd_score == 0.8
        assert created_signal.risk_score == 0.4

        # 2. Query GET /dashboard/hero and verify they propagate and compute correct decision/confidence
        resp = api_client.get("/dashboard/hero")
        assert resp.status_code == 200
        body = resp.json()

        assert body["symbol"] == "BTCUSDT"
        assert body["risk"] == 0.4
        # Since scores are >= 0.5, they all contribute to the ExplainEngine average computation and decision
        assert body["decision"] in ("BUY", "STRONG_BUY", "SELL", "STRONG_SELL", "HOLD")
        assert body["confidence"] > 0.0
