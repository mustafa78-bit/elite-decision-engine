from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.main import app
from database import Signal, Trade
from decision.trust import HistoricalOutcome, TrustEngine, TrustScore


class TestTrustEngineUnit:
    def test_default_trust_score(self):
        engine = TrustEngine()
        ts = engine.compute_trust_score(decision_confidence=80.0, evidence_strength=80.0)
        assert isinstance(ts, TrustScore)
        assert 0.0 <= ts.trust_score <= 100.0
        assert ts.historical_accuracy == 75.0  # baseline default

    def test_provenance_replay_validation(self):
        """Replay validation - tests inputs fingerprinting and provenance hash."""
        engine = TrustEngine()
        inputs = {"symbol": "BTC", "confidence": 90.0, "indicators": {"rsi": 65, "macd": "bullish"}}
        prov = engine.generate_provenance("dec-123", "BTC", inputs)

        assert prov.decision_id == "dec-123"
        assert prov.symbol == "BTC"
        assert prov.provenance_hash
        assert prov.inputs_fingerprint

        # Replay validation: regenerating should produce identical fingerprint
        prov2 = engine.generate_provenance("dec-123", "BTC", inputs)
        assert prov2.inputs_fingerprint == prov.inputs_fingerprint

        # Retrieval check
        retrieved = engine.get_provenance("dec-123")
        assert retrieved is not None
        assert retrieved.provenance_hash == prov2.provenance_hash

    def test_confidence_calibration_math(self):
        """Calibration validation - checks Brier score, ECE, reliability and resolution decomposition."""
        engine = TrustEngine()

        # Record mock outcomes to create a distribution
        # High confidence predictions (80%-100% bin -> mapped to 0.9)
        # Expected accuracy = 80%, so 4 CORRECT, 1 INCORRECT
        for i in range(4):
            engine.record_mock_outcome(HistoricalOutcome(f"h-{i}", "BTC", "LONG", 90.0, "CORRECT"))
        engine.record_mock_outcome(HistoricalOutcome("h-4", "BTC", "LONG", 90.0, "INCORRECT"))

        # Low confidence predictions (0%-20% bin -> mapped to 0.1)
        # Expected accuracy = 20%, so 1 CORRECT, 4 INCORRECT
        engine.record_mock_outcome(HistoricalOutcome("l-0", "BTC", "LONG", 10.0, "CORRECT"))
        for i in range(1, 5):
            engine.record_mock_outcome(HistoricalOutcome(f"l-{i}", "BTC", "LONG", 10.0, "INCORRECT"))

        calib = engine.get_calibration_data()
        assert "ece" in calib
        assert "brier_score" in calib
        assert "reliability" in calib
        assert "resolution" in calib
        assert "uncertainty" in calib

        # ECE should be calculated and binned
        assert calib["ece"] >= 0.0
        assert len(calib["points"]) == 5

        # Brier Score checks
        assert calib["brier_score"] > 0.0

    def test_advisor_ratings(self):
        """Advisor Rating System validation."""
        engine = TrustEngine()
        ratings = engine.get_advisor_ratings()
        assert len(ratings) == 6
        for r in ratings:
            assert r.name in ("Technical", "Trend", "Risk", "News", "Whale", "Macro")
            assert 0.0 <= r.reliability_score <= 100.0
            assert 0.0 <= r.accuracy <= 100.0

    def test_voting_analysis_polarization(self):
        """AI Council Voting Analysis validation - polarization and consensus strength."""
        engine = TrustEngine()

        # Mock report structure with split agents
        class MockAgentReport:
            def __init__(self, direction, confidence):
                self.direction = direction
                self.confidence = confidence

        class MockCouncilReport:
            def __init__(self, reports):
                self.agent_reports = reports

        # High Polarization (3 bullish, 3 bearish)
        split_reports = [
            MockAgentReport("BULLISH", 0.8),
            MockAgentReport("BULLISH", 0.7),
            MockAgentReport("BULLISH", 0.9),
            MockAgentReport("BEARISH", 0.8),
            MockAgentReport("BEARISH", 0.9),
            MockAgentReport("BEARISH", 0.7),
        ]
        res_polar = engine.get_voting_analysis(MockCouncilReport(split_reports))
        assert res_polar["polarization"] == 100.0
        assert res_polar["disagreement_level"] == "HIGH"
        assert res_polar["consensus_strength"] == 50.0

        # Unanimous consensus (all bullish)
        unanimous_reports = [MockAgentReport("BULLISH", 0.8)] * 6
        res_unanimous = engine.get_voting_analysis(MockCouncilReport(unanimous_reports))
        assert res_unanimous["polarization"] == 0.0
        assert res_unanimous["disagreement_level"] == "LOW"
        assert res_unanimous["consensus_strength"] == 100.0

    def test_evidence_details_aggregation(self):
        """Evidence Aggregator details validation."""
        engine = TrustEngine()

        class MockEvidenceItem:
            def __init__(self, title, description, engine, category, supports_decision=True):
                self.title = title
                self.description = description
                self.engine = engine
                self.category = category
                self.supports_decision = supports_decision

            def to_dict(self):
                return {"title": self.title, "engine": self.engine}

        class MockEvidenceReport:
            def __init__(self, supporting, contradicting, reasoning=None):
                self.supporting_evidence = supporting
                self.contradicting_evidence = contradicting
                self.reasoning = reasoning or []

        supporting = [
            MockEvidenceItem("Whale movement", "Large inflow detected", "whale", "whale_activity"),
            MockEvidenceItem("Bullish Breakout", "RSI is 65", "scanner", "scanner_momentum"),
        ]
        contradicting = [
            MockEvidenceItem("Risk Limit", "High volatility", "risk_engine", "risk_volatility", False),
        ]

        report = MockEvidenceReport(supporting, contradicting, ["RSI trend confirmed"])
        details = engine.aggregate_evidence_details(report)

        assert details["why"] == ["RSI trend confirmed"]
        assert len(details["whales"]) == 1
        assert len(details["indicators"]) == 1
        assert details["supporting_count"] == 2
        assert details["contradicting_count"] == 1


