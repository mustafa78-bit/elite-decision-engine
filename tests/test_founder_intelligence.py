from __future__ import annotations

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from database import Signal, Trade, PaperTrade, DecisionExplanation
from services.founder.intelligence import (
    FounderBriefGenerator,
    ExecutiveSummaryEngine,
    OpportunityDetector,
    RiskDetector,
    PortfolioAdvisor,
    WhaleIntelligenceSummary,
    MarketRegimeSummary,
    AICouncilExecutiveReport,
    DailyFounderDigest,
    PriorityRankingEngine,
    ExplainabilityEngine,
    ActionRecommendationEngine,
    FounderDashboardEngine,
)


def _make_signal(db_session, **overrides) -> Signal:
    kwargs = dict(
        symbol="BTCUSDT",
        side="LONG",
        timeframe="1h",
        status="OPEN",
        confidence=85.0,
        score=0.85,
        reason="Bullish breakouts on all intervals"
    )
    kwargs.update(overrides)
    s = Signal(**kwargs)
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def _make_trade(db_session, **overrides) -> Trade:
    kwargs = dict(
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        stop=49000.0,
        tp1=52000.0,
        status="OPEN",
        pnl=0.0
    )
    kwargs.update(overrides)
    t = Trade(**kwargs)
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


def _make_paper_trade(db_session, **overrides) -> PaperTrade:
    kwargs = dict(
        symbol="BTCUSDT",
        side="LONG",
        entry=50000.0,
        quantity=0.1,
        position_id=123,
        status="OPEN",
        pnl=0.0
    )
    kwargs.update(overrides)
    pt = PaperTrade(**kwargs)
    db_session.add(pt)
    db_session.commit()
    db_session.refresh(pt)
    return pt


# ==================================================================
# UNIT TESTS FOR FOUNDER INTELLIGENCE MODULES
# ==================================================================

class TestExecutiveSummaryEngine:
    def test_synthesize_stable(self):
        engine = ExecutiveSummaryEngine()
        market_data = {"price": 60000.0, "regime": "TREND", "btc_health": 0.8}
        signal_stats = {"total": 5, "open": 2}
        trade_stats = {"open": 1, "closed": 4, "total_pnl": 1250.0}

        res = engine.synthesize(market_data, signal_stats, trade_stats)
        assert res["overall_health"] == "STABLE"
        assert "60,000" in res["status_text"]
        assert res["metrics"]["total_pnl"] == 1250.0
        assert "recommended_action" in res

    def test_synthesize_caution_low_btc_health(self):
        engine = ExecutiveSummaryEngine()
        market_data = {"price": 55000.0, "regime": "DOWNTREND", "btc_health": 0.25}
        signal_stats = {"total": 10, "open": 0}
        trade_stats = {"open": 0, "closed": 10, "total_pnl": -500.0}

        res = engine.synthesize(market_data, signal_stats, trade_stats)
        assert res["overall_health"] == "CAUTION"


class TestOpportunityDetector:
    def test_detect_opportunities(self, db_session):
        _make_signal(db_session, symbol="BTCUSDT", score=0.9, status="OPEN")
        _make_signal(db_session, symbol="ETHUSDT", score=0.7, status="OPEN")
        _make_signal(db_session, symbol="SOLUSDT", score=0.85, status="CLOSED")

        detector = OpportunityDetector(lambda: db_session)
        opps = detector.detect_opportunities()
        assert len(opps) == 2
        symbols = [o["symbol"] for o in opps]
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" in symbols
        assert "SOLUSDT" not in symbols
        assert "recommended_action" in opps[0]


class TestRiskDetector:
    def test_evaluate_risks_low(self, db_session):
        detector = RiskDetector(lambda: db_session)
        risks = detector.evaluate_risks(btc_health_score=0.8)
        assert risks["systemic_risk_level"] == "LOW"
        assert "risks" in risks
        assert "market_risk" in risks["risks"]
        assert "portfolio_risk" in risks["risks"]
        assert "liquidity_risk" in risks["risks"]
        assert "whale_risk" in risks["risks"]
        assert "execution_risk" in risks["risks"]
        assert "ai_confidence_risk" in risks["risks"]

        # Verify mitigation suggestions
        for risk_name, r_info in risks["risks"].items():
            assert "mitigation" in r_info
            assert len(r_info["mitigation"]) > 0

    def test_evaluate_risks_high(self, db_session):
        _make_trade(db_session, status="OPEN")
        _make_paper_trade(db_session, status="OPEN")
        _make_paper_trade(db_session, status="OPEN", position_id=124)

        detector = RiskDetector(lambda: db_session)
        risks = detector.evaluate_risks(btc_health_score=0.15)
        assert risks["systemic_risk_level"] == "HIGH"
        assert risks["risks"]["market_risk"]["severity"] == "HIGH"
        assert risks["risks"]["portfolio_risk"]["severity"] == "HIGH"
        assert "recommended_action" in risks


