from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
import pytest
from database import SimulationSession, SimulationTrade, get_session
from simulator.replay_engine import ReplayEngine, ScenarioGenerator
from simulator.simulator_service import SimulatorService

logger = logging.getLogger(__name__)


def test_scenario_generator():
    ticks = ScenarioGenerator.generate(
        scenario_name="FLASH_CRASH",
        symbol="BTC",
        timeframe="1H",
        start_date=datetime.now(timezone.utc),
        length=50,
    )
    assert len(ticks) == 50
    assert any(len(t.whales) > 0 for t in ticks)
    assert any(len(t.news) > 0 for t in ticks)


def test_replay_engine():
    ticks = ScenarioGenerator.generate(
        scenario_name="BULL_RUN",
        symbol="ETH",
        timeframe="15m",
        start_date=datetime.now(timezone.utc),
        length=20,
    )
    engine = ReplayEngine(ticks)
    assert engine.total_ticks == 20
    assert engine.current_index == 0

    tick = engine.step()
    assert tick is not None
    assert engine.current_index == 1

    engine.pause()
    assert engine.is_playing is False

    engine.start()
    assert engine.is_playing is True

    engine.jump_to_date(ticks[10].timestamp)
    assert engine.current_index == 10


def test_simulator_service():
    service = SimulatorService()
    now_dt = datetime.now(timezone.utc)
    sid = service.create_session(
        symbol="BTC",
        timeframe="1H",
        start_date=now_dt,
        end_date=now_dt + timedelta(days=2),
        scenario_name="ETF_NEWS",
        length=35,
    )
    assert sid is not None
    assert service.replay_engine is not None
    assert service.replay_engine.total_ticks == 35

    state = service.get_current_state()
    assert state is not None
    assert "tick" in state
    assert "council" in state
    assert "evidence" in state
    assert "explain" in state

    trades: list = []
    scorecard = service.calculate_training_scorecard(trades)
    assert scorecard["score"] == 0


# ─── API Router Integration Tests ──────────────────────────────────────────


def test_api_create_and_list_sessions(api_client):
    payload = {
        "name": "Test Simulation Run",
        "symbol": "BTC",
        "timeframe": "1H",
        "scenario_name": "RANGE",
        "length": 30,
        "base_price": 50000.0,
    }
    create_resp = api_client.post("/simulator/sessions", json=payload)
    assert create_resp.status_code == 200
    body = create_resp.json()
    assert body["name"] == "Test Simulation Run"
    assert body["symbol"] == "BTC"
    session_id = body["id"]

    list_resp = api_client.get("/simulator/sessions")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_api_playback_controls(api_client, db_session):
    # Seed session
    s = SimulationSession(
        name="Test Playback",
        symbol="BTC",
        timeframe="1H",
        scenario_name="RANGE",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=5),
        current_index=0,
    )
    db_session.add(s)
    db_session.flush()

    # Pause
    resp = api_client.post(f"/simulator/sessions/{s.id}/pause")
    assert resp.status_code == 200
    assert resp.json()["is_playing"] is False

    # Speed
    resp = api_client.post(f"/simulator/sessions/{s.id}/speed", json={"speed": 5.0})
    assert resp.status_code == 200
    assert resp.json()["speed"] == 5.0

    # Step
    resp = api_client.post(f"/simulator/sessions/{s.id}/step")
    assert resp.status_code == 200
    assert resp.json()["tick_index"] == 1


def test_api_trading_controls(api_client, db_session):
    s = SimulationSession(
        name="Test Trading",
        symbol="BTC",
        timeframe="1H",
        scenario_name="RANGE",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=5),
        current_index=0,
    )
    db_session.add(s)
    db_session.flush()

    # Step once to initialize current tick in service
    api_client.post(f"/simulator/sessions/{s.id}/step")

    # Place trade
    trade_payload = {
        "side": "LONG",
        "entry_price": 50000.0,
        "quantity": 1.5,
        "leverage": 5.0,
        "stop_loss": 48000.0,
        "take_profit": 55000.0,
    }
    resp = api_client.post(f"/simulator/sessions/{s.id}/trades", json=trade_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["side"] == "LONG"
    assert body["quantity"] <= 1.5
    assert body["quantity"] > 0
    trade_id = body["id"]

    # Close trade
    resp = api_client.put(f"/simulator/sessions/{s.id}/trades/{trade_id}/close")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CLOSED"
    assert resp.json()["close_reason"] == "MANUAL"

    # Report
    resp = api_client.get(f"/simulator/sessions/{s.id}/report")
    assert resp.status_code == 200
    assert "scorecard" in resp.json()
    assert "statistics" in resp.json()