class TestTrustEngineIntegration:
    def test_historical_db_outcomes(self, db_session):
        """Historical outcomes validation - reads real DB records and updates metrics."""
        engine = TrustEngine(session_factory=lambda: db_session)

        # Create mock Signal and Trade records in db
        sig = Signal(symbol="BTC", side="LONG", confidence=85.0, status="APPROVED")
        db_session.add(sig)
        db_session.commit()

        trade = Trade(signal_id=sig.id, symbol="BTC", side="LONG", status="CLOSED", pnl=150.0)
        db_session.add(trade)
        db_session.commit()

        outcomes = engine.get_historical_outcomes()
        assert len(outcomes) >= 1
        assert outcomes[0].symbol == "BTC"
        assert outcomes[0].actual_outcome == "CORRECT"
        assert outcomes[0].pnl == 150.0

        stats = engine.get_accuracy_stats("BTC")
        assert stats["accuracy"] == 100.0
        assert stats["total_completed"] == 1

    def test_performance_benchmarks(self):
        """Performance benchmarks - ensures Trust & Calibration computations are executed within 50ms."""
        engine = TrustEngine()
        # Seed 1000 outcomes
        for i in range(1000):
            engine.record_mock_outcome(
                HistoricalOutcome(
                    decision_id=f"benchmark-{i}",
                    symbol="BTC",
                    predicted_direction="LONG",
                    predicted_confidence=80.0,
                    actual_outcome="CORRECT" if i % 4 != 0 else "INCORRECT",
                )
            )

        start = time.perf_counter()
        calib = engine.get_calibration_data()
        elapsed = (time.perf_counter() - start) * 1000.0  # ms

        print(f"Calibration calculation for 1000 items elapsed: {elapsed:.2f}ms")
        assert elapsed < 50.0  # Premium execution speed check

        start_trust = time.perf_counter()
        ts = engine.compute_trust_score(85.0, 80.0, "BTC")
        elapsed_trust = (time.perf_counter() - start_trust) * 1000.0  # ms
        print(f"Trust Score computation elapsed: {elapsed_trust:.2f}ms")
        assert elapsed_trust < 20.0


class TestTrustAPI:
    def test_get_trust_summary(self, api_client):
        resp = api_client.get("/trust?symbol=BTC")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "BTC"
        assert "trust_score" in data
        assert "accuracy" in data
        assert "alignment" in data

    def test_get_trust_history(self, api_client):
        resp = api_client.get("/trust/history?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_get_trust_evidence(self, api_client):
        resp = api_client.get("/trust/evidence?decision_id=latest")
        assert resp.status_code == 200
        data = resp.json()
        assert "why" in data
        assert "events" in data
        assert "whales" in data

    def test_get_trust_calibration(self, api_client):
        resp = api_client.get("/trust/calibration")
        assert resp.status_code == 200
        data = resp.json()
        assert "ece" in data
        assert "points" in data

    def test_get_trust_advisors(self, api_client):
        resp = api_client.get("/trust/advisors")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 6
