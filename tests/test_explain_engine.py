"""Unit + Integration tests for the Explain Engine.

Verifies deterministic explanation generation from:
- Technical, Whale, News, Risk, Trend scores
- Portfolio context
- Performance context
"""

from __future__ import annotations

import pytest

from explain import ExplainEngine, ExplainInput, ExplainResult
from explain.engine import ExplainService
from database import DecisionExplanation, Signal


# ── Unit tests: pure ExplainEngine ──────────────────────────────────────────


def _make_input(**overrides) -> ExplainInput:
    kwargs = dict(
        symbol="BTCUSDT",
        side="LONG",
        technical_score=0.0,
        whale_score=0.0,
        news_score=0.0,
        risk_score=0.0,
        trend_score=0.0,
        portfolio_total_equity=10000.0,
        portfolio_initial_capital=10000.0,
        portfolio_exposure=0.0,
        performance_total_pnl=0.0,
        performance_sharpe=0.0,
        performance_profit_factor=0.0,
        performance_max_drawdown=0.0,
    )
    kwargs.update(overrides)
    return ExplainInput(**kwargs)


def test_buy_decision():
    inp = _make_input(
        side="LONG",
        technical_score=0.80,
        trend_score=0.75,
        risk_score=0.70,
    )
    result = ExplainEngine().explain(inp)
    assert result.decision == "BUY"
    assert result.confidence >= 55.0
    assert len(result.reasons) >= 2
    assert len(result.supporting_signals) >= 3
    assert "Technical" in result.supporting_signals
    assert "Trend" in result.supporting_signals
    assert "Risk" in result.supporting_signals


def test_sell_decision():
    inp = _make_input(
        side="SHORT",
        technical_score=0.80,
        trend_score=0.70,
        risk_score=0.65,
        whale_score=0.60,
    )
    result = ExplainEngine().explain(inp)
    assert result.decision == "SELL"
    assert result.confidence >= 50.0


def test_hold_decision_low_scores():
    inp = _make_input(side="LONG")
    result = ExplainEngine().explain(inp)
    assert result.decision == "HOLD"
    assert result.confidence == 0.0
    assert any("Insufficient" in r for r in result.reasons)


def test_hold_decision_conflicting():
    inp = _make_input(
        side="LONG",
        technical_score=0.10,
        trend_score=0.85,
        risk_score=0.10,
        news_score=0.80,
    )
    result = ExplainEngine().explain(inp)
    # high disagreement → confidence penalty
    assert result.confidence < 70.0


def test_warnings_low_risk():
    inp = _make_input(
        side="LONG",
        technical_score=0.80,
        trend_score=0.75,
        risk_score=0.20,
    )
    result = ExplainEngine().explain(inp)
    assert any("risk" in w.lower() for w in result.warnings)


def test_warnings_overleveraged():
    inp = _make_input(
        side="LONG",
        technical_score=0.80,
        trend_score=0.75,
        risk_score=0.70,
        portfolio_total_equity=10000.0,
        portfolio_exposure=50000.0,
    )
    result = ExplainEngine().explain(inp)
    assert any("over-leveraged" in w.lower() for w in result.warnings)


def test_reasons_include_all_high_scores():
    inp = _make_input(
        side="LONG",
        technical_score=0.85,
        whale_score=0.70,
        news_score=0.65,
        risk_score=0.75,
        trend_score=0.80,
    )
    result = ExplainEngine().explain(inp)
    reasons_text = " ".join(result.reasons).lower()
    assert "technical" in reasons_text
    assert "whale" in reasons_text
    assert "news" in reasons_text
    assert "risk" in reasons_text
    assert "trend" in reasons_text


def test_risk_notes_format():
    inp = _make_input(
        side="LONG",
        risk_score=0.65,
        portfolio_total_equity=10000.0,
        portfolio_exposure=3000.0,
        performance_max_drawdown=15.0,
    )
    result = ExplainEngine().explain(inp)
    assert len(result.risk_notes) >= 2
    assert any("MODERATE" in n for n in result.risk_notes)
    assert any("30%" in n or "exposure" in n.lower() for n in result.risk_notes)


def test_summary_format():
    inp = _make_input(
        symbol="ETHUSDT",
        side="SHORT",
        technical_score=0.80,
        trend_score=0.70,
    )
    result = ExplainEngine().explain(inp)
    assert result.summary.startswith("SELL ETHUSDT")
    assert "confidence" in result.summary
    assert "Technical" in result.summary
    assert "Trend" in result.summary


