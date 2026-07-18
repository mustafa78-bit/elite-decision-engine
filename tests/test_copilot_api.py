from __future__ import annotations

import pytest
from database import Signal, Trade

def _make_signal(db_session, **overrides):
    kwargs = dict(symbol="BTC", side="LONG", timeframe="1h", status="OPEN", confidence=85.0, score=85.0)
    kwargs.update(overrides)
    s = Signal(**kwargs)
    db_session.add(s)
    db_session.flush()
    return s

def _make_trade(db_session, **overrides):
    kwargs = dict(symbol="BTCUSDT", side="LONG", entry=43000.0, status="OPEN")
    kwargs.update(overrides)
    t = Trade(**kwargs)
    db_session.add(t)
    db_session.flush()
    return t

class TestCopilotAPI:

    def test_copilot_fallback(self, api_client):
        resp = api_client.post(
            "/copilot/chat",
            json={"message": "Hello, how are you?", "symbol": "BTC"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "reply" in body
        assert "suggestions" in body
        assert "links" in body
        assert "metrics" in body
        assert body["metrics"]["status"] == "fallback"

    def test_copilot_why_buy_btc(self, api_client, db_session):
        # Create a signal so it finds one
        _make_signal(db_session, symbol="BTC", score=92.0, confidence=92.0)
        resp = api_client.post(
            "/copilot/chat",
            json={"message": "Why should I buy BTC?", "symbol": "BTC"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "Why Buy BTC" in body["reply"]
        assert body["metrics"]["symbol"] == "BTC"
        assert body["metrics"]["score"] == 92.0

    def test_copilot_what_changed(self, api_client, db_session):
        # Create a recent signal
        _make_signal(db_session, symbol="ETH", score=78.0, confidence=78.0)
        resp = api_client.post(
            "/copilot/chat",
            json={"message": "What changed in the last hour?", "symbol": "BTC"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "Market Changes" in body["reply"]
        assert body["metrics"]["recent_signals_count"] >= 1

    def test_copilot_portfolio_risks(self, api_client, db_session):
        _make_trade(db_session, symbol="BTCUSDT", entry=150000.0)
        resp = api_client.post(
            "/copilot/chat",
            json={"message": "What are the biggest portfolio risks?", "symbol": "BTC"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "Portfolio Risk Assessment" in body["reply"]
        assert body["metrics"]["open_trades"] >= 1

    def test_copilot_what_if_drops(self, api_client, db_session):
        _make_trade(db_session, symbol="BTCUSDT", entry=50000.0)
        resp = api_client.post(
            "/copilot/chat",
            json={"message": "What happens if BTC drops 10%?", "symbol": "BTC"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "Stress Test Simulation" in body["reply"]
        assert body["metrics"]["simulated_loss"] > 0

    def test_copilot_best_opportunities(self, api_client, db_session):
        _make_signal(db_session, symbol="SOL", score=89.0, confidence=89.0)
        resp = api_client.post(
            "/copilot/chat",
            json={"message": "Show me the best opportunities today.", "symbol": "BTC"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "Top Trading Opportunities" in body["reply"]
        assert body["metrics"]["opportunities_count"] >= 1
