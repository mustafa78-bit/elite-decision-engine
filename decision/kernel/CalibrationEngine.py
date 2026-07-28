from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CalibrationEngine:
    """Calculate ECE, Murphy Brier, and confidence drifts from Decision Ledger."""

    def __init__(self, ledger: Optional[Any] = None) -> None:
        from decision.kernel.DecisionLedger import DecisionLedger
        self.ledger = ledger or DecisionLedger()

    def calculate_metrics(self) -> dict[str, Any]:
        """Compute system calibration metrics across all logged decision outcomes."""
        records = self.ledger.get_all_records()
        completed = [r for r in records if r.get("outcome") is not None]

        if not completed:
            return {
                "predicted_confidence": 0.0,
                "actual_success_rate": 0.0,
                "calibration_error": 0.0,
                "brier_score": 0.0,
                "confidence_distribution": {},
                "confidence_drift": 0.0,
            }

        confidences = []
        outcomes = []
        bins = {i: {"count": 0, "successes": 0, "sum_conf": 0.0} for i in range(10)}

        for r in completed:
            conf = r.get("confidence", 50.0)
            suc = 1.0 if r["outcome"].get("success", False) else 0.0
            confidences.append(conf)
            outcomes.append(suc)

            # Binning confidence (e.g. 0-10%, 10-20%, ..., 90-100%)
            bin_idx = min(9, int(conf // 10))
            bins[bin_idx]["count"] += 1
            bins[bin_idx]["successes"] += suc
            bins[bin_idx]["sum_conf"] += conf / 100.0

        # ECE (Expected Calibration Error) Calculation
        total_count = len(completed)
        ece = 0.0
        brier = 0.0

        for idx, b in bins.items():
            if b["count"] > 0:
                bin_acc = b["successes"] / b["count"]
                bin_conf = b["sum_conf"] / b["count"]
                ece += (b["count"] / total_count) * abs(bin_acc - bin_conf)

        # Brier Score calculation: sum((p_i - o_i)^2) / N
        brier = sum(( (confidences[i]/100.0) - outcomes[i] )**2 for i in range(total_count)) / total_count

        avg_conf = sum(confidences) / len(confidences)
        avg_suc = (sum(outcomes) / len(outcomes)) * 100.0
        drift = avg_conf - avg_suc

        # Distribution percentages
        dist = {}
        for idx, b in bins.items():
            dist[f"{idx*10}-{(idx+1)*10}%"] = round((b["count"] / total_count) * 100, 1)

        return {
            "predicted_confidence": round(avg_conf, 1),
            "actual_success_rate": round(avg_suc, 1),
            "calibration_error": round(ece, 4),
            "brier_score": round(brier, 4),
            "confidence_distribution": dist,
            "confidence_drift": round(drift, 1),
        }
