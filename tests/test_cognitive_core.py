from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from api.main import app
from decision.kernel.DecisionContext import DecisionContext
from decision.kernel.DecisionEvidence import DecisionEvidence
from decision.kernel.DecisionKernel import DecisionKernel
from decision.kernel.DecisionReasoning import DecisionReasoning
from decision.kernel.DecisionRequest import DecisionRequest
from decision.kernel.DecisionResult import DecisionResult
from decision.kernel.DecisionTimeline import DecisionTimeline
from decision.kernel.FounderOS import FounderBrief, FounderOS
from decision.kernel.KnowledgeGraph import GraphEdge, GraphNode, KnowledgeGraph


def test_decision_data_structures():
    """Test standard dataclasses for Unified Decision Kernel."""
    req = DecisionRequest(symbol="BTCUSDT", side="LONG", timeframe="1h", price=50000.0)
    assert req.symbol == "BTCUSDT"
    assert req.side == "LONG"
    assert req.price == 50000.0

    ctx = DecisionContext(
        indicators={"rsi": 65},
        market_regime={"regime": "BULLISH"},
    )
    assert ctx.indicators["rsi"] == 65
    assert ctx.market_regime["regime"] == "BULLISH"

    reason = DecisionReasoning(step="Trust", description="Trust factor okay", impact=0.1)
    assert reason.step == "Trust"
    assert reason.impact == 0.1

    ev = DecisionEvidence(source="WhaleIntelligence", metric_name="whale_count", metric_value=5)
    assert ev.source == "WhaleIntelligence"
    assert ev.metric_value == 5

    timeline = DecisionTimeline()
    timeline.record("Observe", "Observed setup")
    events = timeline.to_list()
    assert len(events) == 1
    assert events[0]["stage"] == "Observe"


def test_decision_kernel_cognitive_flow():
    """Test complete cognitive flow evaluation inside DecisionKernel."""
    kernel = DecisionKernel()
    req = DecisionRequest(
        symbol="ETHUSDT",
        side="LONG",
        timeframe="4h",
        price=3000.0,
        signals=["BULLISH_EMA_CROSS"],
        metadata={"score": 0.82, "confidence": 85.0},
    )
    ctx = DecisionContext(
        indicators={"final_score": 0.82, "confidence": 85.0, "rsi": 62.0},
        trust_scores={"score": 0.9},
        learning_lessons=["Always trade with EMA support"],
        calibration_metrics={"ece": 0.04},
        risk_assessment={"risk_score": 0.25},
    )

    result = kernel.decide(req, ctx)

    assert isinstance(result, DecisionResult)
    assert result.symbol == "ETHUSDT"
    assert result.decision == "STRONG_APPROVE"
    assert result.confidence == 85.0 * (1.0 - 0.04)  # calibrated: 81.6
    assert result.score == 0.82
    assert len(result.evidence) >= 2
    assert result.reasons[0].startswith("Technical indicators align")
    assert "ETHUSDT" in result.founder_summary


