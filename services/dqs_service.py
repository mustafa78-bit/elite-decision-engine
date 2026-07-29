from __future__ import annotations

import logging
from typing import Any, Callable, Optional, List

from database import Trade, Signal, JournalEntry, CognitiveBiasLog, get_session

logger = logging.getLogger(__name__)


class DQSService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.is_test = session_factory is not None

    def calculate_dqs_for_trade(self, trade_id: int) -> dict[str, Any]:
        session = self.session_factory()
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if not trade:
                return {"error": "Trade not found", "score": 0.0}

            # 1. Evidence Quality (0 - 100)
            # Default to signal confidence, fallback to 70.0
            evidence_quality = 70.0
            signal = None
            if trade.signal_id:
                signal = session.query(Signal).filter(Signal.id == trade.signal_id).first()
                if signal and signal.confidence:
                    evidence_quality = signal.confidence

            # 2. Timing Accuracy (0 - 100)
            # If we bought with minimal slippage relative to signal price
            timing_accuracy = 100.0
            if signal and trade.entry and signal.price:
                diff = abs(trade.entry - signal.price) / signal.price
                timing_accuracy = max(0.0, 100.0 - (diff * 200.0)) # penalty of 2 pts per % slippage

            # 3. Risk Compliance (0 - 100)
            # If risk ratio or RR parameter is set, or if we have a defined stop loss
            risk_compliance = 100.0
            if not trade.stop or trade.stop == 0.0:
                risk_compliance = 50.0 # heavy penalty for no stop loss!

            # 4. Execution Precision (0 - 100)
            # If we used optimal order type or filled fully
            execution_precision = 95.0

            # 5. Psychological Calibration (0 - 100)
            # Penalize for cognitive biases logged for this user / decision
            psychological_calibration = 100.0
            if trade.signal_id:
                biases = session.query(CognitiveBiasLog).filter(CognitiveBiasLog.decision_id == trade.signal_id).all()
                psychological_calibration -= len(biases) * 15.0
                psychological_calibration = max(0.0, psychological_calibration)

            # 6. Discipline Index (0 - 100)
            # Start at 100, penalize for deviations
            discipline_index = 100.0
            if trade.status == "SL_HIT":
                discipline_index -= 10.0 # penalty for losing trades, but normal
            elif trade.status == "CLOSED" and trade.close_reason == "MANUAL":
                discipline_index -= 15.0 # penalty for manual override deviating from SL/TP bounds

            # 7. Outcome Score (0 - 100)
            outcome_score = 50.0
            if trade.pnl:
                if trade.pnl > 0:
                    outcome_score = 100.0
                elif trade.pnl < 0:
                    outcome_score = 30.0

            # Weighted Formula
            dqs = (
                (evidence_quality * 0.15)
                + (timing_accuracy * 0.15)
                + (risk_compliance * 0.20)
                + (execution_precision * 0.10)
                + (psychological_calibration * 0.15)
                + (discipline_index * 0.15)
                + (outcome_score * 0.10)
            )

            dqs = round(max(0.0, min(100.0, dqs)), 2)
            logger.info("TELEMETRY: [DQS] Calculated score of %s for trade %s", dqs, trade_id)

            return {
                "trade_id": trade_id,
                "score": dqs,
                "breakdown": {
                    "evidence_quality": round(evidence_quality, 1),
                    "timing_accuracy": round(timing_accuracy, 1),
                    "risk_compliance": round(risk_compliance, 1),
                    "execution_precision": round(execution_precision, 1),
                    "psychological_calibration": round(psychological_calibration, 1),
                    "discipline_index": round(discipline_index, 1),
                    "outcome_score": round(outcome_score, 1)
                }
            }
        finally:
            if not self.is_test:
                session.close()