class TestPortfolioAdvisor:
    def test_generate_advice_profitable(self):
        advisor = PortfolioAdvisor()
        advice = advisor.generate_advice({"open": 1, "total_pnl": 1500.0})
        assert advice["recommended_allocation_pct"] == 10.0
        assert "trailing stop" in advice["suggestions"][0].lower()
        assert "recommended_action" in advice

    def test_generate_advice_max_exposure(self):
        advisor = PortfolioAdvisor()
        advice = advisor.generate_advice({"open": 3, "total_pnl": -200.0})
        assert advice["recommended_allocation_pct"] == 0.0
        assert "Refrain from introducing extra exposure" in advice["suggestions"][0]


class TestWhaleIntelligenceSummary:
    def test_generate_summary_no_move(self):
        summary = WhaleIntelligenceSummary()
        res = summary.generate_summary("BTC", volume_score=0.4, volatility_score=0.3)
        assert res["has_large_move"] is False
        assert "No unusual whale movements" in res["summary_text"]
        assert "recommended_action" in res

    def test_generate_summary_with_move(self):
        summary = WhaleIntelligenceSummary()
        res = summary.generate_summary("BTC", volume_score=0.96, volatility_score=0.85)
        assert res["has_large_move"] is True
        assert "Whale activity detected" in res["summary_text"]


class TestMarketRegimeSummary:
    def test_generate_summary_trend(self):
        summary = MarketRegimeSummary()
        res = summary.generate_summary({
            "close": 53000.0,
            "ema20": 49000.0,
            "ema50": 45000.0,
            "ema200": 40000.0,
            "atr": 500.0,
            "rsi": 65.0,
        })
        assert res["regime"] == "TREND"
        assert res["trend"] == "BULLISH"
        assert res["trend_strength"] == "STRONG"
        assert "recommended_action" in res


class TestAICouncilExecutiveReport:
    def test_generate_report(self):
        report_engine = AICouncilExecutiveReport()
        res = report_engine.generate_report("BTC", scores={"score": 0.8})
        assert res["symbol"] == "BTC"
        assert res["consensus_direction"] in ("BULLISH", "BEARISH", "NEUTRAL")
        assert len(res["agent_reports"]) > 0
        assert "recommended_action" in res


class TestDailyFounderDigest:
    def test_generate_digest(self):
        digest = DailyFounderDigest()
        res = digest.generate_digest(
            summary_data={"overall_health": "STABLE"},
            regime_data={"regime": "TREND", "trend": "BULLISH"},
            risk_data={"systemic_risk_level": "LOW"},
            opportunities_data=[{"symbol": "BTC"}]
        )
        assert "Daily OS Digest Update" in res["digest_text"]
        assert "STABLE" in res["digest_text"]
        assert "recommended_action" in res


class TestPriorityRankingEngine:
    def test_rank_items_with_composite_weights(self):
        engine = PriorityRankingEngine()
        items = [
            {
                "symbol": "ETH", "confidence": 50.0, "trust_score": 0.5,
                "historical_accuracy": 0.5, "market_context": 0.5, "risk": 0.8, "time_sensitivity": 0.5
            },
            {
                "symbol": "BTC", "confidence": 95.0, "trust_score": 0.95,
                "historical_accuracy": 0.9, "market_context": 0.9, "risk": 0.1, "time_sensitivity": 0.9
            },
            {
                "symbol": "SOL", "confidence": 80.0, "trust_score": 0.8,
                "historical_accuracy": 0.8, "market_context": 0.8, "risk": 0.3, "time_sensitivity": 0.8
            },
        ]
        ranked = engine.rank_items(items)
        assert ranked[0]["symbol"] == "BTC"
        assert ranked[1]["symbol"] == "SOL"
        assert ranked[2]["symbol"] == "ETH"
        assert "founder_priority_score" in ranked[0]


class TestExplainabilityEngine:
    def test_explain_action_open_long(self):
        engine = ExplainabilityEngine()
        explanation = engine.explain_action("OPEN_LONG", {"technical_score": 0.85, "trend_score": 0.9})
        assert "Opening a Long position is highly justified" in explanation


