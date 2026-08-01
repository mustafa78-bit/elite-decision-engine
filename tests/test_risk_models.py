"""Tests for the shared risk decision model."""

import logging

from risk.models import (
    RejectionCode,
    RiskCheckDetail,
    RiskDecision,
    risk_decision_from_checks,
    summarize_decision,
)


class TestRejectionCode:

    def test_constants_are_strings(self):
        assert RejectionCode.MAX_OPEN_TRADES == "MAX_OPEN_TRADES"
        assert RejectionCode.SYMBOL_EXPOSURE == "SYMBOL_EXPOSURE"
        assert RejectionCode.PORTFOLIO_EXPOSURE == "PORTFOLIO_EXPOSURE"
        assert RejectionCode.DAILY_LOSS_LIMIT == "DAILY_LOSS_LIMIT"
        assert RejectionCode.POSITION_SIZE_LIMIT == "POSITION_SIZE_LIMIT"
        assert RejectionCode.VOLATILITY_TOO_HIGH == "VOLATILITY_TOO_HIGH"
        assert RejectionCode.REGIME_DEAD == "REGIME_DEAD"
        assert RejectionCode.EXCHANGE_OFFLINE == "EXCHANGE_OFFLINE"
        assert RejectionCode.EXCHANGE_NOT_CONFIGURED == "EXCHANGE_NOT_CONFIGURED"
        assert RejectionCode.RISK_BUDGET_EXCEEDED == "RISK_BUDGET_EXCEEDED"
        assert RejectionCode.INVALID_TRADE == "INVALID_TRADE"


class TestRiskCheckDetail:

    def test_basic_passed(self):
        detail = RiskCheckDetail(name="test", passed=True, detail="ok")
        assert detail.name == "test"
        assert detail.passed is True
        assert detail.detail == "ok"
        assert detail.value is None
        assert detail.limit is None

    def test_with_value_and_limit(self):
        detail = RiskCheckDetail(
            name="MAX_OPEN_TRADES", passed=False,
            detail="Too many trades", value=5.0, limit=3.0,
        )
        assert detail.value == 5.0
        assert detail.limit == 3.0

    def test_frozen(self):
        detail = RiskCheckDetail(name="a", passed=True)
        try:
            detail.passed = False
            assert False, "Should be frozen"
        except Exception:
            pass


class TestRiskDecision:

    def test_allowed_decision(self):
        decision = RiskDecision(allowed=True, reason="")
        assert decision.allowed is True
        assert decision.reason == ""
        assert decision.rejection_code is None
        assert decision.checks == ()

    def test_rejected_decision(self):
        decision = RiskDecision(
            allowed=False, reason="Too risky",
            rejection_code="MAX_OPEN_TRADES",
            checks=(RiskCheckDetail(name="MAX_OPEN_TRADES", passed=False, detail="Too many"),),
        )
        assert decision.allowed is False
        assert decision.rejection_code == "MAX_OPEN_TRADES"

    def test_first_failure_returns_first_failed_check(self):
        checks = [
            RiskCheckDetail(name="check1", passed=True),
            RiskCheckDetail(name="check2", passed=False, detail="failed"),
            RiskCheckDetail(name="check3", passed=False, detail="also failed"),
        ]
        decision = RiskDecision(allowed=False, reason="", checks=tuple(checks))
        failure = decision.first_failure()
        assert failure is not None
        assert failure.name == "check2"
        assert failure.detail == "failed"

    def test_first_failure_none_when_all_pass(self):
        checks = [
            RiskCheckDetail(name="check1", passed=True),
            RiskCheckDetail(name="check2", passed=True),
        ]
        decision = RiskDecision(allowed=True, reason="", checks=tuple(checks))
        assert decision.first_failure() is None

    def test_first_failure_none_when_no_checks(self):
        decision = RiskDecision(allowed=True, reason="")
        assert decision.first_failure() is None

    def test_metadata(self):
        decision = RiskDecision(
            allowed=True, reason="",
            metadata={"volatility_pct": 2.5, "regime": "TRENDING"},
        )
        assert decision.metadata["volatility_pct"] == 2.5
        assert decision.metadata["regime"] == "TRENDING"


class TestRiskDecisionFromChecks:

    def test_all_pass(self):
        checks = [
            RiskCheckDetail(name="check1", passed=True),
            RiskCheckDetail(name="check2", passed=True),
        ]
        decision = risk_decision_from_checks(checks)
        assert decision.allowed is True
        assert decision.reason == ""
        assert len(decision.checks) == 2

    def test_first_failure_short_circuits(self):
        checks = [
            RiskCheckDetail(name="check1", passed=True),
            RiskCheckDetail(name="check2", passed=False, detail="failed here"),
            RiskCheckDetail(name="check3", passed=False, detail="never reached"),
        ]
        decision = risk_decision_from_checks(checks)
        assert decision.allowed is False
        assert decision.reason == "failed here"
        assert decision.rejection_code == "check2"
        assert len(decision.checks) == 3

    def test_metadata_passthrough(self):
        checks = [RiskCheckDetail(name="c1", passed=False, detail="fail")]
        decision = risk_decision_from_checks(checks, {"extra": "data"})
        assert decision.metadata["extra"] == "data"

    def test_empty_checks_allowed(self):
        decision = risk_decision_from_checks([])
        assert decision.allowed is True
        assert decision.reason == ""
        assert decision.checks == ()


class TestSummarizeDecision:

    def test_allowed_logs_info(self, caplog):
        caplog.set_level(logging.INFO)
        decision = RiskDecision(allowed=True, checks=(
            RiskCheckDetail(name="c1", passed=True),
        ))
        summarize_decision(decision, "TestComponent")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.INFO
        assert "Risk check passed" in caplog.text

    def test_rejected_logs_warning(self, caplog):
        caplog.set_level(logging.WARNING)
        decision = RiskDecision(
            allowed=False, reason="blocked",
            rejection_code="TEST_FAIL",
            checks=(RiskCheckDetail(name="TEST_FAIL", passed=False, detail="blocked"),),
        )
        summarize_decision(decision, "TestComponent")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.WARNING
        assert "Risk rejected" in caplog.text
        assert "TEST_FAIL" in caplog.text
        assert "blocked" in caplog.text
