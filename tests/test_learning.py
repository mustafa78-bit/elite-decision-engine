from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api.main import app
from database import (
    Signal,
    Trade,
    PaperTrade,
    LearningOutcome,
    LearningPattern,
    AdvisorWeightHistory,
    AdvisorLearningHistory,
    LearningHistoryEntry,
    get_session,
)
from decision.learning import (
    OutcomeAnalyzer,
    PatternLearningEngine,
    HistoricalSimilarityEngine,
    StrategyPerformanceAnalyzer,
    AdvisorLearningModule,
    ReinforcementWeightUpdater,
    LearningReplayEngine,
    LearningTimeline,
    LearningDashboardEngine,
)




class TestOutcomeAnalyzer:
    def test_extract_features(self):
        analyzer = OutcomeAnalyzer()
        signal = Signal(
            score=85.0,
            confidence=90.0,
            market_health=75.0,
            btc_health=80.0,
            volume_score=70.0,
            funding_score=60.0,
            oi_score=65.0,
            cvd_score=50.0,
            trend_score=85.0,
            risk_score=20.0,
        )
        features = analyzer.extract_features(signal)
        assert features["score"] == 85.0
        assert features["confidence"] == 90.0
        assert features["risk_score"] == 20.0

    def test_analyze_signal_outcome_with_trade(self, db_session):
        # Create a Signal
        signal = Signal(
            symbol="BTC",
            side="LONG",
            score=80.0,
            confidence=85.0,
            market_health=70.0,
            btc_health=75.0,
            volume_score=80.0,
            funding_score=55.0,
            oi_score=60.0,
            cvd_score=50.0,
            trend_score=80.0,
            risk_score=30.0,
            status="CLOSED",
        )
        db_session.add(signal)
        db_session.commit()

        # Create matching Trade
        trade = Trade(
            signal_id=signal.id,
            symbol="BTC",
            side="LONG",
            entry=50000.0,
            exit_price=52000.0,
            pnl=2000.0,
            status="CLOSED",
            created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            closed_at=datetime.now(timezone.utc)
        )
        db_session.add(trade)
        db_session.commit()

        analyzer = OutcomeAnalyzer()
        outcome = analyzer.analyze_signal_outcome(db_session, signal.id)

        assert outcome is not None
        assert outcome.decision_id == f"sig-{signal.id}"
        assert outcome.symbol == "BTC"
        assert outcome.final_outcome == "CORRECT"
        assert outcome.pnl == 2000.0
        assert outcome.roi > 0
        assert outcome.time_horizon == pytest.approx(2.0, abs=0.1)
        assert outcome.confidence_at_decision == 85.0
        assert outcome.success_score > 50.0
        assert outcome.market_regime in ("NORMAL", "BULL_TREND", "STRONG_BULL")


class TestPatternLearningEngine:
    def test_pattern_detection_and_storage(self, db_session):
        # Clear existing
        db_session.query(LearningOutcome).delete()
        db_session.query(LearningPattern).delete()
        db_session.commit()

        # Seed outcomes representing success/failure patterns
        # 3 high trend & volume wins
        for i in range(3):
            outcome = LearningOutcome(
                decision_id=f"win-{i}",
                symbol="BTC",
                strategy="CONFLUENCE_TREND",
                final_outcome="CORRECT",
                pnl=500.0,
                roi=5.0,
                replay_id="TEST_REPLAY",
                features={"trend_score": 75.0, "volume_score": 80.0, "btc_health": 50.0, "confidence_at_decision": 70.0}
            )
            db_session.add(outcome)

        # 2 weak market losses
        for i in range(2):
            outcome = LearningOutcome(
                decision_id=f"loss-{i}",
                symbol="BTC",
                strategy="CONFLUENCE_TREND",
                final_outcome="INCORRECT",
                pnl=-300.0,
                roi=-3.0,
                replay_id="TEST_REPLAY",
                features={"risk_score": 65.0, "btc_health": 30.0}
            )
            db_session.add(outcome)

        db_session.commit()

        engine = PatternLearningEngine()
        result = engine.generate_and_store_patterns(db_session, replay_id="TEST_REPLAY")

        success_pats = result["success_patterns"]
        failure_pats = result["failure_patterns"]

        assert len(success_pats) >= 1
        assert any(p["name"] == "High Trend & High Volume Alignment" for p in success_pats)
        assert len(failure_pats) >= 1
        assert any(p["name"] == "High Risk Exposure in Weak BTC Environment" for p in failure_pats)

        # Verify database storage and supporting evidence lists
        stored = db_session.query(LearningPattern).all()
        assert len(stored) >= 2
        for p in stored:
            assert len(p.supporting_decisions) >= 2
            assert p.historical_precision > 0.0


