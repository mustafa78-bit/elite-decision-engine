"""Unit and integration tests for the Discovery Engine.

Covers detectors, correlation, multi-faceted ranking, replay comparison, snapshots,
and E2E REST API endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from database import Signal, Trade, JournalEntry, get_session
from services.discovery.detectors import (
    DiscoveryOpportunity,
    EmergingCoinDetector,
    WhaleAccumulationScanner,
    NarrativeDiscovery,
    LiquidityShiftDetector,
    SmartMoneyDetector,
    RegimeChangeDetector,
    EarlyMomentumDetector,
)
from services.discovery.ranking import (
    CrossMarketCorrelationEngine,
    OpportunityRankingEngine,
)
from services.discovery.replay import DiscoveryReplayEngine


@pytest.fixture
def test_data_setup(db_session):
    """Sets up mock signal, trade, and journal database records for discovery testing."""
    # Signals
    s1 = Signal(symbol="BTCUSDT", score=0.88, confidence=0.85, status="PENDING")
    s2 = Signal(symbol="WUSDT", score=0.92, confidence=0.45, status="PENDING") # AI Sector, low confidence (EMD)
    s3 = Signal(symbol="SOLUSDT", score=0.82, confidence=0.75, status="PENDING")
    db_session.add_all([s1, s2, s3])

    # Trades
    t1 = Trade(symbol="ETHUSDT", side="LONG", entry=3200.0, status="OPEN", pnl=620.0) # Active, positive PnL (WAS / LSD)
    t2 = Trade(symbol="SOLUSDT", side="LONG", entry=140.0, status="CLOSED", pnl=1200.0) # Closed, high PnL (WAS)
    db_session.add_all([t1, t2])

    # Journal entry (successful WIN profile for SmartMoney)
    j1 = JournalEntry(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=64000.0,
        exit_price=68000.0,
        result="WIN",
        pnl=4000.0,
        exit_reason="Take Profit target reached",
    )
    db_session.add(j1)
    db_session.commit()


def test_detectors_correctness(db_session, test_data_setup):
    """Verifies that all 7 detectors properly process data and adhere to canonical non-speculative schemas."""
    # 1. Emerging Coin Detector
    ecd = EmergingCoinDetector()
    ecd_ops = ecd.detect(db_session)
    assert len(ecd_ops) > 0
    for op in ecd_ops:
        assert op.category in ["AI", "L1/L2"]
        assert op.estimated_risk == "MEDIUM"

    # 2. Whale Accumulation Scanner
    was = WhaleAccumulationScanner()
    was_ops = was.detect(db_session)
    assert len(was_ops) > 0
    for op in was_ops:
        assert "Whale" in op.category
        assert op.estimated_impact == "EXTREME"

    # 3. Narrative Discovery
    nd = NarrativeDiscovery()
    nd_ops = nd.detect(db_session)
    assert len(nd_ops) > 0
    for op in nd_ops:
        # Category contains thematic description
        assert len(op.category) > 0

    # 4. Liquidity Shift Detector
    lsd = LiquidityShiftDetector()
    lsd_ops = lsd.detect(db_session)
    assert len(lsd_ops) > 0
    assert lsd_ops[0].category == "Liquidity Shifts"

    # 5. Smart Money Detector
    smd = SmartMoneyDetector()
    smd_ops = smd.detect(db_session)
    assert len(smd_ops) > 0
    assert smd_ops[0].category == "Smart Money"

    # 6. Regime Change Detector
    rcd = RegimeChangeDetector()
    rcd_ops = rcd.detect(db_session)
    assert len(rcd_ops) > 0
    assert rcd_ops[0].category == "Macro Regimes"

    # 7. Early Momentum Detector
    emd = EarlyMomentumDetector()
    emd_ops = emd.detect(db_session)
    assert len(emd_ops) > 0
    assert emd_ops[0].category == "Early Momentum"


def test_ranking_stability_and_explainability(db_session, test_data_setup):
    """Verifies ranking formula, Multi-faceted composite sorting, and metadata explainability."""
    corr_engine = CrossMarketCorrelationEngine()
    ranker = OpportunityRankingEngine(corr_engine)

    ecd_ops = EmergingCoinDetector().detect(db_session)
    ranked = ranker.rank(ecd_ops, market_regime="BULLISH", learning_feedback=1.1, calibration_adjustment=5.0)

    assert len(ranked) == len(ecd_ops)
    # Ensure descending sort
    for i in range(len(ranked) - 1):
        assert ranked[i].founder_priority >= ranked[i + 1].founder_priority

    # Ensure metadata contains ranking provenance (transparency)
    first = ranked[0]
    provenance = first.metadata["ranking_provenance"]
    assert "base_score" in provenance
    assert provenance["learning_feedback"] == 1.1
    assert provenance["calibration_adjustment"] == 5.0


def test_cross_market_correlation_generics(db_session, test_data_setup):
    """Verifies generic asset class correlation calculates without hardcoded errors."""
    engine = CrossMarketCorrelationEngine()
    op = EmergingCoinDetector().detect(db_session)[0]

    # Test distinct asset classes passing custom non-identical anchor_asset
    c_crypto = engine.calculate_correlation(op, anchor_asset="ETHUSDT", asset_class="Crypto")
    c_equities = engine.calculate_correlation(op, anchor_asset="ETHUSDT", asset_class="Equities")
    c_macro = engine.calculate_correlation(op, anchor_asset="ETHUSDT", asset_class="Macro Indicators")

    assert -1.0 <= c_crypto <= 1.0
    assert -1.0 <= c_equities <= 1.0
    assert -1.0 <= c_macro <= 1.0
    assert c_macro < c_equities # Macro indicators have lower/negative default correlation value


def test_replay_determinism_comparison_and_snapshots(db_session, test_data_setup):
    """Tests that discovery replay is deterministic, duplicate-free, and handles comparison metrics."""
    replay_engine = DiscoveryReplayEngine()

    # Snapshot A
    res_a = replay_engine.replay_from_state(db_session, replay_id="snapshot_a")
    # Snapshot B (Identical database state)
    res_b = replay_engine.replay_from_state(db_session, replay_id="snapshot_b")

    assert res_a["total_reconstructed"] == res_b["total_reconstructed"]
    assert res_a["benchmarks"]["precision"] == res_b["benchmarks"]["precision"]

    # Compare replays
    comparison = replay_engine.compare_replays(res_a, res_b)
    assert comparison["identical"] is True
    assert comparison["consistency_score"] == 1.0
    assert comparison["added_count"] == 0
    assert comparison["removed_count"] == 0


def test_e2e_discovery_api(api_client, db_session, test_data_setup):
    """Validates the entire exposed REST routes under the /discovery prefix."""
    # 1. Root diagnostic status
    resp = api_client.get("/discovery")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert "Emerging Coin Detector" in body["detectors_loaded"]

    # 2. Opportunities ranked
    resp = api_client.get("/discovery/opportunities")
    assert resp.status_code == 200
    ops = resp.json()
    assert len(ops) > 0
    # Every opportunity adheres fully to specified attributes
    first = ops[0]
    assert "opportunity_id" in first
    assert "category" in first
    assert "founder_priority_score" in first
    assert "confidence" in first
    assert "why" in first
    assert "supporting_evidence" in first

    # 3. Filtering options
    resp = api_client.get("/discovery/opportunities?min_confidence=0.80")
    assert resp.status_code == 200
    filtered_ops = resp.json()
    for o in filtered_ops:
        assert o["confidence"] >= 0.80

    # 4. Emerging Coins
    resp = api_client.get("/discovery/emerging")
    assert resp.status_code == 200
    emerging = resp.json()
    assert len(emerging) > 0

    # 5. Narratives
    resp = api_client.get("/discovery/narratives")
    assert resp.status_code == 200

    # 6. Replay trigger
    resp = api_client.post("/discovery/replay")
    assert resp.status_code == 200
    replay_body = resp.json()
    assert replay_body["replayed_at"] == "canonical_replay_state"

    # 7. Complete Dashboard Workspace for Founder Intelligence
    resp = api_client.get("/discovery/dashboard")
    assert resp.status_code == 200
    dashboard = resp.json()
    assert dashboard["workspace_id"] == "founder_intelligence_discovery_dashboard"
    assert "benchmarks" in dashboard
    assert "visualizations" in dashboard
    assert "radar_distribution" in dashboard["visualizations"]
