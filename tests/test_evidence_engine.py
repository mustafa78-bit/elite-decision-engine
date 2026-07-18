from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import pytest

from decision.evidence import (
    EvidenceEngine,
    EvidenceItem,
    EvidenceReport,
    EvidenceBuilder,
    SourceTrace,
    EvidenceCategory,
    calculate_confidence,
    calculate_evidence_strength,
    calculate_explainability,
    calculate_decision_quality,
    get_category,
    REGISTRY,
    ENGINE_VERSIONS,
    get_version,
    Conflict,
    detect_conflicts,
    build_timeline,
    timeline_summary,
)
from decision.evidence.parser import (
    parse_decision_result,
    parse_risk_decision,
    parse_scanner_opportunity,
    parse_council_report,
    parse_portfolio_summary,
    parse_market_regime,
    parse_whale_result,
    parse_explain_result,
)
from decision.evidence.confidence import SEVERITY_WEIGHTS, SOURCE_WEIGHTS, STRENGTH_WEIGHTS


class TestSourceTrace:
    def test_default_module_version_from_engine(self):
        st = SourceTrace(origin="BTC", engine="scanner")
        assert st.module_version == "2.4"

    def test_custom_module_version(self):
        st = SourceTrace(origin="ETH", engine="custom", module_version="1.0")
        assert st.module_version == "1.0"

    def test_decision_id_generated(self):
        st = SourceTrace(origin="XRP", engine="scanner")
        assert st.decision_id
        assert len(st.decision_id) == 12

    def test_to_dict(self):
        st = SourceTrace(origin="XRP", engine="scanner", module_version="2.0")
        d = st.to_dict()
        assert d["origin"] == "XRP"
        assert d["engine"] == "scanner"
        assert d["module_version"] == "2.0"
        assert "decision_id" in d

    def test_get_version_known(self):
        assert get_version("scanner") == "2.4"

    def test_get_version_unknown(self):
        assert get_version("nonexistent") == "0.0"

    def test_all_versions_defined(self):
        expected = ("scanner", "risk_engine", "council", "portfolio", "market_regime", "whale", "explain", "decision", "evidence_engine")
        for e in expected:
            assert e in ENGINE_VERSIONS


class TestEvidenceItem:
    def test_minimal_creation(self):
        item = EvidenceItem()
        assert item.id
        assert len(item.id) == 12

    def test_full_creation(self):
        src = SourceTrace(origin="BTC", engine="scanner")
        item = EvidenceItem(
            title="Test",
            description="Desc",
            engine="scanner",
            category="momentum",
            severity="HIGH",
            confidence=0.85,
            weight=1.0,
            source=src,
        )
        assert item.title == "Test"
        assert item.confidence == 0.85
        assert item.weight == 1.0

    def test_version_from_source(self):
        src = SourceTrace(origin="O", engine="scanner")
        item = EvidenceItem(engine="scanner", category="c", source=src)
        assert item.version == "2.4"

    def test_to_dict(self):
        item = EvidenceItem(title="T", description="D", engine="e", category="c")
        d = item.to_dict()
        assert d["title"] == "T"
        assert d["description"] == "D"
        assert d["engine"] == "e"
        assert "weight" in d

    def test_to_dict_with_source(self):
        src = SourceTrace(origin="O", engine="e", module_version="1.0")
        item = EvidenceItem(title="T", description="D", engine="e", category="c", source=src)
        d = item.to_dict()
        assert d["source"]["origin"] == "O"
        assert "version" in d

    def test_frozen(self):
        item = EvidenceItem(title="T", description="D", engine="e", category="c")
        with pytest.raises(Exception):
            item.title = "changed"


