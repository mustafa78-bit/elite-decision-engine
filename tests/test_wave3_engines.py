import pytest
from database import Trade, Signal, DecisionDNA, CognitiveBiasLog, CoachingRecommendation, MarketRegimeSnap

# ─── Epic 6 — Coaching Tests ───────────────────────────────────────────────

def test_coaching_service_fomo_pattern(db_session):
    from services.coaching_service import CoachingService
    svc = CoachingService(session_factory=lambda: db_session)

    # Inject some FOMO bias logs
    b = CognitiveBiasLog(user_id=1, decision_id=10, bias_type="FOMO", explanation="test", suggested_improvement="test")
    db_session.add(b)
    db_session.flush()

    recs = svc.generate_recommendations(user_id=1)
    assert len(recs) >= 1
    assert any(r["category"] == "PATTERN_BREAK" for r in recs)


def test_coaching_service_habit_strength(db_session):
    from services.coaching_service import CoachingService
    svc = CoachingService(session_factory=lambda: db_session)

    dna = DecisionDNA(user_id=2, risk_profile="MODERATE", trading_discipline_score=80.0)
    db_session.add(dna)
    db_session.flush()

    recs = svc.generate_recommendations(user_id=2)
    assert len(recs) >= 1
    assert any(r["category"] == "HABIT_STRENGTHENING" for r in recs)


# ─── Epic 7 — Market Memory Tests ───────────────────────────────────────────

def test_market_memory_record_and_query(db_session):
    from services.market_memory_service import MarketMemoryService
    svc = MarketMemoryService(session_factory=lambda: db_session)

    snap = svc.record_regime_snapshot(
        symbol="BTC",
        price=50000.0,
        ema20=51000.0,
        ema50=50500.0,
        ema200=50200.0, # TREND (BULLISH)
        atr=200.0,
        rsi=65.0
    )
    assert snap["regime_type"] == "TREND"

    matches = svc.get_similar_contexts("TREND")
    assert len(matches) == 1
    assert matches[0]["symbol"] == "BTC"


# ─── Epic 8 — Strategic Intelligence Tests ─────────────────────────────────

def test_strategic_intelligence_orchestration(db_session):
    from services.strategic_intelligence_service import StrategicIntelligenceService
    svc = StrategicIntelligenceService(session_factory=lambda: db_session)

    assessment = svc.generate_strategic_assessment(symbol="BTC", user_id=1)
    assert assessment is not None
    assert assessment["symbol"] == "BTC"
    assert assessment["strategic_score"] > 0.0
    assert len(assessment["recommendations"]) >= 1


# ─── Wave 3 API Integration Tests ───────────────────────────────────────────

def test_coaching_api_endpoint(api_client, db_session):
    resp = api_client.get("/api/v1/coaching?user_id=1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_market_memory_api_endpoints(api_client, db_session):
    payload = {
        "symbol": "BTC",
        "price": 50000.0,
        "ema20": 51000.0,
        "ema50": 50500.0,
        "ema200": 50200.0,
        "atr": 200.0,
        "rsi": 65.0
    }
    resp = api_client.post("/api/v1/market-memory/snapshot", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC"
    assert data["regime_type"] == "TREND"

    resp2 = api_client.get("/api/v1/market-memory?regime=TREND")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1


def test_strategic_intelligence_api_endpoint(api_client, db_session):
    resp = api_client.get("/api/v1/strategic-intelligence?symbol=BTC&user_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC"
    assert data["strategic_score"] > 0.0