class TestHistoricalSimilarityEngine:
    def test_similarity_math(self):
        engine = HistoricalSimilarityEngine()
        f1 = {"trend_score": 80.0, "volume_score": 70.0, "btc_health": 60.0}
        f2 = {"trend_score": 80.0, "volume_score": 70.0, "btc_health": 60.0}
        assert engine.calculate_similarity(f1, f2) == 100.0

        f3 = {"trend_score": 10.0, "volume_score": 10.0, "btc_health": 10.0}
        assert engine.calculate_similarity(f1, f3) < 80.0

    def test_find_similar_cases(self, db_session):
        db_session.query(LearningOutcome).delete()
        db_session.commit()

        # Seed outcomes
        o1 = LearningOutcome(
            decision_id="dec-1",
            symbol="ETH",
            final_outcome="CORRECT",
            pnl=100.0,
            replay_id="INITIAL",
            features={"trend_score": 80.0, "volume_score": 70.0, "btc_health": 60.0}
        )
        o2 = LearningOutcome(
            decision_id="dec-2",
            symbol="SOL",
            final_outcome="INCORRECT",
            pnl=-50.0,
            replay_id="INITIAL",
            features={"trend_score": 20.0, "volume_score": 30.0, "btc_health": 40.0}
        )
        db_session.add(o1)
        db_session.add(o2)
        db_session.commit()

        engine = HistoricalSimilarityEngine()
        similar = engine.find_similar_cases(db_session, {"trend_score": 82.0, "volume_score": 68.0, "btc_health": 62.0})

        assert len(similar) >= 1
        assert similar[0]["decision_id"] == "dec-1"
        assert similar[0]["similarity"] > 90.0


class TestStrategyPerformanceAnalyzer:
    def test_strategy_performance_calculations(self, db_session):
        db_session.query(LearningOutcome).delete()
        db_session.commit()

        # Seed 3 CORRECT and 1 INCORRECT outcomes
        for i in range(3):
            o = LearningOutcome(
                decision_id=f"perf-win-{i}",
                symbol="BTC",
                final_outcome="CORRECT",
                pnl=300.0,
                replay_id="INITIAL",
                features={}
            )
            db_session.add(o)

        o_loss = LearningOutcome(
            decision_id="perf-loss-1",
            symbol="BTC",
            final_outcome="INCORRECT",
            pnl=-100.0,
            replay_id="INITIAL",
            features={}
        )
        db_session.add(o_loss)
        db_session.commit()

        analyzer = StrategyPerformanceAnalyzer()
        perf = analyzer.analyze_performance(db_session, replay_id="INITIAL")

        assert perf["total_completed"] == 4
        assert perf["win_rate"] == 75.0
        assert perf["total_pnl"] == 800.0
        assert perf["profit_factor"] == 9.0
        assert perf["expectancy"] > 0.0


