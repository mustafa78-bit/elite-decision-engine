from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TrustMetrics:
    """Calculate performance-based trust metrics and a dynamic Trust Score from Decision Ledger."""

    def __init__(self, ledger: Optional[Any] = None) -> None:
        from decision.kernel.DecisionLedger import DecisionLedger
        self.ledger = ledger or DecisionLedger()

    def calculate_trust(self) -> dict[str, Any]:
        """Evaluate mathematical trust metrics from all logged outcomes."""
        records = self.ledger.get_all_records()
        completed = [r for r in records if r.get("outcome") is not None]

        if not completed:
            return {
                "win_rate": 0.0,
                "loss_rate": 0.0,
                "average_return": 0.0,
                "expected_return": 0.0,
                "realized_return": 0.0,
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "prediction_accuracy": 0.0,
                "decision_accuracy": 0.0,
                "trust_score": 0.85,  # neutral default starting trust
            }

        pnls = []
        wins = 0
        losses = 0

        for r in completed:
            p = r["outcome"].get("pnl", 0.0)
            suc = r["outcome"].get("success", False)
            pnls.append(p)
            if p > 0 or suc:
                wins += 1
            else:
                losses += 1

        total = len(completed)
        win_rate = wins / total
        loss_rate = losses / total

        avg_return = sum(pnls) / total
        realized_return = sum(pnls)

        # Expected Return = (Win Probability * Avg Win PnL) - (Loss Probability * Avg Loss PnL)
        win_pnls = [p for p in pnls if p > 0]
        loss_pnls = [abs(p) for p in pnls if p <= 0]
        avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0.0
        avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0.0
        exp_return = (win_rate * avg_win) - (loss_rate * avg_loss)

        # Volatility & Sharpe Approximation
        pnl_variance = sum((p - avg_return) ** 2 for p in pnls) / total
        pnl_std = pnl_variance ** 0.5
        sharpe = (avg_return / pnl_std * (365 ** 0.5)) if pnl_std > 0 else 0.0

        # Max Drawdown Approximation
        peak = 0.0
        current_balance = 0.0
        max_dd = 0.0
        for p in pnls:
            current_balance += p
            if current_balance > peak:
                peak = current_balance
            dd = peak - current_balance
            if dd > max_dd:
                max_dd = dd

        # Accuracy parameters
        pred_acc = sum(1.0 for r in completed if r["outcome"].get("success", False)) / total
        dec_acc = sum(1.0 for r in completed if r.get("decision") in ("APPROVE", "STRONG_APPROVE") and r["outcome"].get("success", False)) / max(1, len([r for r in completed if r.get("decision") in ("APPROVE", "STRONG_APPROVE")]))

        # dynamic calculated Trust Score (0.0 - 1.0)
        # Trust score is calculated. Never manually assigned!
        trust_score = (win_rate * 0.4) + (min(1.0, max(0.0, sharpe / 3.0)) * 0.3) + (pred_acc * 0.3)
        trust_score = max(0.0, min(1.0, trust_score))

        return {
            "win_rate": round(win_rate * 100, 1),
            "loss_rate": round(loss_rate * 100, 1),
            "average_return": round(avg_return, 4),
            "expected_return": round(exp_return, 4),
            "realized_return": round(realized_return, 4),
            "sharpe": round(sharpe, 2),
            "max_drawdown": round(max_dd, 4),
            "prediction_accuracy": round(pred_acc, 2),
            "decision_accuracy": round(dec_acc, 2),
            "trust_score": round(trust_score, 2),
        }
