import pytest
from datetime import datetime, timezone, timedelta
from database import Trade, Signal, DecisionDNA, CognitiveBiasLog

# ─── Epic 1 — DNA Engine Tests ──────────────────────────────────────────────

def test_dna_get_or_create_profile(db_session):
    from services.dna_service import DecisionDNAService
    svc = DecisionDNAService(session_factory=lambda: db_session)

    profile = svc.get_or_create_profile(user_id=42)
    assert profile is not None
    assert profile["user_id"] == 42
    assert profile["risk_profile"] == "MODERATE"
    assert profile["trading_discipline_score"] == 100.0

    # Ensure get_or_create returns existing if already present
    dna = db_session.query(DecisionDNA).filter(DecisionDNA.user_id == 42).first()
    dna.risk_profile = "CONSERVATIVE"
    db_session.commit()

    profile2 = svc.get_or_create_profile(user_id=42)
    assert profile2["risk_profile"] == "CONSERVATIVE"


def test_dna_rebuild_from_history(db_session):
    from services.dna_service import DecisionDNAService
    svc = DecisionDNAService(session_factory=lambda: db_session)

    # Create fake historical signals & trades
    s = Signal(symbol="BTCUSDT", side="LONG", divergence="EMA_CROSS", status="EXECUTED")
    db_session.add(s)
    db_session.flush()

    t1 = Trade(
        signal_id=s.id,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        status="CLOSED",
        pnl=150.0,
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
        closed_at=datetime.now(timezone.utc)
    )
    t2 = Trade(
        signal_id=s.id,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        status="SL_HIT",
        pnl=-50.0,
        created_at=datetime.now(timezone.utc) - timedelta(hours=1),
        closed_at=datetime.now(timezone.utc)
    )
    db_session.add_all([t1, t2])
    db_session.flush()

    profile = svc.update_profile_from_history(user_id=1)
    assert profile["win_loss_ratio"] == 1.0 # 1 win, 1 loss
    assert profile["preferred_strategies"] == ["EMA_CROSS"]
    assert profile["trading_discipline_score"] == 95.0 # penalty of 5.0 for 1 SL_HIT


# ─── Epic 2 — Cognitive Bias Detection Tests ─────────────────────────────────

def test_bias_fomo_detection(db_session):
    from services.bias_service import CognitiveBiasService
    svc = CognitiveBiasService(session_factory=lambda: db_session)

    s = Signal(symbol="BTCUSDT", side="LONG", price=50000.0)
    db_session.add(s)
    db_session.flush()

    # Buy at 52000.0 (>4% above recommended entry price of 50000.0)
    t = Trade(signal_id=s.id, symbol="BTCUSDT", side="LONG", entry=52000.0)
    db_session.add(t)
    db_session.flush()

    biases = svc.detect_biases_for_trade(user_id=1, trade_id=t.id)
    assert len(biases) == 1
    assert biases[0]["bias_type"] == "FOMO"
    assert biases[0]["confidence"] == 0.9


def test_bias_revenge_trading_detection(db_session):
    from services.bias_service import CognitiveBiasService
    svc = CognitiveBiasService(session_factory=lambda: db_session)

    now = datetime.now(timezone.utc)

    # First trade closed with SL_HIT 5 minutes ago
    t1 = Trade(symbol="BTCUSDT", side="LONG", status="SL_HIT", closed_at=now - timedelta(minutes=5))
    # Second trade opened now
    t2 = Trade(symbol="BTCUSDT", side="LONG", status="OPEN", created_at=now)

    db_session.add_all([t1, t2])
    db_session.flush()

    biases = svc.detect_biases_for_trade(user_id=1, trade_id=t2.id)
    assert len(biases) == 1
    assert biases[0]["bias_type"] == "REVENGE_TRADING"
    assert biases[0]["confidence"] == 0.85


# ─── Epic 10 — Decision Quality Score Tests ──────────────────────────────────

def test_dqs_score_calculation(db_session):
    from services.dqs_service import DQSService
    svc = DQSService(session_factory=lambda: db_session)

    s = Signal(symbol="BTCUSDT", side="LONG", confidence=95.0, price=50000.0)
    db_session.add(s)
    db_session.flush()

    # Perfect entry, perfect stop loss, positive PnL
    t = Trade(signal_id=s.id, symbol="BTCUSDT", side="LONG", entry=50000.0, stop=49000.0, pnl=500.0, status="CLOSED")
    db_session.add(t)
    db_session.flush()

    res = svc.calculate_dqs_for_trade(t.id)
    assert "error" not in res
    assert res["score"] > 80.0
    assert res["breakdown"]["evidence_quality"] == 95.0
    assert res["breakdown"]["timing_accuracy"] == 100.0


# ─── Wave 1 API Endpoints Integration Tests ─────────────────────────────────

def test_dna_api_endpoints(api_client, db_session):
    resp = api_client.get("/api/v1/dna?user_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 1
    assert data["risk_profile"] == "MODERATE"

    resp2 = api_client.post("/api/v1/dna/rebuild?user_id=1")
    assert resp2.status_code == 200
    assert resp2.json()["user_id"] == 1


def test_bias_api_endpoints(api_client, db_session):
    resp = api_client.get("/api/v1/biases?user_id=1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_dqs_api_endpoints(api_client, db_session):
    s = Signal(symbol="BTCUSDT", side="LONG", confidence=95.0, price=50000.0)
    db_session.add(s)
    db_session.flush()

    t = Trade(signal_id=s.id, symbol="BTCUSDT", side="LONG", entry=50000.0, stop=49000.0, pnl=500.0)
    db_session.add(t)
    db_session.flush()

    resp = api_client.get(f"/api/v1/dqs/{t.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trade_id"] == t.id
    assert data["score"] > 0.0