class TestAdvisorLearningModule:
    def test_weight_evolution_and_independent_metrics(self, db_session):
        db_session.query(AdvisorWeightHistory).delete()
        db_session.query(AdvisorLearningHistory).delete()
        db_session.commit()

        outcome = LearningOutcome(
            decision_id="adv-sig-1",
            symbol="BTC",
            final_outcome="CORRECT",
            pnl=500.0,
            roi=5.0,
            replay_id="INITIAL",
            confidence_at_decision=80.0,
            features={"trend_score": 80.0, "volume_score": 80.0, "btc_health": 70.0}
        )
        db_session.add(outcome)
        db_session.commit()

        updater = ReinforcementWeightUpdater()
        updates = updater.apply_reinforcement(db_session, outcome)

        assert len(updates) > 0

        # Verify weight evolution is appended and tracked independently
        hist = db_session.query(AdvisorLearningHistory).filter(
            AdvisorLearningHistory.advisor_name == "Trend"
        ).order_by(AdvisorLearningHistory.created_at.desc()).first()

        assert hist is not None
        assert hist.win_rate > 0.0
        assert hist.precision > 0.0
        assert len(hist.learning_timeline) > 0


class TestLearningReplayEngine:
    def test_deterministic_replay_and_modes(self, db_session):
        replay_engine = LearningReplayEngine()

        # Seed raw trade/signals for replay reconstruction
        signal = Signal(
            symbol="BTC",
            side="LONG",
            score=85.0,
            confidence=90.0,
            market_health=80.0,
            btc_health=85.0,
            volume_score=80.0,
            funding_score=60.0,
            oi_score=70.0,
            cvd_score=50.0,
            trend_score=85.0,
            risk_score=15.0,
            status="CLOSED",
        )
        db_session.add(signal)
        db_session.commit()

        trade = Trade(
            signal_id=signal.id,
            symbol="BTC",
            side="LONG",
            entry=50000.0,
            exit_price=52500.0,
            pnl=2500.0,
            status="CLOSED",
            created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            closed_at=datetime.now(timezone.utc)
        )
        db_session.add(trade)
        db_session.commit()

        # Run Replay from scratch
        result1 = replay_engine.replay_from_scratch(db_session, replay_id="REPLAY_V1")
        assert result1["status"] == "SUCCESS"
        assert result1["outcomes_processed"] >= 1

        # Run Replay again - should be fully deterministic and produce identical metrics
        result2 = replay_engine.replay_from_scratch(db_session, replay_id="REPLAY_V1")
        assert result2["outcomes_processed"] == result1["outcomes_processed"]
        assert result2["performance"]["win_rate"] == result1["performance"]["win_rate"]

        # Run Incremental Replay
        inc_result = replay_engine.incremental_replay(db_session, replay_id="REPLAY_V1")
        assert inc_result["status"] == "SUCCESS"

        # Version Comparison
        comp = replay_engine.version_comparison(db_session, "REPLAY_V1", "REPLAY_V1")
        assert comp["comparison"]["win_rate_diff"] == 0.0


class TestLearningAPI:
    def test_get_learning_summary(self, api_client):
        resp = api_client.get("/learning?replay_id=INITIAL")
        assert resp.status_code == 200
        data = resp.json()
        assert "advisor_weights" in data
        assert "performance" in data

    def test_get_learning_history(self, api_client):
        resp = api_client.get("/learning/history?limit=10")
        assert resp.status_code == 200
        assert "history" in resp.json()

    def test_get_learning_patterns(self, api_client):
        resp = api_client.get("/learning/patterns")
        assert resp.status_code == 200
        assert "patterns" in resp.json()

    def test_get_learning_outcomes(self, api_client):
        resp = api_client.get("/learning/outcomes?symbol=BTC")
        assert resp.status_code == 200
        assert "outcomes" in resp.json()

    def test_get_advisor_learning(self, api_client):
        resp = api_client.get("/learning/advisors?advisor_name=Trend")
        assert resp.status_code == 200
        assert "advisors" in resp.json()

    def test_trigger_learning_replay(self, api_client):
        resp = api_client.post("/learning/replay?mode=FULL&replay_id=API_REPLAY")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert data["replay_id"] == "API_REPLAY"

    def test_get_learning_dashboard(self, api_client):
        resp = api_client.get("/learning/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "insights" in data
        assert "metrics" in data
        assert "patterns" in data