class TestEvidenceReport:
    def test_minimal_creation(self):
        report = EvidenceReport()
        assert report.decision_id
        assert report.decision_confidence == 0.0
        assert report.evidence_strength == 0.0
        assert report.explainability == 0.0

    def test_frozen(self):
        report = EvidenceReport()
        with pytest.raises(Exception):
            report.recommendation = "BUY"

    def test_to_dict_structure(self):
        item = EvidenceItem(title="S", description="D", engine="e", category="c")
        src = SourceTrace(origin="O", engine="e")
        report = EvidenceReport(
            recommendation="BUY",
            decision_confidence=75.5,
            evidence_strength=80.0,
            explainability=90.0,
            decision_quality="MODERATE",
            summary="Test",
            supporting_evidence=[item],
            timeline=[item],
            sources=[src],
        )
        d = report.to_dict()
        assert d["recommendation"] == "BUY"
        assert d["decision_confidence"] == 75.5
        assert d["evidence_strength"] == 80.0
        assert d["explainability"] == 90.0
        assert d["decision_quality"] == "MODERATE"
        assert len(d["supporting_evidence"]) == 1
        assert len(d["timeline"]) == 1
        assert len(d["sources"]) == 1

    def test_to_dict_empty(self):
        report = EvidenceReport()
        d = report.to_dict()
        assert d["supporting_evidence"] == []
        assert d["contradicting_evidence"] == []
        assert d["timeline"] == []

    def test_created_at_default(self):
        report = EvidenceReport()
        assert report.created_at


class DictObj:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getattr__(self, name: str) -> Any:
        return self._data.get(name)


class TestParseDecisionResult:
    def test_parses_decision(self):
        result = DictObj({"decision": "BUY", "confidence": 85.0, "score": 0.75, "risk_score": 0.2, "reasons": ["Trend bullish"], "warnings": []})
        items = parse_decision_result(result, "BTC")
        assert len(items) >= 1
        assert items[0].engine == "decision"

    def test_parses_warnings_as_contradicting(self):
        result = DictObj({"decision": "BUY", "confidence": 85.0, "score": 0.75, "risk_score": 0.2, "reasons": [], "warnings": ["High volatility"]})
        items = parse_decision_result(result)
        warnings = [i for i in items if not i.supports_decision]
        assert len(warnings) > 0


class TestParseRiskDecision:
    def test_rejected_trade(self):
        result = DictObj({"allowed": False, "reason": "Max open trades exceeded", "checks": ()})
        items = parse_risk_decision(result, "BTC")
        assert len(items) >= 1
        assert not items[0].supports_decision

    def test_allowed_no_items(self):
        result = DictObj({"allowed": True, "reason": "", "checks": ()})
        items = parse_risk_decision(result)
        assert len(items) == 0

    def test_dict_checks(self):
        result = DictObj({"allowed": False, "reason": "Risk", "checks": {"volatility": 0.8}})
        items = parse_risk_decision(result, "ETH")
        assert len(items) >= 1


class TestParseScannerOpportunity:
    def test_parses_opportunity(self):
        result = DictObj({"symbol": "BTC", "side": "LONG", "score": 0.85, "confidence": 90.0, "strategy": "momentum", "reason": "Strong breakout", "signals": ["RSI > 70"]})
        items = parse_scanner_opportunity(result)
        assert len(items) >= 1
        assert items[0].supports_decision


class TestParseCouncilReport:
    def test_parses_consensus(self):
        result = DictObj({"symbol": "BTC", "consensus_direction": "BULLISH", "consensus_score": 85.0, "agreement_level": "strong", "sources_agreeing": 4, "sources_disagreeing": 1, "agent_reports": []})
        items = parse_council_report(result)
        assert len(items) >= 1
        assert items[0].engine == "council"

    def test_parses_agent_reports(self):
        agent = DictObj({"agent_name": "TrendAgent", "direction": "BULLISH", "confidence": 85.0, "reasoning": ["Trend is up"]})
        result = DictObj({"symbol": "BTC", "consensus_direction": "BULLISH", "consensus_score": 85.0, "agreement_level": "strong", "sources_agreeing": 4, "sources_disagreeing": 1, "agent_reports": [agent]})
        items = parse_council_report(result)
        assert len(items) >= 2