def test_confidence_boosted_by_performance():
    base = _make_input(
        side="LONG",
        technical_score=0.70,
        trend_score=0.70,
        risk_score=0.70,
    )
    boosted = _make_input(
        side="LONG",
        technical_score=0.70,
        trend_score=0.70,
        risk_score=0.70,
        performance_total_pnl=5000.0,
        performance_sharpe=2.0,
        performance_profit_factor=3.0,
        portfolio_total_equity=15000.0,
        portfolio_initial_capital=10000.0,
    )
    base_result = ExplainEngine().explain(base)
    boosted_result = ExplainEngine().explain(boosted)
    assert boosted_result.confidence > base_result.confidence


def test_confidence_penalized_by_overexposure():
    inp = _make_input(
        side="LONG",
        technical_score=0.80,
        trend_score=0.80,
        risk_score=0.80,
        portfolio_total_equity=10000.0,
        portfolio_exposure=50000.0,
    )
    result = ExplainEngine().explain(inp)
    assert result.confidence < 80.0


def test_supporting_signals_empty():
    inp = _make_input(side="LONG")
    result = ExplainEngine().explain(inp)
    assert result.supporting_signals == []


def test_supporting_signals_all():
    inp = _make_input(
        side="LONG",
        technical_score=0.80,
        whale_score=0.60,
        news_score=0.70,
        risk_score=0.65,
        trend_score=0.75,
    )
    result = ExplainEngine().explain(inp)
    assert set(result.supporting_signals) == {
        "Technical", "Whale", "News", "Risk", "Trend",
    }


def test_deterministic():
    inp = _make_input(
        side="LONG",
        technical_score=0.80,
        trend_score=0.70,
        risk_score=0.60,
    )
    r1 = ExplainEngine().explain(inp)
    r2 = ExplainEngine().explain(inp)
    assert r1.decision == r2.decision
    assert r1.confidence == r2.confidence
    assert r1.reasons == r2.reasons
    assert r1.summary == r2.summary


# ── Integration tests: ExplainService with DB ─────────────────────────────


def test_service_saves_to_db(db_session, session_factory):
    signal = Signal(
        symbol="BTCUSDT",
        side="LONG",
        score=0.80,
        risk_score=0.70,
        trend_score=0.75,
        status="OPEN",
    )
    db_session.add(signal)
    db_session.flush()

    service = ExplainService(session_factory=session_factory)
    model = service.explain_signal(signal, whale_score=0.60, news_score=0.55)

    assert isinstance(model, DecisionExplanation)
    assert model.id is not None
    assert model.symbol == "BTCUSDT"
    assert model.side == "LONG"
    assert model.decision == "BUY"
    assert model.confidence >= 50.0
    assert len(model.reasons) > 0
    assert len(model.risk_notes) > 0
    assert model.summary != ""
    assert model.technical_score == 0.80
    assert model.whale_score == 0.60
    assert model.news_score == 0.55
    assert model.risk_score == 0.70
    assert model.trend_score == 0.75


def test_service_with_portfolio_and_performance(db_session, session_factory):
    signal = Signal(symbol="ETHUSDT", side="SHORT", score=0.75, risk_score=0.60)
    db_session.add(signal)
    db_session.flush()

    from portfolio.core import PortfolioSnapshot
    from performance.core import PerformanceReport

    snap = PortfolioSnapshot(
        total_equity=12000.0,
        initial_capital=10000.0,
        unrealized_pnl=1000.0,
        realized_pnl=1000.0,
        exposure=2000.0,
        total_pnl=2000.0,
        profit_factor=2.5,
        win_rate=60.0,
        max_drawdown=8.0,
    )
    perf = PerformanceReport(
        sharpe_ratio=1.5,
        sortino_ratio=2.0,
        calmar_ratio=0.8,
    )

    service = ExplainService(session_factory=session_factory)
    model = service.explain_signal(signal, snapshot=snap, performance=perf)

    assert model.decision == "SELL"
    assert model.confidence >= 50.0
    assert model.portfolio_total_equity == 12000.0
    assert model.performance_sharpe == 1.5


def test_service_explain_input(session_factory):
    inp = _make_input(
        symbol="BTCUSDT",
        side="BUY",
        technical_score=0.90,
        risk_score=0.80,
        trend_score=0.85,
    )
    service = ExplainService(session_factory=session_factory)
    model = service.explain(inp)
    assert model.decision in ("BUY", "HOLD")
    assert model.confidence > 0


def test_from_signal_static():
    signal = Signal(
        symbol="BTCUSDT", side="LONG", score=0.80,
        risk_score=0.70, trend_score=0.75,
    )
    inp = ExplainEngine.from_signal(signal)
    assert inp.symbol == "BTCUSDT"
    assert inp.side == "LONG"
    assert inp.technical_score == 0.80
    assert inp.risk_score == 0.70
    assert inp.trend_score == 0.75
    assert inp.whale_score == 0.0
    assert inp.news_score == 0.0
