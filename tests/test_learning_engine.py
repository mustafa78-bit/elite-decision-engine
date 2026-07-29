import math
import pytest
from database import Signal, Trade, DecisionExplanation, DecisionMemory
from services.learning.decision_memory import DecisionMemoryService
from services.learning.pattern_discovery import PatternDiscoveryService
from services.learning.calibration_engine import CalibrationService
from services.learning.drift_detection import DriftDetectionEngine


# ─── DECISION MEMORY SYNC TESTS ─────────────────────────────────────────────


def test_decision_memory_sync(db_session):
    # Seed Signal, Trade, and DecisionExplanation
    sig = Signal(
        symbol="BTCUSDT",
        side="LONG",
        timeframe="1h",
        price=50000.0,
        trend_score=0.8,
        volume_score=0.7,
        btc_health=0.9,
        risk_score=0.2,
        confidence=85.0,
        score=75.0,
        status="EXECUTED",
        reason="Strong trend breakout",
    )
    db_session.add(sig)
    db_session.flush()

    trade = Trade(
        signal_id=sig.id,
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        pnl=150.0,
        status="CLOSED",
    )
    db_session.add(trade)
    db_session.flush()

    expl = DecisionExplanation(
        signal_id=sig.id,
        symbol="BTCUSDT",
        side="LONG",
        decision="BUY",
        confidence=85.0,
        reasons=["Trend alignment confirms long"],
        summary="A clear bullish trend alignment",
    )
    db_session.add(expl)
    db_session.flush()

    sig_id = sig.id

    # Run Memory Sync
    svc = DecisionMemoryService(session_factory=lambda: db_session)
    synced = svc.sync_memories()
    assert synced == 1

    # Verify memory
    mem = db_session.query(DecisionMemory).filter(DecisionMemory.signal_id == sig_id).first()
    assert mem is not None
    assert mem.symbol == "BTCUSDT"
    assert mem.side == "LONG"
    assert mem.decision_dna["trend_score"] == 0.8
    assert mem.decision_dna["confidence"] == 85.0
    assert mem.outcome["pnl"] == 150.0
    assert mem.outcome["result"] == "WIN"
    assert "A clear bullish trend alignment" in mem.reasoning_chain


# ─── SIMILARITY SEARCH COSINE TESTS ─────────────────────────────────────────


def test_similarity_search_cosine():
    svc = DecisionMemoryService()

    # Test identical vectors
    vec_a = [1.0, 1.0, 1.0]
    vec_b = [1.0, 1.0, 1.0]
    sim = svc._cosine_similarity(vec_a, vec_b)
    assert math.isclose(sim, 1.0, rel_tol=1e-5)

    # Test completely orthogonal vectors
    vec_c = [1.0, 0.0, 0.0]
    vec_d = [0.0, 1.0, 0.0]
    sim_ortho = svc._cosine_similarity(vec_c, vec_d)
    assert math.isclose(sim_ortho, 0.0, abs_tol=1e-5)

    # Test parallel vectors of different magnitudes
    vec_e = [1.0, 2.0, 3.0]
    vec_f = [2.0, 4.0, 6.0]
    sim_parallel = svc._cosine_similarity(vec_e, vec_f)
    assert math.isclose(sim_parallel, 1.0, rel_tol=1e-5)


# ─── PATTERN CLUSTERING KMEANS TESTS ────────────────────────────────────────


def test_pattern_clustering_kmeans():
    svc = PatternDiscoveryService()

    # Seed 3 distinct vectors grouping into 2 clusters
    vecs = [
        [0.9, 0.9, 0.9, 0.9, 0.1, 0.9],  # Group 1 (Strong trend)
        [0.85, 0.85, 0.85, 0.85, 0.15, 0.85],  # Group 1 (Strong trend)
        [0.1, 0.1, 0.1, 0.1, 0.9, 0.2],  # Group 2 (Failing risk)
    ]
    clusters = svc._deterministic_kmeans(vecs, k=2, max_iter=10)

    assert len(clusters) == 2
    # Verify separation
    all_assigned = sum(len(c) for c in clusters)
    assert all_assigned == 3


# ─── CONFIDENCE CALIBRATION METRICS TESTS ───────────────────────────────────


