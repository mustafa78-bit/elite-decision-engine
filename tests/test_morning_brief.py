import pytest
from fastapi.testclient import TestClient
from database import Signal, Trade, Notification, OPEN
from services.portfolio_service import PortfolioService
from api.routes.ollo import calculate_founder_priority_score, format_prioritized_signal
from api.main import app

def test_portfolio_health_score_empty_db():
    """Verify that when no trades are present, the portfolio health score defaults to 100."""
    class MockSession:
        def query(self, model):
            return self
        def all(self):
            return []
        def close(self):
            pass

    service = PortfolioService(session_factory=lambda: MockSession())
    details = service.get_portfolio_health_details()

    assert details["score"] == 100
    assert details["status"] == "Excellent"
    assert "contributors" in details
    assert len(details["contributors"]) == 3
    assert "recommended_action" in details


def test_calculate_founder_priority_score_and_format():
    """Verify that the priority scoring is bounded, stable, and formats qualitative details correctly."""
    signal = Signal(
        symbol="BTCUSDT",
        side="LONG",
        confidence=90.0,
        risk_score=20.0,
        market_health=80.0,
        btc_health=85.0,
        timeframe="1h"
    )

    score = calculate_founder_priority_score(signal)
    assert 0.0 <= score <= 100.0

    formatted = format_prioritized_signal(signal, score)
    assert formatted["symbol"] == "BTCUSDT"
    assert formatted["side"] == "LONG"
    assert formatted["confidence"] == "High"
    assert formatted["risk"] == "Conservative"
    assert "why_ranked_top" in formatted
    assert "supporting_evidence" in formatted
    assert len(formatted["supporting_evidence"]) >= 2
    assert formatted["expected_holding_horizon"] == "1-4 hours"


def test_morning_brief_endpoint_schema(db_session, api_client):
    """Test that the /ollo/morning-brief endpoint returns the expected 30-Second Morning JSON payload."""

    # Pre-populate database using db_session fixture (which uses a safe in-memory/test db)
    db_session.query(Signal).delete()
    db_session.query(Trade).delete()
    db_session.query(Notification).delete()

    signal = Signal(
        symbol="ETHUSDT",
        side="LONG",
        price=3000.0,
        confidence=88.0,
        risk_score=25.0,
        market_health=80.0,
        status="OPEN"
    )
    db_session.add(signal)

    trade = Trade(
        symbol="BTCUSDT",
        side="LONG",
        entry=60000.0,
        status="OPEN",
        pnl=-50.0
    )
    db_session.add(trade)

    notification = Notification(
        event_type="TP_HIT",
        payload={"symbol": "SOLUSDT", "side": "LONG", "exit_price": 150.0, "pnl": 200.0}
    )
    db_session.add(notification)

    db_session.commit()

    # Call endpoint using api_client (which is already configured with auth, conftest-patched, etc.)
    response = api_client.get("/ollo/morning-brief")

    assert response.status_code == 200
    data = response.json()

    assert "market_regime_banner" in data
    assert "overnight_summary" in data
    assert "attention_required" in data
    assert "portfolio_risk" in data
    assert "best_opportunities" in data
    assert "whats_changed" in data
    assert "ai_council_summary" in data
    assert "important_action" in data

    banner = data["market_regime_banner"]
    assert "regime" in banner
    assert "trend" in banner

    portfolio = data["portfolio_risk"]
    assert "score" in portfolio
    assert "status" in portfolio
    assert "contributors" in portfolio
    assert "recommended_action" in portfolio

    opps = data["best_opportunities"]
    assert len(opps) > 0
    assert opps[0]["symbol"] == "ETHUSDT"
    assert "why_ranked_top" in opps[0]

    action = data["important_action"]
    assert "action" in action
    assert "priority" in action
    assert "rationale" in action
