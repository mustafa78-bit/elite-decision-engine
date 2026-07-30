import pytest
from datetime import datetime, timezone, timedelta
from database import Base, create_engine, sessionmaker
from core.experience.models import ExperienceSubstrate, InstinctState, ExperienceGraduation
from core.experience.service import (
    ExperienceSubstrateService,
    InstinctStateService,
    FamiliaritySignalService,
    ExperienceVsKnowledgeService,
    ExperienceSufficiencyService,
    ExperienceGraduationService,
)

@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing the Experience Engine."""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_record_and_realize_substrate(test_db):
    """Verify that we can record and realize substrates properly."""
    t1 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    exp = ExperienceSubstrateService.record_experience(
        session=test_db,
        timestamp=t1,
        symbol="BTCUSDT",
        timeframe="1h",
        state_snapshot={"trend_score": 0.8, "rsi": 60, "regime": "TREND"},
        action_taken="LONG",
    )
    assert exp.id is not None
    assert exp.outcome is None
    assert exp.realized_at is None

    # Realize the experience chronologically
    t2 = t1 + timedelta(minutes=30)
    success = ExperienceSubstrateService.realize_experience(test_db, exp.id, 150.5, t2)
    assert success is True

    # Refresh from database
    refreshed = test_db.query(ExperienceSubstrate).filter(ExperienceSubstrate.id == exp.id).first()
    assert refreshed.outcome == 150.5

    # SQLite datetimes are returned naive. Force UTC comparison.
    refreshed_realized = refreshed.realized_at.replace(tzinfo=timezone.utc) if refreshed.realized_at.tzinfo is None else refreshed.realized_at
    assert refreshed_realized == t2


def test_walk_forward_query_isolation(test_db):
    """Verify that future information is never accessible and lookups are isolated walk-forward."""
    t1 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(hours=1)
    t3 = t1 + timedelta(hours=2)

    ExperienceSubstrateService.record_experience(
        test_db, t1, "BTCUSDT", "1h", {"rsi": 50}, "LONG"
    )
    ExperienceSubstrateService.record_experience(
        test_db, t2, "BTCUSDT", "1h", {"rsi": 60}, "LONG"
    )
    ExperienceSubstrateService.record_experience(
        test_db, t3, "BTCUSDT", "1h", {"rsi": 70}, "LONG"
    )

    # At t1, we should only see 1 experience
    results_t1 = ExperienceSubstrateService.get_historical_substrate(test_db, t1, "BTCUSDT", "1h")
    assert len(results_t1) == 1
    assert results_t1[0].state_snapshot["rsi"] == 50

    # At t2, we should see 2 experiences
    results_t2 = ExperienceSubstrateService.get_historical_substrate(test_db, t2, "BTCUSDT", "1h")
    assert len(results_t2) == 2

    # A query at t1 - 1 sec should see 0 experiences (strict isolation)
    results_past = ExperienceSubstrateService.get_historical_substrate(test_db, t1 - timedelta(seconds=1), "BTCUSDT", "1h")
    assert len(results_past) == 0


def test_evolving_instinct_disposition(test_db):
    """Verify that InstinctState has evolving behavioral dispositions that change with outcomes."""
    t1 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Create 3 winning experiences
    for i in range(3):
        t_exp = t1 + timedelta(hours=i)
        exp = ExperienceSubstrateService.record_experience(
            test_db, t_exp, "BTCUSDT", "1h", {"rsi": 50}, "LONG"
        )
        ExperienceSubstrateService.realize_experience(test_db, exp.id, 50.0, t_exp + timedelta(minutes=15))

    instinct = InstinctStateService.compute_and_update_instinct(test_db, "BTCUSDT", "1h", t1 + timedelta(hours=4))
    disp_wins = dict(instinct.disposition_vector)

    assert instinct.total_trades == 3
    assert instinct.win_rate == 1.0
    assert instinct.vibe_score > 0

    # Defensiveness should decrease, courage and conviction should increase on winning
    assert disp_wins["defensiveness"] < 0.3
    assert disp_wins["conviction"] > 0.5


def test_chronological_integrity_reordering_effects(test_db):
    """Verify that reordering experiences changes the resulting Instinct State (chronological integrity)."""
    t_start = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Sequence A: 3 wins then 3 losses
    # Sequence B: 3 losses then 3 wins
    # Because of the rolling/chronological proportional update, Sequence A and Sequence B must yield different final vectors!

    # Create Instinct State for Sequence A
    for i in range(3):
        t_exp = t_start + timedelta(hours=i)
        exp = ExperienceSubstrateService.record_experience(
            test_db, t_exp, "SEQA", "1h", {"rsi": 50}, "LONG"
        )
        ExperienceSubstrateService.realize_experience(test_db, exp.id, 10.0, t_exp + timedelta(minutes=15))

    for i in range(3, 6):
        t_exp = t_start + timedelta(hours=i)
        exp = ExperienceSubstrateService.record_experience(
            test_db, t_exp, "SEQA", "1h", {"rsi": 50}, "LONG"
        )
        ExperienceSubstrateService.realize_experience(test_db, exp.id, -10.0, t_exp + timedelta(minutes=15))

    instinct_a = InstinctStateService.compute_and_update_instinct(test_db, "SEQA", "1h", t_start + timedelta(hours=10))
    disp_a = instinct_a.disposition_vector

    # Create Instinct State for Sequence B (Reordered: losses first, then wins)
    for i in range(3):
        t_exp = t_start + timedelta(hours=i)
        exp = ExperienceSubstrateService.record_experience(
            test_db, t_exp, "SEQB", "1h", {"rsi": 50}, "LONG"
        )
        ExperienceSubstrateService.realize_experience(test_db, exp.id, -10.0, t_exp + timedelta(minutes=15))

    for i in range(3, 6):
        t_exp = t_start + timedelta(hours=i)
        exp = ExperienceSubstrateService.record_experience(
            test_db, t_exp, "SEQB", "1h", {"rsi": 50}, "LONG"
        )
        ExperienceSubstrateService.realize_experience(test_db, exp.id, 10.0, t_exp + timedelta(minutes=15))

    instinct_b = InstinctStateService.compute_and_update_instinct(test_db, "SEQB", "1h", t_start + timedelta(hours=10))
    disp_b = instinct_b.disposition_vector

    # Confirm win rates are identical
    assert instinct_a.win_rate == instinct_b.win_rate

    # Confirm disposition vector values differ due to chronological order
    assert disp_a["defensiveness"] != disp_b["defensiveness"]
    assert disp_a["conviction"] != disp_b["conviction"]


def test_familiarity_consults_distilled_instinct(test_db):
    """Verify FamiliaritySignal does not run costly DB lookups but consults pre-distilled InstinctState."""
    t1 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    features = {"trend_score": 0.8, "rsi": 65, "regime": "TREND"}

    # No instinct compiled yet
    fam1 = FamiliaritySignalService.calculate_familiarity(test_db, "BTCUSDT", "1h", features, t1)
    assert fam1 == 0.0

    # Insert experience and pre-distill instinct
    exp = ExperienceSubstrateService.record_experience(
        test_db, t1, "BTCUSDT", "1h", {"rsi": 50}, "LONG"
    )
    ExperienceSubstrateService.realize_experience(test_db, exp.id, 50.0, t1 + timedelta(minutes=15))
    InstinctStateService.compute_and_update_instinct(test_db, "BTCUSDT", "1h", t1 + timedelta(minutes=30))

    # Calculate familiarity: should now retrieve non-zero score consulting the distilled instinct
    fam2 = FamiliaritySignalService.calculate_familiarity(test_db, "BTCUSDT", "1h", features, t1 + timedelta(hours=1))
    assert fam2 > 0.0


def test_experience_vs_knowledge_independent_dimensions(test_db):
    """Verify that experience and knowledge scores remain independent dimensions."""
    t1 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
    features = {"trend_score": 0.8, "rsi": 65, "regime": "TREND"}

    res = ExperienceVsKnowledgeService.contrast_experience_vs_knowledge(
        test_db, "BTCUSDT", "1h", features, 0.9, t1
    )

    # Assert they are returned as separate independent entities
    assert "knowledge_dimension" in res
    assert "experience_dimension" in res
    assert res["knowledge_dimension"]["score"] == 0.9
    assert res["experience_dimension"]["score"] == 0.5  # Neutral default


def test_experience_sufficiency_rules(test_db):
    """Verify sufficiency is only reached after both event count and duration requirements are met."""
    t1 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)

    # 0 events -> insufficient
    suff = ExperienceSufficiencyService.check_sufficiency(test_db, "BTCUSDT", "1h", t1)
    assert suff["is_sufficient"] is False

    # Insert 5 events but within 2 hours -> insufficient duration
    for i in range(5):
        t_exp = t1 + timedelta(minutes=15 * i)
        ExperienceSubstrateService.record_experience(
            test_db, t_exp, "BTCUSDT", "1h", {"rsi": 50}, "LONG"
        )

    suff_short_duration = ExperienceSufficiencyService.check_sufficiency(test_db, "BTCUSDT", "1h", t1 + timedelta(hours=2))
    assert suff_short_duration["is_sufficient"] is False

    # Insert enough duration -> sufficient
    suff_sufficient = ExperienceSufficiencyService.check_sufficiency(test_db, "BTCUSDT", "1h", t1 + timedelta(hours=26))
    assert suff_sufficient["is_sufficient"] is True


def test_governance_blocks_unauthorized_graduation(test_db):
    """Verify graduation recommendation does not activate rules and only explicit governance approve promotes."""
    t1 = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Make sufficient and profitable experiences
    for i in range(6):
        t_exp = t1 + timedelta(hours=6 * i)
        exp = ExperienceSubstrateService.record_experience(
            test_db, t_exp, "BTCUSDT", "1h", {"rsi": 50, "regime": "TREND"}, "LONG"
        )
        ExperienceSubstrateService.realize_experience(test_db, exp.id, 100.0, t_exp + timedelta(hours=2))

    t_eval = t1 + timedelta(hours=40)

    # Evaluate recommendation
    rec = ExperienceGraduationService.evaluate_graduation_recommendation(test_db, "BTCUSDT", "1h", t_eval)
    assert rec.status == "RECOMMENDED"
    assert rec.graduated is False  # Blocks automatic promotion!
    assert rec.governance_rules == {}  # No multipliers applied!

    # Explicit governance approval activates promotion
    approved = ExperienceGraduationService.approve_graduation(test_db, "BTCUSDT", "1h", "FOUNDER_GOVERNOR", t_eval)
    assert approved.status == "APPROVED_BY_GOVERNANCE"
    assert approved.graduated is True
    assert approved.governance_rules["position_size_multiplier"] == 1.25

    # Revocation blocks graduation
    revoked = ExperienceGraduationService.reject_graduation(test_db, "BTCUSDT", "1h", "FOUNDER_GOVERNOR", t_eval)
    assert revoked.status == "REJECTED_BY_GOVERNANCE"
    assert revoked.graduated is False
    assert revoked.governance_rules["position_size_multiplier"] == 1.0


def test_experience_api_endpoints(api_client, db_session):
    """Verify Experience REST endpoints using the patched api_client and JWT tokens."""
    from auth.jwt import create_access_token
    from database import User

    # 1. Setup authenticated user
    u = User(username="test_gov", email="gov@nexus.ai", hashed_password="hashed_placeholder")
    db_session.add(u)
    db_session.flush()

    token = create_access_token({"sub": str(u.id), "username": u.username})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test manual produce (testing utility endpoint)
    payload = {
        "timestamp": "2026-07-10T12:00:00Z",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "state_snapshot": {"trend_score": 0.8, "rsi": 65, "regime": "TREND"},
        "action_taken": "LONG",
        "outcome": 100.5,
        "realized_at": "2026-07-10T12:30:00Z"
    }
    resp = api_client.post("/api/v1/experience/test-produce", json=payload, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["message"] == "Experience produced successfully for testing"

    # 3. Test read-oriented substrate query
    resp = api_client.get("/api/v1/experience/substrate?symbol=BTCUSDT&timeframe=1h&current_time=2026-07-10T15:00:00Z", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["action_taken"] == "LONG"

    # 4. Test read-oriented instinct query
    resp = api_client.get("/api/v1/experience/instinct?symbol=BTCUSDT&timeframe=1h&current_time=2026-07-10T15:00:00Z", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "BTCUSDT"
    assert resp.json()["disposition_vector"]["conviction"] > 0.0

    # 5. Test familiarity endpoint with query parameters
    features_payload = {
        "trend_score": 0.8,
        "volume_score": 0.7,
        "rsi": 65,
        "regime": "TREND",
        "confidence": 0.8,
        "score": 0.8
    }
    resp = api_client.post("/api/v1/experience/familiarity?symbol=BTCUSDT&timeframe=1h&current_time=2026-07-10T15:00:00Z", json=features_payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["consulted_instinct"] is True

    # 6. Test contrast endpoint
    contrast_payload = {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "current_features": {
            "trend_score": 0.8,
            "volume_score": 0.7,
            "rsi": 65,
            "regime": "TREND",
            "confidence": 0.8,
            "score": 0.8
        },
        "knowledge_score": 0.95
    }
    resp = api_client.post("/api/v1/experience/contrast?current_time=2026-07-10T15:00:00Z", json=contrast_payload, headers=headers)
    assert resp.status_code == 200
    assert "knowledge_dimension" in resp.json()
    assert "experience_dimension" in resp.json()

    # 7. Test sufficiency endpoint
    resp = api_client.get("/api/v1/experience/sufficiency?symbol=BTCUSDT&timeframe=1h&current_time=2026-07-10T15:00:00Z", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_sufficient"] is False # Need more events

    # 8. Test graduation recommendation
    resp = api_client.get("/api/v1/experience/graduation/recommendation?symbol=BTCUSDT&timeframe=1h&current_time=2026-07-10T15:00:00Z", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "PENDING"
    assert resp.json()["graduated"] is False

    # 9. Test Governance Explicit Approval Action
    gov_payload = {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "governor_name": "FOUNDER_CHIEF"
    }
    resp = api_client.post("/api/v1/experience/governance/approve?current_time=2026-07-10T15:00:00Z", json=gov_payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED_BY_GOVERNANCE"
    assert resp.json()["graduated"] is True
    assert resp.json()["governance_rules"]["approved_by"] == "FOUNDER_CHIEF"
