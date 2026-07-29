import pytest
from database import Trade, Signal, DecisionDNA, CounterfactualAnalysis

# ─── Epic 3 — Simulator Tests ───────────────────────────────────────────────

def test_simulator_service_conservative(db_session):
    from services.simulator_service import DecisionSimulatorService
    # Ensure user has CONSERVATIVE DNA
    dna = DecisionDNA(user_id=1, risk_profile="CONSERVATIVE")
    db_session.add(dna)
    db_session.flush()

    svc = DecisionSimulatorService(session_factory=lambda: db_session)
    res = svc.simulate_decision(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=50000.0,
        stop_loss=40000.0, # high risk distance
        take_profit=60000.0,
        position_size=10000.0, # high position size -> high risk usd
        user_id=1
    )
    assert res is not None
    assert "Conservative" in res["primary_risks"][0]
    assert res["confidence"] < 80.0


def test_simulator_service_optimal(db_session):
    from services.simulator_service import DecisionSimulatorService
    dna = DecisionDNA(user_id=2, risk_profile="AGGRESSIVE")
    db_session.add(dna)
    db_session.flush()

    svc = DecisionSimulatorService(session_factory=lambda: db_session)
    res = svc.simulate_decision(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=50000.0,
        stop_loss=48000.0,
        take_profit=55000.0, # RR ratio > 1.5
        position_size=1000.0,
        user_id=2
    )
    assert res["expected_outcome"] == "PROFIT"
    assert res["confidence"] > 80.0


# ─── Epic 4 — Debate Engine Tests ───────────────────────────────────────────

def test_debate_engine(db_session):
    from services.debate_service import AIDebateService
    dna = DecisionDNA(user_id=1, risk_profile="CONSERVATIVE")
    db_session.add(dna)
    db_session.flush()

    svc = AIDebateService(session_factory=lambda: db_session)
    res = svc.run_debate(symbol="BTCUSDT", side="LONG", user_id=1)
    assert res is not None
    assert res["consensus_score"] == 0.60
    assert "Risk Officer" in res["minority_opinion"]
    assert res["final_recommendation"] == "APPROVE_HALF_SIZE"


# ─── Epic 5 — Counterfactual Tests ──────────────────────────────────────────

def test_counterfactual_engine_win(db_session):
    from services.counterfactual_service import CounterfactualService
    svc = CounterfactualService(session_factory=lambda: db_session)

    t = Trade(symbol="BTCUSDT", side="LONG", entry=50000.0, pnl=1000.0, status="CLOSED")
    db_session.add(t)
    db_session.flush()

    analysis = svc.analyze_counterfactuals(trade_id=t.id, user_id=1)
    assert analysis["trade_id"] == t.id
    assert analysis["actual_pnl"] == 1000.0
    assert analysis["half_size_pnl"] == 500.0
    assert analysis["optimal_scenario"] == "DELAYED_ENTRY"


def test_counterfactual_engine_loss(db_session):
    from services.counterfactual_service import CounterfactualService
    svc = CounterfactualService(session_factory=lambda: db_session)

    t = Trade(symbol="BTCUSDT", side="LONG", entry=50000.0, pnl=-500.0, status="CLOSED")
    db_session.add(t)
    db_session.flush()

    analysis = svc.analyze_counterfactuals(trade_id=t.id, user_id=1)
    assert analysis["actual_pnl"] == -500.0
    assert analysis["no_trade_delta"] == 500.0
    assert analysis["optimal_scenario"] == "TIGHT_STOP_LOSS"


# ─── Wave 2 API Integration Tests ───────────────────────────────────────────

def test_simulator_api_endpoint(api_client, db_session):
    payload = {
        "symbol": "BTCUSDT",
        "side": "LONG",
        "entry_price": 50000.0,
        "stop_loss": 49000.0,
        "take_profit": 55000.0,
        "position_size": 1000.0,
        "user_id": 1
    }
    resp = api_client.post("/api/v1/simulator", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTCUSDT"
    assert "alternative_outcomes" in data


def test_debate_api_endpoint(api_client, db_session):
    payload = {
        "symbol": "BTCUSDT",
        "side": "LONG",
        "user_id": 1
    }
    resp = api_client.post("/api/v1/debate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTCUSDT"
    assert "consensus_score" in data


def test_counterfactual_api_endpoints(api_client, db_session):
    t = Trade(symbol="BTCUSDT", side="LONG", entry=50000.0, pnl=500.0, status="CLOSED")
    db_session.add(t)
    db_session.flush()

    resp = api_client.post(f"/api/v1/counterfactuals/{t.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trade_id"] == t.id
    assert data["optimal_scenario"] == "DELAYED_ENTRY"

    resp2 = api_client.get(f"/api/v1/counterfactuals/{t.id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == data["id"]