class TestParsePortfolioSummary:
    def test_drawdown_contradicts(self):
        result = DictObj({"current_exposure": 5000, "max_exposure": 10000, "open_pnl": -5000, "win_rate": 55.0})
        items = parse_portfolio_summary(result)
        contradicting = [i for i in items if not i.supports_decision]
        assert len(contradicting) >= 1


class TestParseMarketRegime:
    def test_bullish_regime_supports(self):
        result = {"regime": "TREND", "trend": "BULLISH", "trend_strength": "STRONG", "volatility_class": "NORMAL", "score": 0.85}
        items = parse_market_regime(result)
        supporting = [i for i in items if i.supports_decision]
        assert len(supporting) >= 1

    def test_high_volatility_adds_contradicting(self):
        result = {"regime": "RANGE", "trend": "NEUTRAL", "trend_strength": "WEAK", "volatility_class": "EXTREME", "score": 0.5}
        items = parse_market_regime(result)
        contradicting = [i for i in items if not i.supports_decision]
        assert len(contradicting) >= 1


class TestParseWhaleResult:
    def test_parses_whale_list(self):
        whales = [
            {"symbol": "BTC", "type": "WHALE_MOVE", "severity": "high", "description": "Large inflow", "confidence": 0.85},
            {"symbol": "ETH", "type": "HIGH_VOLUME", "severity": "medium", "description": "Volume spike", "confidence": 0.7},
        ]
        items = parse_whale_result(whales)
        assert len(items) == 2

    def test_empty_list(self):
        items = parse_whale_result([])
        assert len(items) == 0


class TestParseExplainResult:
    def test_parses_explain(self):
        result = DictObj({"decision": "BUY", "confidence": 80.0, "reasons": ["Strong trend"], "warnings": [], "supporting_signals": ["RSI bullish"], "risk_notes": [], "summary": "Overall bullish"})
        items = parse_explain_result(result)
        assert len(items) >= 2

    def test_warnings_contradict(self):
        result = DictObj({"decision": "BUY", "confidence": 80.0, "reasons": [], "warnings": ["High risk"], "supporting_signals": [], "risk_notes": ["Volatility high"], "summary": ""})
        items = parse_explain_result(result)
        contradicting = [i for i in items if not i.supports_decision]
        assert len(contradicting) >= 1


class TestConfidence:
    def test_no_evidence_zero(self):
        assert calculate_confidence([], []) == 0.0

    def test_only_supporting_high(self):
        item = EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)
        c = calculate_confidence([item], [])
        assert c > 50.0

    def test_contradicting_reduces(self):
        sup = EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)
        con = EvidenceItem(engine="risk_engine", severity="CRITICAL", confidence=0.95, supports_decision=False)
        c_with = calculate_confidence([sup], [con])
        c_without = calculate_confidence([sup], [])
        assert c_with < c_without

    def test_clamps_zero_to_hundred(self):
        item = EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)
        c = calculate_confidence([item, item, item], [item])
        assert 0.0 <= c <= 100.0

    def test_weight_affects_confidence(self):
        con = EvidenceItem(engine="risk_engine", severity="HIGH", confidence=0.8, supports_decision=False)
        light = EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, weight=0.5, supports_decision=True)
        heavy = EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, weight=2.0, supports_decision=True)
        c_light = calculate_confidence([light], [con])
        c_heavy = calculate_confidence([heavy], [con])
        assert c_heavy > c_light


class TestEvidenceStrength:
    def test_no_evidence_zero(self):
        assert calculate_evidence_strength([]) == 0.0

    def test_strength_from_supporting(self):
        item = EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)
        s = calculate_evidence_strength([item])
        assert s > 0.0
        assert s <= 100.0

    def test_strength_higher_with_better_evidence(self):
        weak = EvidenceItem(engine="whale", severity="LOW", confidence=0.3, supports_decision=True)
        strong = EvidenceItem(engine="council", severity="HIGH", confidence=0.95, supports_decision=True)
        s_weak = calculate_evidence_strength([weak])
        s_strong = calculate_evidence_strength([strong])
        assert s_strong > s_weak

    def test_strength_with_multiple(self):
        items = [
            EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True),
            EvidenceItem(engine="council", severity="HIGH", confidence=0.85, supports_decision=True),
            EvidenceItem(engine="market_regime", severity="MEDIUM", confidence=0.8, supports_decision=True),
        ]
        s = calculate_evidence_strength(items)
        assert s > 50.0