class TestActionRecommendationEngine:
    def test_generate_recommendations_with_traceability_linkage(self):
        engine = ActionRecommendationEngine()
        opps = [{
            "id": 42,
            "symbol": "BTCUSDT",
            "score": 0.9,
            "confidence": 92.0,
            "trust_score": 0.88,
            "historical_accuracy": 0.85,
            "market_context": 0.80,
            "risk": 0.25,
            "time_sensitivity": 0.92,
            "founder_priority_score": 90.5
        }]
        risks = {"systemic_risk_level": "HIGH", "threats": ["Consolidation bracket break"]}
        whale = {"whale_signals": [{"type": "WHALE_MOVE", "description": "Large move on BTC"}]}

        recs = engine.generate_recommendations(opps, risks, whale)
        assert len(recs) == 2

        # Verify complete schema alignment + traceability metadata
        opp_rec = recs[0]
        assert opp_rec["action"] == "OPEN_LONG"
        assert opp_rec["priority"] == "High"
        assert "why" in opp_rec
        assert opp_rec["confidence"] == 92.0
        assert "evidence" in opp_rec
        assert "related_coins" in opp_rec
        assert "related_whales" in opp_rec
        assert "related_news" in opp_rec
        assert "related_ai_decisions" in opp_rec
        assert "expected_impact" in opp_rec
        assert opp_rec["risk_level"] == "Medium"

        # Verify Traceability / Explainability linkage
        assert "memory_events" in opp_rec
        assert "projection_ids" in opp_rec
        assert "graph_nodes" in opp_rec
        assert "trust_score" in opp_rec
        assert "provenance" in opp_rec

        # Verify Risk Mitigation recommendation
        risk_rec = recs[1]
        assert risk_rec["action"] == "HALT_TRADING"
        assert risk_rec["priority"] == "Critical"
        assert risk_rec["risk_level"] == "Extreme"


class TestFounderDashboardEngine:
    def test_get_dashboard_briefing(self, db_session):
        _make_signal(db_session, score=0.9, status="OPEN")
        _make_trade(db_session, status="OPEN")

        engine = FounderDashboardEngine(lambda: db_session)
        res = engine.get_dashboard_briefing()

        assert "What happened?" in res
        assert "Why does it matter?" in res
        assert "What should I do?" in res
        assert "What can wait?" in res
        assert "complete_brief" in res


# ==================================================================
# INTEGRATION TESTS FOR FOUNDER INTELLIGENCE REST ENDPOINTS
# ==================================================================

class TestFounderEndpoints:
    def test_get_founder_brief_conforms_exactly_to_cto_structure(self, api_client, db_session):
        _make_signal(db_session, score=0.9, status="OPEN")
        _make_trade(db_session, status="OPEN")

        resp = api_client.get("/founder/brief?symbol=BTC")
        assert resp.status_code == 200
        body = resp.json()

        # Verify precise required structure
        required_sections = [
            "Executive Summary",
            "Top Opportunities",
            "Top Risks",
            "Critical AI Decisions",
            "Whale Intelligence",
            "Portfolio Health",
            "Market Regime",
            "Recommended Actions",
            "Confidence Level",
            "Evidence Summary"
        ]
        for section in required_sections:
            assert section in body, f"Section {section} missing from consolidated brief"

            # Verify each section includes recommended action / strategic directives
            if section not in ["Recommended Actions", "Confidence Level", "Evidence Summary"]:
                assert "recommended_action" in body[section], f"Recommended action missing from section {section}"

    def test_get_founder_opportunities_success(self, api_client, db_session):
        _make_signal(db_session, symbol="BTCUSDT", score=0.88, status="OPEN")

        resp = api_client.get("/founder/opportunities")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) >= 1
        assert body[0]["symbol"] == "BTCUSDT"

    def test_get_founder_risks_success(self, api_client, db_session):
        _make_trade(db_session, status="OPEN")

        resp = api_client.get("/founder/risks")
        assert resp.status_code == 200
        body = resp.json()
        assert "systemic_risk_level" in body
        assert "recommended_action" in body
        assert "risks" in body

    def test_get_founder_actions_success(self, api_client, db_session):
        _make_signal(db_session, symbol="BTCUSDT", score=0.95, confidence=91.0, status="OPEN")

        resp = api_client.get("/founder/actions")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) >= 1
        action = body[0]
        assert "action" in action
        assert "priority" in action
        assert "why" in action
        assert "confidence" in action
        assert "evidence" in action
        assert "related_coins" in action
        assert "related_whales" in action
        assert "related_news" in action
        assert "related_ai_decisions" in action
        assert "expected_impact" in action
        assert "risk_level" in action

        # Traceability assertions
        assert "memory_events" in action
        assert "projection_ids" in action
        assert "graph_nodes" in action
        assert "trust_score" in action
        assert "provenance" in action

    def test_get_founder_dashboard_endpoint(self, api_client, db_session):
        _make_signal(db_session, score=0.92, status="OPEN")

        resp = api_client.get("/founder/dashboard")
        assert resp.status_code == 200
        body = resp.json()

        assert "What happened?" in body
        assert "Why does it matter?" in body
        assert "What should I do?" in body
        assert "What can wait?" in body
        assert "complete_brief" in body

    def test_get_founder_history_success(self, api_client, db_session):
        _make_signal(db_session, status="EXECUTED")
        _make_trade(db_session, status="CLOSED")

        resp = api_client.get("/founder/history?limit=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "signals" in body
        assert "trades" in body
        assert "explanations" in body
