from __future__ import annotations

import logging
from typing import Any, Optional

import database
from database import EventLedger

logger = logging.getLogger(__name__)


class TrustMetricsService:
    """Calculate platform trust metrics directly derived from the append-only Ledger."""

    def __init__(self, session_factory=None) -> None:
        self.session_factory = session_factory

    def _get_session(self):
        if self.session_factory is not None:
            return self.session_factory()
        return database.get_session()

    def calculate_metrics(self) -> dict[str, Any]:
        """Derive all trust metrics directly from the central Event Ledger."""
        session = self._get_session()
        try:
            # Query all Outcome Calculated events
            outcomes = (
                session.query(EventLedger)
                .filter(EventLedger.event_type == "Outcome Calculated")
                .all()
            )

            # Query all Decision Generated events (to calculate prediction accuracy / calibration)
            decisions = (
                session.query(EventLedger)
                .filter(EventLedger.event_type == "Decision Generated")
                .all()
            )

            total_trades = len(outcomes)
            if total_trades == 0:
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "loss_rate": 0.0,
                    "decision_accuracy": 0.0,
                    "prediction_accuracy": 0.0,
                    "average_return": 0.0,
                    "confidence_calibration": {
                        "avg_win_confidence": 0.0,
                        "avg_loss_confidence": 0.0,
                        "calibration_gap": 0.0,
                    },
                    "trust_score": 50.0,  # Default neutral trust score
                    "reasons_for_success": {},
                    "reasons_for_failure": {},
                }

            wins = 0
            losses = 0
            total_pnl = 0.0
            reasons_success: dict[str, int] = {}
            reasons_failure: dict[str, int] = {}

            # Map trade_id to its success/failure status
            trade_outcomes = {}

            for outcome in outcomes:
                details = outcome.details or {}
                trade_id = outcome.trade_id
                success = details.get("success", False)
                pnl = details.get("pnl", 0.0)

                trade_outcomes[trade_id] = success
                total_pnl += pnl

                if success:
                    wins += 1
                else:
                    losses += 1

            # Fetch feedback events to extract reasons
            feedback_events = (
                session.query(EventLedger)
                .filter(EventLedger.event_type == "Feedback Stored")
                .all()
            )

            for fb in feedback_events:
                details = fb.details or {}
                if details.get("stage") == "CLOSURE":
                    succ_reason = details.get("reason_for_success")
                    fail_reason = details.get("reason_for_failure")
                    if succ_reason:
                        reasons_success[succ_reason] = reasons_success.get(succ_reason, 0) + 1
                    if fail_reason:
                        reasons_failure[fail_reason] = reasons_failure.get(fail_reason, 0) + 1

            win_rate = wins / total_trades
            loss_rate = losses / total_trades
            avg_return = total_pnl / total_trades

            # Calibration: analyze decision confidence vs actual outcome
            win_confidences = []
            loss_confidences = []

            for dec in decisions:
                details = dec.details or {}
                confidence = details.get("confidence", 0.0)
                # Find matching outcome
                matching_outcome = None

                # If signal_id is present, let's find if a trade was executed and what its outcome was
                sig_id = dec.signal_id
                if sig_id:
                    # Look up if any outcome had the same signal_id
                    for o in outcomes:
                        if o.signal_id == sig_id:
                            matching_outcome = o.details.get("success")
                            break

                if matching_outcome is not None:
                    if matching_outcome:
                        win_confidences.append(confidence)
                    else:
                        loss_confidences.append(confidence)

            avg_win_conf = sum(win_confidences) / len(win_confidences) if win_confidences else 0.0
            avg_loss_conf = sum(loss_confidences) / len(loss_confidences) if loss_confidences else 0.0
            calibration_gap = abs(avg_win_conf - avg_loss_conf)

            # Trust score calculation (0 - 100)
            # Base trust is 50. We add/subtract based on win_rate, return, and calibration
            trust_score = 50.0 + (win_rate * 40.0) - (loss_rate * 20.0)
            if avg_return > 0:
                trust_score += 10.0
            else:
                trust_score -= 10.0
            # Cap trust score between 0 and 100
            trust_score = max(0.0, min(100.0, trust_score))

            return {
                "total_trades": total_trades,
                "win_rate": round(win_rate * 100, 2),
                "loss_rate": round(loss_rate * 100, 2),
                "decision_accuracy": round(win_rate * 100, 2),
                "prediction_accuracy": round((1.0 - (calibration_gap / 100.0)) * 100, 2) if calibration_gap > 0 else 100.0,
                "average_return": round(avg_return, 4),
                "confidence_calibration": {
                    "avg_win_confidence": round(avg_win_conf, 2),
                    "avg_loss_confidence": round(avg_loss_conf, 2),
                    "calibration_gap": round(calibration_gap, 2),
                },
                "trust_score": round(trust_score, 2),
                "reasons_for_success": reasons_success,
                "reasons_for_failure": reasons_failure,
            }
        finally:
            session.close()