class TestExplainability:
    def test_no_evidence_zero(self):
        assert calculate_explainability([], [], [], 0) == 0.0

    def test_explainability_with_evidence(self):
        item = EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)
        src = SourceTrace(origin="BTC", engine="scanner")
        e = calculate_explainability([item], [], [src], 1)
        assert e > 0.0
        assert e <= 100.0

    def test_contradicting_boosts_explainability(self):
        sup = EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)
        con = EvidenceItem(engine="risk_engine", severity="HIGH", confidence=0.8, supports_decision=False)
        src = SourceTrace(origin="BTC", engine="scanner")
        without = calculate_explainability([sup], [], [src], 1)
        with_contra = calculate_explainability([sup], [con], [src], 1)
        assert with_contra > without


class TestDecisionQuality:
    def test_strong(self):
        assert calculate_decision_quality(85.0, 88.0, 90.0, 3, 0) == "STRONG"

    def test_moderate(self):
        assert calculate_decision_quality(65.0, 60.0, 70.0, 1, 0) == "MODERATE"

    def test_weak(self):
        assert calculate_decision_quality(45.0, 40.0, 50.0, 1, 1) == "WEAK"

    def test_insufficient(self):
        assert calculate_decision_quality(20.0, 10.0, 15.0, 0, 0) == "INSUFFICIENT"

    def test_strong_requires_no_contradict(self):
        assert calculate_decision_quality(90.0, 90.0, 90.0, 2, 1) != "STRONG"


class TestEvidenceRegistry:
    def test_registry_has_categories(self):
        assert "council_consensus" in REGISTRY
        assert "risk_rejection" in REGISTRY
        assert len(REGISTRY) >= 12

    def test_get_category_known(self):
        cat = get_category("scanner_momentum")
        assert cat.severity == "HIGH"

    def test_get_category_unknown_returns_default(self):
        cat = get_category("nonexistent")
        assert cat.name == "nonexistent"
        assert cat.category == "general"


class TestConflictDetector:
    def test_no_conflicts_empty(self):
        assert detect_conflicts([], []) == []

    def test_no_conflicts_all_support(self):
        sup = [EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)]
        con = []
        assert detect_conflicts(sup, con) == []

    def test_risk_vs_scanner_conflict(self):
        sup = [EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)]
        con = [EvidenceItem(engine="risk_engine", severity="HIGH", confidence=0.8, supports_decision=False)]
        conflicts = detect_conflicts(sup, con)
        assert len(conflicts) >= 1
        assert "risk_engine" in conflicts[0].engine_a or "risk_engine" in conflicts[0].engine_b

    def test_conflict_to_dict(self):
        c = Conflict(pair="Risk vs Scanner", severity="HIGH", description="Test", engine_a="risk_engine", engine_b="scanner")
        d = c.to_dict()
        assert d["pair"] == "Risk vs Scanner"
        assert d["severity"] == "HIGH"

    def test_council_vs_scanner_conflict(self):
        sup = [EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)]
        con = [EvidenceItem(engine="council", severity="MEDIUM", confidence=0.7, supports_decision=False)]
        conflicts = detect_conflicts(sup, con)
        assert len(conflicts) >= 1
        assert "council" in conflicts[0].description

    def test_risk_scanner_escalation(self):
        sup = [EvidenceItem(engine="scanner", severity="HIGH", confidence=0.9, supports_decision=True)]
        con = [EvidenceItem(engine="risk_engine", severity="MEDIUM", confidence=0.8, supports_decision=False)]
        conflicts = detect_conflicts(sup, con)
        assert conflicts[0].severity == "CRITICAL"