def test_calibration_metrics_ece_brier(db_session):
    # Seed three winning memories with varying confidence
    mem1 = DecisionMemory(
        decision_id="DEC-100", symbol="BTC", side="LONG",
        decision_dna={"confidence": 90.0},
        outcome={"result": "WIN"}
    )
    mem2 = DecisionMemory(
        decision_id="DEC-101", symbol="BTC", side="LONG",
        decision_dna={"confidence": 80.0},
        outcome={"result": "WIN"}
    )
    mem3 = DecisionMemory(
        decision_id="DEC-102", symbol="BTC", side="LONG",
        decision_dna={"confidence": 20.0},
        outcome={"result": "LOSS"}
    )
    db_session.add(mem1)
    db_session.add(mem2)
    db_session.add(mem3)
    db_session.flush()

    svc = CalibrationService(session_factory=lambda: db_session)
    report = svc.calculate_calibration()

    assert report["total_decisions"] == 3
    # Brier score = ( (0.9-1)^2 + (0.8-1)^2 + (0.2-0)^2 ) / 3
    #             = ( 0.01 + 0.04 + 0.04 ) / 3 = 0.09 / 3 = 0.03
    assert math.isclose(report["brier_score"], 0.03, rel_tol=1e-3)
    assert "ece" in report
    assert "bins" in report


# ─── DECISION DRIFT DETECTION PSI TESTS ─────────────────────────────────────


def test_drift_detection_psi():
    engine = DriftDetectionEngine()

    # Test baseline and target identical
    base = [0.1, 0.3, 0.5, 0.7, 0.9]
    target = [0.1, 0.3, 0.5, 0.7, 0.9]
    psi_val = engine._calculate_psi(base, target)
    assert psi_val < 0.01  # extremely close to 0

    # Test baseline and target highly drifted
    base_shifted = [0.1, 0.1, 0.2, 0.2, 0.3]
    target_shifted = [0.8, 0.8, 0.9, 0.9, 0.9]
    psi_drifted = engine._calculate_psi(base_shifted, target_shifted)
    assert psi_drifted >= 0.25  # Significant drift detected


# ─── PATTERN DISCOVERY FULL PIPELINE TESTS ──────────────────────────────────


def test_discover_patterns_full_pipeline(db_session):
    # Seed memories to trigger actual clustering pipeline in PatternDiscoveryService
    m1 = DecisionMemory(
        decision_id="DEC-201", symbol="BTC", side="LONG",
        decision_dna={"trend_score": 0.8, "volume_score": 0.7, "btc_score": 0.8, "mtf_score": 0.8, "risk_score": 0.2, "confidence": 90.0},
        outcome={"result": "WIN", "pnl": 120.0}
    )
    m2 = DecisionMemory(
        decision_id="DEC-202", symbol="BTC", side="LONG",
        decision_dna={"trend_score": 0.85, "volume_score": 0.65, "btc_score": 0.75, "mtf_score": 0.8, "risk_score": 0.15, "confidence": 85.0},
        outcome={"result": "WIN", "pnl": 140.0}
    )
    m3 = DecisionMemory(
        decision_id="DEC-203", symbol="BTC", side="LONG",
        decision_dna={"trend_score": 0.2, "volume_score": 0.3, "btc_score": 0.2, "mtf_score": 0.3, "risk_score": 0.8, "confidence": 40.0},
        outcome={"result": "LOSS", "pnl": -90.0}
    )
    db_session.add(m1)
    db_session.add(m2)
    db_session.add(m3)
    db_session.flush()

    svc = PatternDiscoveryService(session_factory=lambda: db_session)
    patterns = svc.discover_patterns()

    assert "profitable_patterns" in patterns
    assert "failure_patterns" in patterns
    assert len(patterns["profitable_patterns"]) > 0
    assert len(patterns["failure_patterns"]) > 0

    # Verify the generated structures have correct fields
    win_pat = patterns["profitable_patterns"][0]
    assert "id" in win_pat
    assert "name" in win_pat
    assert "profile" in win_pat
    assert win_pat["win_rate"] == 100.0
    assert win_pat["avg_return"] > 0
