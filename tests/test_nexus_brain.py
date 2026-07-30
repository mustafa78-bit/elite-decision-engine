import pytest
from core.nexus_brain.blackboard import CognitiveBlackboard, BlackboardEvent, EventPriority
from core.nexus_brain.memory import EpisodicMemory
from core.nexus_brain.guard import ConstraintGuard, GuardOutcome
from core.nexus_brain.learning import DecoupledCalibrationEngine, AdaptiveThresholdController
from core.nexus_brain.intelligence import MultiAgentCore
from core.nexus_brain.decision import DecisionGraph
from core.nexus_brain.ai_engine import AIEngine
from core.nexus_brain.founder_platform import FounderPlatformCoordinator

def test_blackboard_event_priority_ordering():
    bb = CognitiveBlackboard()
    ev1 = BlackboardEvent("SIGNAL", {"id": 1}, "test", EventPriority.LOW)
    ev2 = BlackboardEvent("SIGNAL", {"id": 2}, "test", EventPriority.CRITICAL)
    ev3 = BlackboardEvent("SIGNAL", {"id": 3}, "test", EventPriority.HIGH)

    bb.post_event(ev1)
    bb.post_event(ev2)
    bb.post_event(ev3)

    assert bb.queue[0].priority == EventPriority.CRITICAL
    assert bb.queue[1].priority == EventPriority.HIGH
    assert bb.queue[2].priority == EventPriority.LOW

def test_blackboard_subscriptions_and_dispatch():
    bb = CognitiveBlackboard()
    received = []

    def mock_handler(event: BlackboardEvent):
        received.append(event.payload["data"])

    bb.register_subscriber("TEST_EVENT", mock_handler)
    ev = BlackboardEvent("TEST_EVENT", {"data": "hello_world"}, "test_producer", EventPriority.MEDIUM)
    bb.post_event(ev)

    dispatched = bb.dispatch_next()
    assert dispatched is not None
    assert dispatched.event_id == ev.event_id
    assert len(received) == 1
    assert received[0] == "hello_world"

def test_episodic_memory_storage_and_replay():
    mem = EpisodicMemory()
    event_log = [{"event": "test"}]

    ep = mem.record_episode(
        signal_id=101,
        symbol="ETHUSDT",
        side="SHORT",
        score=0.92,
        confidence=88.5,
        reasoning_chain=["PASS: Checked rules"],
        guard_status="PASS",
        event_chain=event_log
    )

    assert ep["symbol"] == "ETHUSDT"
    assert ep["replay_reconstructable"] is True

    fetched = mem.get_episode_by_signal(101)
    assert fetched["score"] == 0.92
    assert len(fetched["event_chain"]) == 1

def test_constraint_guard_non_binary_outcomes():
    guard = ConstraintGuard(max_open_trades=2, max_exposure_per_symbol=10000.0, max_daily_loss=500.0)

    # Test PASS
    outcome, reasons = guard.evaluate("BTCUSDT", active_trades_count=0, symbol_exposure=1000.0, current_daily_loss=0.0, score=0.90)
    assert outcome == GuardOutcome.PASS

    # Test WARN
    outcome, reasons = guard.evaluate("BTCUSDT", active_trades_count=1, symbol_exposure=9000.0, current_daily_loss=50.0, score=0.90)
    assert outcome == GuardOutcome.WARN
    assert any("WARN" in r for r in reasons)

    # Test REJECT (Too low score)
    outcome, reasons = guard.evaluate("BTCUSDT", active_trades_count=1, symbol_exposure=1000.0, current_daily_loss=50.0, score=0.65)
    assert outcome == GuardOutcome.REJECT
    assert any("score" in r for r in reasons)

def test_decoupled_calibration_and_adaptive_thresholds():
    engine = DecoupledCalibrationEngine()

    # 4-factor inputs (Success, Agreement, Evidence, Uncertainty)
    conf = engine.calculate_confidence(0.90, 0.95, 0.85, 0.10)
    assert conf > 50.0
    assert conf <= 100.0

    ctrl = AdaptiveThresholdController(base_threshold=0.85)
    threshold = ctrl.adapt(0.80)  # High win rate adapts threshold down
    assert threshold < 0.85

    threshold2 = ctrl.adapt(0.40) # Low win rate adapts threshold up
    assert threshold2 > threshold

def test_multi_agent_blackboard_coordination():
    core = MultiAgentCore()
    res = core.process({"symbol": "SOLUSDT", "side": "LONG"})

    assert res["agent_network_status"] == "ONLINE"
    assert "critic" in res["evaluations"]
    assert res["blackboard_replays"] == 7  # 1 Ingest + 6 Agents

def test_decision_graph_building():
    dg = DecisionGraph()
    dg.add_decision_node("node1", {"p": 1})
    dg.add_decision_node("node2", {"p": 2})
    dg.link_nodes("node1", "node2")

    assert "node1" in dg.nodes
    assert "node2" in dg.nodes
    assert "node2" in dg.nodes["node1"].edges

def test_ai_engine_utilities():
    eng = AIEngine()
    episodes = eng.retrieve_similar_episodes("test")
    assert len(episodes) == 1
    assert episodes[0]["similarity_score"] == 0.94

    hyp = eng.generate_hypothesis("BTC", "up")
    assert "confidence_estimate" in hyp

    causal = eng.run_causal_analysis("rate")
    assert causal["influence_percentage"] == 75.0

def test_founder_platform_coordinator():
    coord = FounderPlatformCoordinator()
    pref = coord.get_founder_preferences()
    assert pref["risk_mode"] == "conservative"

    coord.update_founder_preference("risk_mode", "aggressive")
    assert coord.get_founder_preferences()["risk_mode"] == "aggressive"

    telemetry = coord.get_platform_telemetry()
    assert telemetry["market_intelligence_status"] == "ONLINE"
