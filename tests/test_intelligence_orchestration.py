from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.orchestrator.models import IntelligenceContext, IntelligenceResult, IntelligenceEvent
from core.orchestrator.event_bus import event_bus
from core.orchestrator.registry import intelligence_registry
from core.orchestrator.orchestrator import orchestrator


def test_shared_data_structures():
    """Verify standard schema and properties of Shared Context models."""
    ctx = IntelligenceContext(symbol="BTC", raw_inputs={"value": 100})
    assert ctx.symbol == "BTC"
    assert ctx.raw_inputs["value"] == 100
    assert isinstance(ctx.state, dict)

    res = IntelligenceResult(
        engine_name="Test Engine",
        confidence=0.85,
        reasoning="Test passed",
        evidence={"matched": True}
    )
    assert res.engine_name == "Test Engine"
    assert res.confidence == 0.85
    assert res.evidence["matched"] is True

    ev = IntelligenceEvent(event_type="DecisionStarted", symbol="BTC")
    assert ev.event_type == "DecisionStarted"
    assert ev.symbol == "BTC"


def test_event_bus_subscription_and_publishing():
    """Verify subscription logs, wildcards, and history tracking inside EventBus."""
    event_bus.clear()
    emitted = []

    def callback(event: IntelligenceEvent):
        emitted.append(event)

    event_bus.subscribe("CustomEvent", callback)
    event_bus.subscribe("*", lambda e: emitted.append(e))

    ev = IntelligenceEvent(event_type="CustomEvent", symbol="ETH", payload={"test": 1})
    event_bus.publish(ev)

    assert len(emitted) == 2  # 1 for specific, 1 for wildcard subscriber
    assert emitted[0].symbol == "ETH"
    assert len(event_bus.get_history()) == 1


def test_orchestrated_pipeline_sequencing_flow():
    """Verify sequence pipeline execution logic & correct stage coordination."""
    event_bus.clear()

    # We trigger orchestration for BTC
    profile = orchestrator.orchestrate("BTC", raw_inputs={"technical_strength": 0.90})
    assert profile["symbol"] == "BTC"
    assert "pipeline_stages" in profile
    assert profile["duration_seconds"] > 0

    stages = profile["pipeline_stages"]
    assert "Market Regime" in stages
    assert "Priority Ranking" in stages
    assert "Explainability" in stages
    assert "Executive Recommendation" in stages


def test_endpoints_via_test_client(api_client):
    """Verify end-to-end integration via the REST FastAPI endpoints."""
    # Test Orchestrate execution
    resp = api_client.post("/intelligence/orchestrate?symbol=SOL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "SOL"
    assert "pipeline_stages" in data

    # Test Reports
    resp = api_client.get("/intelligence/reports?symbol=SOL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["engine_name"] == "Market Regime"

    # Test Brief
    resp = api_client.get("/intelligence/brief?symbol=SOL")
    assert resp.status_code == 200
    data = resp.json()
    assert "title" in data
    assert data["highest_confidence_opportunity"] == "SOL"
    assert len(data["reasons"]) == 2

    # Test Timeline
    resp = api_client.get("/intelligence/timeline")
    assert resp.status_code == 200
    timeline = resp.json()
    assert len(timeline) > 0

    # Test Analytics
    resp = api_client.get("/intelligence/analytics?symbol=SOL")
    assert resp.status_code == 200
    analytics = resp.json()
    assert "decision_accuracy_pct" in analytics