class TestTimeline:
    def test_empty_timeline(self):
        assert build_timeline([]) == []

    def test_single_item(self):
        item = EvidenceItem(title="Test", description="D", engine="e", category="c", timestamp="2026-07-16T09:11:00+00:00")
        t = build_timeline([item])
        assert len(t) == 1
        assert t[0].title == "Test"

    def test_chronological_order(self):
        early = EvidenceItem(title="Early", description="D", engine="e", category="c", timestamp="2026-07-16T09:11:00+00:00")
        late = EvidenceItem(title="Late", description="D", engine="e", category="c", timestamp="2026-07-16T09:15:00+00:00")
        t = build_timeline([late, early])
        assert t[0].title == "Early"
        assert t[1].title == "Late"

    def test_timeline_summary(self):
        item = EvidenceItem(title="Scanner", description="Breakout", engine="scanner", category="scanner_momentum", timestamp="2026-07-16T09:11:00+00:00")
        s = timeline_summary([item])
        assert len(s) == 1
        assert s[0]["time"] == "09:11"
        assert s[0]["title"] == "Scanner"
        assert s[0]["engine"] == "scanner"
        assert s[0]["supports_decision"] is True

    def test_timeline_summary_empty(self):
        assert timeline_summary([]) == []

    def test_items_without_timestamp_excluded(self):
        item = EvidenceItem(title="No TS", description="D", engine="e", category="c")
        t = build_timeline([item])
        assert len(t) == 1  # still included, sorted with minimum timestamp


class TestEvidenceBuilder:
    def test_build_empty(self):
        builder = EvidenceBuilder()
        report = builder.build()
        assert report.decision_confidence == 0.0
        assert report.evidence_strength == 0.0
        assert report.explainability == 0.0
        assert report.decision_quality == "INSUFFICIENT"

    def test_build_with_scanner(self):
        builder = EvidenceBuilder()
        scanner = DictObj({"symbol": "BTC", "side": "LONG", "score": 0.85, "confidence": 90.0, "strategy": "momentum", "reason": "Strong", "signals": []})
        report = builder.build(scanner_result=scanner, recommendation="BUY")
        assert report.decision_confidence > 0.0
        assert report.evidence_strength > 0.0
        assert report.explainability > 0.0
        assert len(report.supporting_evidence) > 0

    def test_build_with_risk_rejection(self):
        builder = EvidenceBuilder()
        risk = DictObj({"allowed": False, "reason": "Max trades", "checks": ()})
        report = builder.build(risk_result=risk, recommendation="BUY")
        assert len(report.contradicting_evidence) > 0

    def test_build_with_all_inputs(self):
        builder = EvidenceBuilder()
        decision = DictObj({"decision": "BUY", "confidence": 80.0, "score": 0.8, "risk_score": 0.2, "reasons": [], "warnings": []})
        scanner = DictObj({"symbol": "BTC", "side": "LONG", "score": 0.85, "confidence": 90.0, "strategy": "momentum", "reason": "Strong", "signals": []})
        council = DictObj({"symbol": "BTC", "consensus_direction": "BULLISH", "consensus_score": 85.0, "agreement_level": "strong", "sources_agreeing": 4, "sources_disagreeing": 1, "agent_reports": []})
        market = {"regime": "TREND", "trend": "BULLISH", "trend_strength": "STRONG", "volatility_class": "NORMAL", "score": 0.85}
        portfolio = DictObj({"current_exposure": 5000, "max_exposure": 10000, "open_pnl": 200, "win_rate": 55.0})
        report = builder.build(
            decision_result=decision,
            scanner_result=scanner,
            council_result=council,
            market_regime_result=market,
            portfolio_result=portfolio,
            recommendation="BUY",
        )
        assert len(report.supporting_evidence) >= 1
        assert len(report.timeline) >= 1
        assert report.decision_confidence > 0.0
        assert report.evidence_strength > 0.0
        assert report.explainability > 0.0
        assert report.recommendation == "BUY"