def test_knowledge_graph_propagation_and_queries():
    """Test Graph 2.0 nodes, edges, weight propagation, and executive query APIs."""
    kg = KnowledgeGraph()

    # 1. Expand and add nodes
    coin_eth = GraphNode(id="coin_eth", type="Coin", name="Ethereum", confidence=0.9, trust=0.95)
    trade_1 = GraphNode(id="trade_1", type="Trade", name="LONG ETH #1", confidence=0.85, trust=0.9, replay_ids=["replay_42"])
    pattern_break = GraphNode(id="pattern_break", type="Pattern", name="Breakout Pattern", confidence=0.8)

    kg.add_node(coin_eth)
    kg.add_node(trade_1)
    kg.add_node(pattern_break)

    # 2. Add semantic relationship edges
    kg.add_edge(source_id="pattern_break", target_id="trade_1", type="CAUSED", weight=0.9, confidence=0.95, trust=0.92)
    kg.add_edge(source_id="trade_1", target_id="coin_eth", type="INFLUENCED", weight=0.8, confidence=0.9, trust=0.95)
    kg.add_edge(source_id="coin_eth", target_id="coin_btc", type="SIMILAR_TO", weight=0.75)

    # 3. Test propagations
    conf_propagation = kg.propagate_confidence("pattern_break")
    assert "trade_1" in conf_propagation
    assert conf_propagation["trade_1"] == 0.8 * 0.95

    trust_propagation = kg.propagate_trust("pattern_break")
    assert "trade_1" in trust_propagation

    influence_propagation = kg.propagate_influence("trade_1")
    assert "coin_eth" in influence_propagation

    # 4. Test Queries
    # Replay traversal
    replay_nodes = kg.replay_traversal("replay_42")
    assert len(replay_nodes) == 1
    assert replay_nodes[0].id == "trade_1"

    # Why query
    why_resp = kg.why("trade_1")
    assert "rational" in why_resp["explanation"].lower() or "causal" in why_resp["explanation"].lower()

    # What caused this query
    causes = kg.what_caused_this("trade_1")
    assert len(causes) == 1
    assert causes[0]["node_id"] == "pattern_break"

    # Similarity query
    similars = kg.what_is_similar("coin_eth")
    assert len(similars) == 1
    assert similars[0]["node_id"] == "coin_btc"

    # Counterfactual simulation query
    counterfactual = kg.what_happens_if_removed("trade_1")
    assert counterfactual["cascade_count"] == 1
    assert counterfactual["affected_downstream"][0]["node_id"] == "coin_eth"

    # Predictive forecasting query
    forecast = kg.what_will_likely_happen_next("coin_eth")
    assert len(forecast["forecasts"]) > 0


def test_founder_operating_system_and_memory():
    """Test FounderOS morning briefing, memory logs, and executive command responses."""
    # Use standard test JSON memory path
    fos = FounderOS(memory_filepath="test_founder_memory.json")
    if os.path.exists("test_founder_memory.json"):
        os.remove("test_founder_memory.json")

    # Record some memories
    fos.record_decision({"symbol": "BTC", "side": "LONG", "result": "WIN"})
    fos.record_rejected_opportunity({"symbol": "SOL", "side": "SHORT", "reason": "High ATR Risk"})
    fos.record_learning_event({"lesson": "Avoid trading against the NY session trend"})

    # Generate Daily Briefing
    brief = fos.generate_brief()
    assert isinstance(brief, FounderBrief)
    assert "NEXUS analyzed" in brief.executive_summary
    assert len(brief.recommended_actions) > 0

    # Query answers
    ans_overnight = fos.query("What changed overnight?")
    assert "Regime" in ans_overnight["answer"] or "regime" in ans_overnight["answer"].lower()

    ans_attention = fos.query("What deserves attention?")
    assert "whales" in ans_attention["answer"].lower()

    ans_avoid = fos.query("What should I absolutely avoid today?")
    assert "FOMO" in ans_avoid["answer"]

    # Cleanup test memory file
    if os.path.exists("test_founder_memory.json"):
        os.remove("test_founder_memory.json")


def test_api_integration_endpoints(api_client):
    """Test all new REST endpoints under /founder/ and /graph/ prefixes using TestClient."""
    client = api_client

    # 1. Test Founder OS morning brief
    resp = client.get("/founder/brief")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "executive_summary" in data["brief"]

    # 2. Test Executive query command
    resp = client.post("/founder/query", json={"question": "What deserves attention?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "answer" in data["response"]

    # 3. Test Register Executive Action
    resp = client.post("/founder/action", json={"action_type": "MANUAL_REJECT", "details": {"symbol": "ETH"}})
    assert resp.status_code == 200
    data = resp.json()
    assert "registered executive action" in data["message"]

    # 4. Test Institutional memory lists
    resp = client.get("/founder/memory")
    assert resp.status_code == 200
    data = resp.json()
    assert "executive_actions" in data["memory"]

    # 5. Test Graph Nodes and Edges
    resp = client.get("/graph/nodes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) >= 2  # default nodes registered

    # Create new node via API
    node_payload = {
        "id": "coin_sol",
        "type": "Coin",
        "name": "Solana",
        "confidence": 0.88,
        "trust": 0.91,
    }
    resp = client.post("/graph/nodes", json=node_payload)
    assert resp.status_code == 200

    # Extract local subgraph
    resp = client.get("/graph/subgraph/coin_sol")
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_id"] == "coin_sol"

    # Why query
    resp = client.get("/graph/why/coin_sol")
    assert resp.status_code == 200
    data = resp.json()
    assert "explanation" in data["explanation"]
