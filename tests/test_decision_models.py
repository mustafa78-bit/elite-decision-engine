from datetime import datetime, timezone

from decision.models import (
    DecisionContext,
    DecisionFactor,
    DecisionExplanation,
    DecisionSnapshot,
    TradeOutcome,
)


class TestDecisionFactor:

    def test_defaults(self):
        f = DecisionFactor(name="test", value=0.5)
        assert f.name == "test"
        assert f.value == 0.5
        assert f.weight == 1.0
        assert f.source == ""

    def test_weighted_value(self):
        f = DecisionFactor(name="test", value=10.0, weight=2.0)
        assert f.weighted_value() == 20.0

    def test_to_dict(self):
        f = DecisionFactor(name="test", value=0.5, weight=1.5, source="whale")
        d = f.to_dict()
        assert d["name"] == "test"
        assert d["value"] == 0.5
        assert d["weight"] == 1.5
        assert d["source"] == "whale"


class TestDecisionContext:

    def test_defaults(self):
        ctx = DecisionContext()
        assert ctx.signal_symbol == ""
        assert ctx.signal_side == ""
        assert ctx.factors == []
        assert ctx.base_score == 0.0

    def test_add_factor(self):
        ctx = DecisionContext()
        f = DecisionFactor(name="whale_health", value=1.0)
        ctx.add_factor(f)
        assert len(ctx.factors) == 1
        assert ctx.factor_by_name("whale_health") is f
        assert ctx.factor_by_name("nonexistent") is None

    def test_total_weighted_score_empty(self):
        ctx = DecisionContext(base_score=50.0)
        assert ctx.total_weighted_score() == 50.0

    def test_total_weighted_score_with_factors(self):
        ctx = DecisionContext(base_score=0.0)
        ctx.add_factor(DecisionFactor(name="a", value=80.0, weight=1.0))
        ctx.add_factor(DecisionFactor(name="b", value=60.0, weight=1.0))
        assert ctx.total_weighted_score() == 70.0

    def test_total_weighted_score_weighted(self):
        ctx = DecisionContext(base_score=0.0)
        ctx.add_factor(DecisionFactor(name="a", value=100.0, weight=2.0))
        ctx.add_factor(DecisionFactor(name="b", value=50.0, weight=1.0))
        assert ctx.total_weighted_score() == 83.33333333333333

    def test_to_dict(self):
        ctx = DecisionContext(signal_symbol="BTC", signal_side="LONG", base_score=50.0)
        ctx.add_factor(DecisionFactor(name="test", value=1.0))
        d = ctx.to_dict()
        assert d["signal_symbol"] == "BTC"
        assert d["signal_side"] == "LONG"
        assert d["base_score"] == 50.0
        assert len(d["factors"]) == 1
        assert "total_weighted_score" in d
        assert "timestamp" in d


class TestDecisionExplanation:

    def test_defaults(self):
        exp = DecisionExplanation()
        assert exp.decision == "PENDING"
        assert exp.reasons["approval"] == []
        assert exp.reasons["rejection"] == []

    def test_add_approval_reason(self):
        exp = DecisionExplanation()
        exp.add_approval_reason("All checks passed")
        assert "All checks passed" in exp.reasons["approval"]
        exp.add_approval_reason("All checks passed")
        assert len(exp.reasons["approval"]) == 1

    def test_add_rejection_reason(self):
        exp = DecisionExplanation()
        exp.add_rejection_reason("BTC unhealthy")
        assert "BTC unhealthy" in exp.reasons["rejection"]

    def test_is_approved(self):
        exp = DecisionExplanation(decision="APPROVED")
        assert exp.is_approved() is True
        assert exp.is_rejected() is False

    def test_is_rejected(self):
        exp = DecisionExplanation(decision="REJECTED")
        assert exp.is_rejected() is True
        assert exp.is_approved() is False

    def test_summary(self):
        exp = DecisionExplanation(decision="APPROVED")
        exp.add_approval_reason("OK")
        assert "APPROVED" in exp.summary()
        assert "OK" in exp.summary()

    def test_to_dict(self):
        exp = DecisionExplanation(decision="APPROVED")
        exp.add_approval_reason("OK")
        d = exp.to_dict()
        assert d["decision"] == "APPROVED"
        assert "OK" in d["reasons"]["approval"]


class TestDecisionSnapshot:

    def test_to_dict(self):
        ctx = DecisionContext(signal_symbol="BTC")
        exp = DecisionExplanation(decision="APPROVED")
        snap = DecisionSnapshot(
            signal_id=1, decision="APPROVED", score=85.0, context=ctx, explanation=exp, confidence=80.0
        )
        d = snap.to_dict()
        assert d["signal_id"] == 1
        assert d["decision"] == "APPROVED"
        assert d["score"] == 85.0
        assert d["confidence"] == 80.0
        assert d["context"]["signal_symbol"] == "BTC"


class TestTradeOutcome:

    def test_defaults(self):
        outcome = TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000, exit_price=55000, pnl=5000, pnl_pct=10.0
        )
        assert outcome.is_win() is True
        assert outcome.is_loss() is False

    def test_loss(self):
        outcome = TradeOutcome(
            symbol="BTC", side="SHORT", entry_price=50000, exit_price=55000, pnl=-5000, pnl_pct=-10.0
        )
        assert outcome.is_win() is False
        assert outcome.is_loss() is True

    def test_to_dict(self):
        outcome = TradeOutcome(
            symbol="BTC", side="LONG", entry_price=50000, exit_price=55000, pnl=5000, pnl_pct=10.0
        )
        d = outcome.to_dict()
        assert d["symbol"] == "BTC"
        assert d["is_win"] is True
