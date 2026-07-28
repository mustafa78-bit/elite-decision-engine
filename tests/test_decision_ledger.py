from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

from api.main import app
from decision.kernel.DecisionContext import DecisionContext
from decision.kernel.DecisionKernel import DecisionKernel
from decision.kernel.DecisionRequest import DecisionRequest
from decision.kernel.DecisionLedger import DecisionLedger
from decision.kernel.DecisionEvaluator import DecisionEvaluator
from decision.kernel.CalibrationEngine import CalibrationEngine
from decision.kernel.TrustMetrics import TrustMetrics


def test_decision_ledger_operations():
    """Test append, retrieve, and update operations on DecisionLedger."""
    ledger_file = "test_decision_ledger.json"
    if os.path.exists(ledger_file):
        os.remove(ledger_file)

    ledger = DecisionLedger(filepath=ledger_file)

    # Append
    ledger.append("dec_123", {
        "decision_id": "dec_123",
        "symbol": "BTCUSDT",
        "side": "LONG",
        "decision": "APPROVE",
        "confidence": 75.0,
        "score": 0.8,
    })

    record = ledger.get_record("dec_123")
    assert record is not None
    assert record["symbol"] == "BTCUSDT"
    assert record["execution_status"] == "PENDING"

    # Update execution status
    ledger.update_execution_status("dec_123", "EXECUTED")
    assert ledger.get_record("dec_123")["execution_status"] == "EXECUTED"

    # Attach outcome
    outcome = {
        "pnl": 150.0,
        "success": True,
        "duration_seconds": 1200,
        "max_drawdown": 10.0,
        "max_profit": 150.0,
        "exit_reason": "TP_HIT",
    }
    ledger.attach_outcome("dec_123", outcome)
    assert ledger.get_record("dec_123")["outcome"]["pnl"] == 150.0

    # Cleanup
    if os.path.exists(ledger_file):
        os.remove(ledger_file)


def test_decision_evaluator_and_learning_loops():
    """Test DecisionEvaluator calculation parameters and learning hooks."""
    ledger_file = "test_eval_ledger.json"
    if os.path.exists(ledger_file):
        os.remove(ledger_file)

    ledger = DecisionLedger(filepath=ledger_file)
    evaluator = DecisionEvaluator(ledger=ledger)

    ledger.append("dec_999", {
        "decision_id": "dec_999",
        "symbol": "ETHUSDT",
        "side": "SHORT",
        "decision": "STRONG_APPROVE",
        "confidence": 90.0,
        "score": 0.85,
        "risk_score": 0.2,
        "evidence": [{"name": "rsi", "value": 75}],
        "reasons": ["RSI Overbought"],
    })

    # Fail before outcome is attached
    assert evaluator.evaluate("dec_999") is None

    # Attach outcome and evaluate
    outcome = {
        "pnl": 200.0,
        "success": True,
        "duration_seconds": 600,
        "max_drawdown": 0.0,
        "max_profit": 200.0,
        "exit_reason": "TP_HIT",
    }
    ledger.attach_outcome("dec_999", outcome)

    eval_result = evaluator.evaluate("dec_999")
    assert eval_result is not None
    assert eval_result["prediction_accuracy"] == 1.0
    assert eval_result["decision_quality"] > 0.8

    # Check updated record
    rec = ledger.get_record("dec_999")
    assert rec["evaluation"] == eval_result

    if os.path.exists(ledger_file):
        os.remove(ledger_file)


def test_calibration_and_trust_calculators():
    """Test continuous math calibration and trust scoring engines."""
    ledger_file = "test_metrics_ledger.json"
    if os.path.exists(ledger_file):
        os.remove(ledger_file)

    ledger = DecisionLedger(filepath=ledger_file)
    calibration = CalibrationEngine(ledger=ledger)
    trust = TrustMetrics(ledger=ledger)

    # Empty stats
    assert calibration.calculate_metrics()["brier_score"] == 0.0
    assert trust.calculate_trust()["win_rate"] == 0.0

    # Log several winning and losing trades to calculate stats
    ledger.append("dec_win1", {
        "decision_id": "dec_win1",
        "decision": "APPROVE",
        "confidence": 80.0,
    })
    ledger.attach_outcome("dec_win1", {"pnl": 50.0, "success": True})

    ledger.append("dec_win2", {
        "decision_id": "dec_win2",
        "decision": "STRONG_APPROVE",
        "confidence": 90.0,
    })
    ledger.attach_outcome("dec_win2", {"pnl": 120.0, "success": True})

    ledger.append("dec_loss1", {
        "decision_id": "dec_loss1",
        "decision": "APPROVE",
        "confidence": 70.0,
    })
    ledger.attach_outcome("dec_loss1", {"pnl": -30.0, "success": False})

    cal_metrics = calibration.calculate_metrics()
    assert cal_metrics["actual_success_rate"] == round((2 / 3) * 100, 1)
    assert cal_metrics["brier_score"] > 0.0

    trust_metrics = trust.calculate_trust()
    assert trust_metrics["win_rate"] == round((2 / 3) * 100, 1)
    assert trust_metrics["sharpe"] != 0.0
    assert trust_metrics["trust_score"] > 0.0

    if os.path.exists(ledger_file):
        os.remove(ledger_file)


def test_rest_api_replays_and_explanations(api_client):
    """Test REST API endpoint results using pre-authenticated TestClient conftest fixture."""
    client = api_client

    # Empty brief
    resp = client.get("/founder/brief")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "brief" in data

    # Graph ledger
    resp = client.get("/graph/ledger")
    assert resp.status_code == 200
    data = resp.json()
    assert "ledger" in data

    # Metrics
    resp = client.get("/founder/calibration")
    assert resp.status_code == 200
    assert "metrics" in resp.json()

    resp = client.get("/founder/trust")
    assert resp.status_code == 200
    assert "metrics" in resp.json()
