from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DecisionEvaluator:
    """Evaluate decision results against actual trade outcomes and emit learning packages."""

    def __init__(self, ledger: Optional[Any] = None) -> None:
        from decision.kernel.DecisionLedger import DecisionLedger
        self.ledger = ledger or DecisionLedger()

    def evaluate(self, decision_id: str) -> Optional[dict[str, Any]]:
        """Perform a post-mortem evaluation of a finished decision and link it to the ledger."""
        record = self.ledger.get_record(decision_id)
        if not record:
            logger.warning("Decision %s not found in ledger for evaluation", decision_id)
            return None

        outcome = record.get("outcome")
        if not outcome:
            logger.warning("No outcome attached to decision %s for evaluation", decision_id)
            return None

        # Extract values
        pnl = outcome.get("pnl", 0.0)
        success = outcome.get("success", False)
        confidence = record.get("confidence", 50.0)
        decision = record.get("decision", "REJECT")
        side = record.get("side", "LONG")

        # 1. Prediction Accuracy (0.0 to 1.0)
        # Winning LONG or winning SHORT is correct prediction
        pred_accuracy = 1.0 if success else 0.0

        # 2. Confidence Accuracy (0.0 to 1.0)
        # High confidence should ideally lead to higher wins, low confidence to smaller wins/losses
        confidence_fraction = confidence / 100.0
        conf_accuracy = 1.0 - abs(confidence_fraction - pred_accuracy)

        # 3. Reasoning Quality (0.0 to 1.0)
        # Ratio of supporting reasons vs total evidence
        evidence_count = len(record.get("evidence", []))
        reasons_count = len(record.get("reasons", []))
        reasoning_quality = min(1.0, reasons_count / max(1, evidence_count))

        # 4. Risk Quality (0.0 to 1.0)
        # Lower risk score inputs corresponding to high outcomes is high quality
        risk_score = record.get("risk_score", 0.5)
        risk_quality = 1.0 - risk_score if success else risk_score

        # 5. Execution Quality (0.0 to 1.0)
        # High score if duration matches expected strategy targets
        duration_sec = outcome.get("duration_seconds", 3600)
        exec_quality = 1.0 if duration_sec < 86400 else 0.7  # penalty for very slow trades

        # 6. Decision Quality (overall composite index)
        decision_quality = (pred_accuracy * 0.4) + (conf_accuracy * 0.2) + (reasoning_quality * 0.1) + (risk_quality * 0.2) + (exec_quality * 0.1)

        evaluation = {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "prediction_accuracy": round(pred_accuracy, 2),
            "confidence_accuracy": round(conf_accuracy, 2),
            "reasoning_quality": round(reasoning_quality, 2),
            "risk_quality": round(risk_quality, 2),
            "execution_quality": round(exec_quality, 2),
            "decision_quality": round(decision_quality, 2),
        }

        # Save to ledger
        self.ledger.attach_evaluation(decision_id, evaluation)

        # Emit Learning Package
        self._emit_learning_data(record, outcome, evaluation)

        return evaluation

    def _emit_learning_data(self, record: dict[str, Any], outcome: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
        """Format and emit a structured package containing features, context, decision, outcome, and evaluation for ML."""
        learning_package = {
            "features": record.get("request", {}).get("signals", []),
            "context": record.get("context_snapshot", {}),
            "decision": {
                "decision_id": record.get("decision_id"),
                "symbol": record.get("symbol"),
                "side": record.get("side"),
                "decision": record.get("decision"),
                "confidence": record.get("confidence"),
            },
            "outcome": outcome,
            "evaluation": evaluation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("Learning Loop emitted structured learning data for decision %s", record.get("decision_id"))
        return learning_package