class TestEvidenceEngine:
    def test_initial_state(self):
        engine = EvidenceEngine()
        assert engine.latest() is None
        assert engine.get("nonexistent") is None
        s = engine.status()
        assert s["reports_stored"] == 0

    def test_build_and_retrieve(self):
        engine = EvidenceEngine()
        scanner = DictObj({"symbol": "BTC", "side": "LONG", "score": 0.85, "confidence": 90.0, "strategy": "momentum", "reason": "Strong", "signals": []})
        report = engine.build(scanner_result=scanner, recommendation="BUY")
        assert engine.latest() is report
        assert engine.get(report.decision_id) is report
        s = engine.status()
        assert s["reports_stored"] == 1

    def test_build_multiple(self):
        engine = EvidenceEngine()
        for i in range(3):
            scanner = DictObj({"symbol": f"ASSET{i}", "side": "LONG", "score": 0.8, "confidence": 80.0, "strategy": "trend", "reason": "R", "signals": []})
            engine.build(scanner_result=scanner, recommendation="BUY")
        assert engine.status()["reports_stored"] == 3

    def test_timeline_endpoint(self):
        engine = EvidenceEngine()
        scanner = DictObj({"symbol": "BTC", "side": "LONG", "score": 0.85, "confidence": 90.0, "strategy": "momentum", "reason": "Strong", "signals": []})
        report = engine.build(scanner_result=scanner, recommendation="BUY")
        tl = engine.timeline(report.decision_id)
        assert len(tl) > 0
        assert tl[0]["engine"] == "scanner"

    def test_timeline_nonexistent(self):
        engine = EvidenceEngine()
        assert engine.timeline("nonexistent") == []

    def test_report_to_dict(self):
        engine = EvidenceEngine()
        scanner = DictObj({"symbol": "BTC", "side": "LONG", "score": 0.85, "confidence": 90.0, "strategy": "momentum", "reason": "Strong", "signals": []})
        report = engine.build(scanner_result=scanner, recommendation="BUY")
        d = report.to_dict()
        assert d["recommendation"] == "BUY"
        assert "decision_id" in d
        assert "decision_confidence" in d
        assert "evidence_strength" in d
        assert "explainability" in d
        assert "timeline" in d
        assert "created_at" in d

    def test_report_immutable_after_build(self):
        engine = EvidenceEngine()
        scanner = DictObj({"symbol": "BTC", "side": "LONG", "score": 0.85, "confidence": 90.0, "strategy": "momentum", "reason": "Strong", "signals": []})
        report = engine.build(scanner_result=scanner, recommendation="BUY")
        assert report.decision_confidence > 0.0
        with pytest.raises(Exception):
            report.recommendation = "SELL"


