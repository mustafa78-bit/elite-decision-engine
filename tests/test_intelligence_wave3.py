from __future__ import annotations

import pytest
from auth.jwt import create_access_token


def _make_user(db_session, **overrides):
    from auth.service import hash_password
    from database import User
    kwargs = dict(username="testinteluser", email="intel@example.com", hashed_password=hash_password("pass123"))
    kwargs.update(overrides)
    u = User(**kwargs)
    db_session.add(u)
    db_session.flush()
    return u


def _token_for_user(user) -> str:
    return create_access_token({"sub": str(user.id), "username": user.username})


def test_api_intelligence_orchestrate(api_client, db_session):
    user = _make_user(db_session)
    headers = {"Authorization": f"Bearer {_token_for_user(user)}"}

    # Trigger orchestration
    resp = api_client.get("/intelligence/orchestrate?symbol=BTC&price=55000.0", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Assert type-safe attributes are computed correctly
    assert data["symbol"] == "BTC"
    assert data["market_price"] == 55000.0
    assert data["service_states"]["decision_memory"] == "SUCCESS"
    assert data["service_states"]["pattern_discovery"] == "SUCCESS"
    assert data["service_states"]["risk_engine"] == "SUCCESS"

    # Assert timings and global aggregates are recorded
    assert "total_coordination" in data["timings"]
    assert "overall_threat_score" in data["metrics"]
    assert "aggregated_confidence" in data["metrics"]


def test_api_intelligence_dashboard(api_client, db_session):
    user = _make_user(db_session)
    headers = {"Authorization": f"Bearer {_token_for_user(user)}"}

    resp = api_client.get("/intelligence/dashboard?symbol=BTC", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Check sections
    assert "executive_summary" in data
    assert "top_opportunities" in data
    assert "portfolio_intelligence" in data
    assert "active_risks" in data
    assert "market_regime" in data
    assert "confidence_distribution" in data
    assert "decision_memory_insights" in data
    assert "pattern_discovery_highlights" in data
    assert "system_health" in data

    # Verify content values
    assert data["executive_summary"]["action_recommendation"] is not None
    assert len(data["top_opportunities"]) == 1
    assert data["top_opportunities"][0]["symbol"] == "BTC"
    assert data["active_risks"]["allowed"] is True
    assert data["pattern_discovery_highlights"]["is_exceptional"] is True


def test_api_intelligence_timeline(api_client, db_session):
    user = _make_user(db_session)
    headers = {"Authorization": f"Bearer {_token_for_user(user)}"}

    # Trigger a clean run first to generate fresh events
    api_client.get("/intelligence/orchestrate?symbol=ETH&price=1800.0", headers=headers)

    # Call timeline API
    resp = api_client.get("/intelligence/timeline?limit=10", headers=headers)
    assert resp.status_code == 200
    events = resp.json()

    # Confirm events were recorded chronological and typed
    assert len(events) > 0
    first_event = events[0]
    assert "timestamp" in first_event
    assert "correlation_id" in first_event
    assert "event_type" in first_event
    assert "summary" in first_event
    assert "symbol" in first_event


def test_api_intelligence_briefing(api_client, db_session):
    user = _make_user(db_session)
    headers = {"Authorization": f"Bearer {_token_for_user(user)}"}

    resp = api_client.get("/intelligence/briefing?symbol=ETH", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Verify briefing details
    assert "briefing_id" in data
    assert "timestamp" in data
    assert "summary" in data
    assert "details" in data
    assert len(data["details"]["catalysts"]) > 0
    assert len(data["details"]["recommendations"]) > 0

    # Verify structured explainability block
    assert "explainability" in data
    assert "why" in data["explainability"]
    assert "why_now" in data["explainability"]
    assert "why_not" in data["explainability"]
    assert data["explainability"]["calibration_factor"] == 0.95
    assert len(data["explainability"]["supporting_evidence"]) > 0


def test_api_intelligence_analytics(api_client, db_session):
    user = _make_user(db_session)
    headers = {"Authorization": f"Bearer {_token_for_user(user)}"}

    resp = api_client.get("/intelligence/analytics", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Verify diagnostics and status reporting are fully present
    assert "diagnostics" in data
    assert "services_status" in data
    assert data["diagnostics"]["decision_accuracy_pct"] == 84.5
    assert data["diagnostics"]["average_expected_calibration_error"] == 0.04
    assert "risk_engine" in data["services_status"]
    assert data["services_status"]["risk_engine"]["enabled"] is True
