import pytest
from core.autonomous_models import (
    IntelligenceContext,
    IntelligenceResult,
    PipelineStarted,
    ServiceStarted,
    ServiceCompleted,
    ServiceFailed,
    PipelineCompleted
)
from core.intelligence_registry import IntelligenceRegistry
from core.autonomous_event_bus import AutonomousEventBus
from core.autonomous_orchestrator import GlobalIntelligenceOrchestrator


# ─── Epic 21.2 — Context Immutability Tests ─────────────────────────────────

def test_context_is_immutable():
    ctx = IntelligenceContext(symbol="BTC", side="LONG")
    # Mutating an attribute on a frozen dataclass must raise dataclasses.FrozenInstanceError
    import dataclasses
    with pytest.raises(Exception):
        ctx.symbol = "ETH"


# ─── Epic 21.4 — Intelligence Registry Tests ────────────────────────────────

def test_registry_registration():
    reg = IntelligenceRegistry()
    reg.clear()

    dummy_service = lambda ctx: {"confidence": 95.0, "reasoning": ["looks good"]}
    reg.register("DUMMY_SERVICE", dummy_service)

    assert "DUMMY_SERVICE" in reg.get_all_registered_names()
    assert reg.get_service("DUMMY_SERVICE") == dummy_service
    assert reg.get_service("NONEXISTENT") is None

    reg.clear()
    assert len(reg.get_all_registered_names()) == 0


# ─── Epic 21.6 — Event Bus Tests ────────────────────────────────────────────

def test_event_bus_pub_sub():
    bus = AutonomousEventBus()
    bus.clear()

    received_events = []
    subscriber_callback = lambda ev: received_events.append(ev)

    bus.subscribe(subscriber_callback)

    event = PipelineStarted(correlation_id="corr_test")
    bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0].correlation_id == "corr_test"
    assert len(bus.get_history()) == 1


# ─── Epic 21.1 — Orchestrator Tests ─────────────────────────────────────────

def test_orchestrator_pipeline_success():
    reg = IntelligenceRegistry()
    reg.clear()
    bus = AutonomousEventBus()
    bus.clear()

    # Register two dummy services
    reg.register("STAGE_ONE", lambda ctx: {"confidence": 90.0, "reasoning": ["Stage one success"]})
    reg.register("STAGE_TWO", lambda ctx: {"confidence": 85.0, "reasoning": ["Stage two success"]})

    ctx = IntelligenceContext(symbol="BTC", side="LONG", correlation_id="corr_pipeline_test")

    orchestrator = GlobalIntelligenceOrchestrator()
    results = orchestrator.run_pipeline(ctx, ["STAGE_ONE", "STAGE_TWO", "MISSING_STAGE"])

    assert "STAGE_ONE" in results
    assert results["STAGE_ONE"].status == "SUCCESS"
    assert results["STAGE_ONE"].confidence == 90.0

    assert "STAGE_TWO" in results
    assert results["STAGE_TWO"].status == "SUCCESS"

    assert "MISSING_STAGE" in results
    assert results["MISSING_STAGE"].status == "SKIPPED"

    history = bus.get_history()
    event_types = [ev.__class__.__name__ for ev in history]
    assert "PipelineStarted" in event_types
    assert "ServiceStarted" in event_types
    assert "ServiceCompleted" in event_types
    assert "ServiceFailed" in event_types
    assert "PipelineCompleted" in event_types


# ─── Epic 21.5 — API Route Integration Tests ────────────────────────────────

def test_orchestrate_api_endpoint(api_client):
    reg = IntelligenceRegistry()
    reg.clear()
    reg.register("DUMMY_STAGE", lambda ctx: {"confidence": 92.5, "reasoning": ["API testing"]})

    payload = {
        "symbol": "BTC",
        "side": "LONG",
        "stages": ["DUMMY_STAGE", "NONEXISTENT_STAGE"],
        "correlation_id": "corr_api_test"
    }

    resp = api_client.post("/api/v1/autonomous/orchestrate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["correlation_id"] == "corr_api_test"
    assert "DUMMY_STAGE" in data["results"]
    assert data["results"]["DUMMY_STAGE"]["status"] == "SUCCESS"
    assert data["results"]["DUMMY_STAGE"]["confidence"] == 92.5