class TestEvidenceEngineIntegration:
    def test_full_story_long_signal(self):
        engine = EvidenceEngine()
        scanner = DictObj({"symbol": "BTC", "side": "LONG", "score": 0.88, "confidence": 92.0, "strategy": "momentum", "reason": "Strong momentum breakout with high volume", "signals": ["RSI(14) = 72", "Volume 2.5x average"]})
        risk = DictObj({"allowed": True, "reason": "", "checks": ()})
        council = DictObj({"symbol": "BTC", "consensus_direction": "BULLISH", "consensus_score": 88.0, "agreement_level": "strong", "sources_agreeing": 5, "sources_disagreeing": 0, "agent_reports": [DictObj({"agent_name": "TrendAgent", "direction": "BULLISH", "confidence": 90.0, "reasoning": ["Strong uptrend across timeframes"]})]})
        market = {"regime": "TREND", "trend": "BULLISH", "trend_strength": "STRONG", "volatility_class": "NORMAL", "score": 0.85}
        portfolio = DictObj({"current_exposure": 3000, "max_exposure": 10000, "open_pnl": 500, "win_rate": 62.0})
        report = engine.build(
            scanner_result=scanner,
            risk_result=risk,
            council_result=council,
            market_regime_result=market,
            portfolio_result=portfolio,
            recommendation="BUY",
        )
        assert report.recommendation == "BUY"
        assert report.decision_confidence >= 60.0
        assert report.evidence_strength >= 60.0
        assert report.explainability >= 50.0
        assert report.decision_quality in ("STRONG", "MODERATE")
        assert len(report.timeline) >= 3
        assert len(report.sources) >= 1

    def test_full_story_risk_rejection(self):
        engine = EvidenceEngine()
        scanner = DictObj({"symbol": "BTC", "side": "LONG", "score": 0.85, "confidence": 90.0, "strategy": "momentum", "reason": "Strong", "signals": []})
        risk = DictObj({"allowed": False, "reason": "Max open trades exceeded (3/3)", "checks": [DictObj({"name": "max_open_trades", "passed": False, "detail": "3 trades open"})]})
        council = DictObj({"symbol": "BTC", "consensus_direction": "BULLISH", "consensus_score": 80.0, "agreement_level": "moderate", "sources_agreeing": 3, "sources_disagreeing": 1, "agent_reports": []})
        market = {"regime": "TREND", "trend": "BULLISH", "trend_strength": "MODERATE", "volatility_class": "NORMAL", "score": 0.75}
        report = engine.build(
            scanner_result=scanner,
            risk_result=risk,
            council_result=council,
            market_regime_result=market,
            recommendation="BUY",
        )
        assert report.decision_confidence < 50.0
        assert len(report.contradicting_evidence) >= 1

    def test_no_evidence(self):
        engine = EvidenceEngine()
        report = engine.build(recommendation="HOLD")
        assert report.decision_confidence == 0.0
        assert report.evidence_strength == 0.0
        assert report.explainability == 0.0
        assert report.decision_quality == "INSUFFICIENT"
        assert report.recommendation == "HOLD"

    def test_immutable_historical(self):
        engine = EvidenceEngine()
        r1 = engine.build(recommendation="BUY")
        r2 = engine.build(recommendation="SELL")
        # Both reports are frozen and can never change
        assert r1.recommendation == "BUY"
        assert r2.recommendation == "SELL"
        assert r1.decision_id != r2.decision_id


class TestEdgeCases:
    def test_confidence_bounds(self):
        assert calculate_confidence([], []) == 0.0
        high = EvidenceItem(engine="scanner", severity="HIGH", confidence=1.0, supports_decision=True)
        c = calculate_confidence([high], [])
        assert 0.0 <= c <= 100.0

    def test_strength_bounds(self):
        assert calculate_evidence_strength([]) == 0.0
        high = EvidenceItem(engine="scanner", severity="HIGH", confidence=1.0, supports_decision=True)
        s = calculate_evidence_strength([high])
        assert 0.0 <= s <= 100.0

    def test_explainability_bounds(self):
        assert calculate_explainability([], [], [], 0) == 0.0
        item = EvidenceItem(engine="scanner", severity="HIGH", confidence=1.0, supports_decision=True)
        src = SourceTrace(origin="BTC", engine="scanner")
        e = calculate_explainability([item, item, item, item, item], [], [src, src, src], 5)
        assert 0.0 <= e <= 100.0

    def test_empty_report_to_dict(self):
        r = EvidenceReport()
        d = r.to_dict()
        assert "decision_id" in d
        assert d["decision_confidence"] == 0.0

    def test_severity_weights(self):
        assert SEVERITY_WEIGHTS["CRITICAL"] == 2.0
        assert SEVERITY_WEIGHTS["LOW"] == 0.5

    def test_source_weights(self):
        assert SOURCE_WEIGHTS["risk_engine"] > SOURCE_WEIGHTS["whale"]

    def test_strength_weights(self):
        assert STRENGTH_WEIGHTS["council"] > STRENGTH_WEIGHTS["whale"]
