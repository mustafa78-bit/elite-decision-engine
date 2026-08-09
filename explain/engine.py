from __future__ import annotations

import logging
from typing import Any, Optional

from explain.core import ExplainInput, ExplainResult

logger = logging.getLogger(__name__)

_BUY_THRESHOLD = 0.55
_SELL_THRESHOLD = 0.55
_HIGH_CONFIDENCE = 75.0
_MEDIUM_CONFIDENCE = 55.0

_DECISION_LABELS = {
    "LONG": "BUY",
    "SHORT": "SELL",
}

_SIGNAL_DIMENSIONS = ["Technical", "Whale", "News", "Risk", "Trend"]


class ExplainEngine:

    def explain(self, inp: ExplainInput) -> ExplainResult:
        decision, confidence = self._compute_decision(inp)
        reasons = self._build_reasons(inp, decision)
        warnings = self._build_warnings(inp)
        supporting = self._supporting_signals(inp)
        risk_notes = self._build_risk_notes(inp)
        summary = self._build_summary(inp, decision, confidence, reasons)

        return ExplainResult(
            decision=decision,
            confidence=round(confidence, 1),
            reasons=reasons,
            warnings=warnings,
            supporting_signals=supporting,
            risk_notes=risk_notes,
            summary=summary,
        )

    def _dimension_scores(self, inp: ExplainInput) -> dict[str, float]:
        return {
            "Technical": inp.technical_score,
            "Whale": inp.whale_score,
            "News": inp.news_score,
            "Risk": inp.risk_score,
            "Trend": inp.trend_score,
        }

    def _compute_decision(
        self, inp: ExplainInput,
    ) -> tuple[str, float]:
        dims = self._dimension_scores(inp)
        values = [v for v in dims.values() if v > 0]

        if values:
            avg_score = sum(values) / len(values)
        else:
            avg_score = 0.0

        portfolio_equity_ratio = (
            inp.portfolio_total_equity / inp.portfolio_initial_capital
            if inp.portfolio_initial_capital > 0
            else 1.0
        )
        sharpe_bonus = max(0.0, min(0.15, inp.performance_sharpe * 0.02))
        pf_bonus = max(0.0, min(0.10, inp.performance_profit_factor * 0.01))
        equity_bonus = max(0.0, min(0.10, (portfolio_equity_ratio - 1.0) * 0.5))

        adjusted = avg_score + sharpe_bonus + pf_bonus + equity_bonus
        adjusted = max(0.0, min(1.0, adjusted))

        side_label = _DECISION_LABELS.get(inp.side, "HOLD")
        if adjusted >= _BUY_THRESHOLD:
            decision = side_label
        elif inp.side == "SHORT" and adjusted >= _SELL_THRESHOLD:
            decision = "SELL"
        else:
            decision = "HOLD"

        base_conf = adjusted * 100.0
        agreement = self._agreement_penalty(dims)
        base_conf *= agreement

        if inp.performance_total_pnl > 0:
            base_conf = min(100.0, base_conf + 5.0)
        if inp.performance_sharpe > 1.5:
            base_conf = min(100.0, base_conf + 5.0)
        if inp.performance_profit_factor > 2.0:
            base_conf = min(100.0, base_conf + 3.0)
        if portfolio_equity_ratio > 1.05:
            base_conf = min(100.0, base_conf + 3.0)
        if inp.portfolio_exposure > inp.portfolio_total_equity * 3:
            base_conf = max(0.0, base_conf - 10.0)

        return decision, base_conf

    def _agreement_penalty(self, dims: dict[str, float]) -> float:
        values = [v for v in dims.values()]
        if len(values) < 2:
            return 1.0
        mean_v = sum(values) / len(values)
        variance = sum((v - mean_v) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        if std_dev > 0.3:
            return 0.80
        if std_dev > 0.2:
            return 0.90
        return 1.0

    def _build_reasons(self, inp: ExplainInput, decision: str) -> list[str]:
        reasons: list[str] = []

        tech_wording = self._score_wording(inp.technical_score)
        if inp.technical_score >= 0.5:
            reasons.append(f"Technical score: {inp.technical_score:.2f} — {tech_wording}")

        trend_wording = self._score_wording(inp.trend_score)
        if inp.trend_score >= 0.5:
            reasons.append(f"Trend score: {inp.trend_score:.2f} — {trend_wording}")

        if inp.whale_score >= 0.5:
            reasons.append(f"Whale activity score: {inp.whale_score:.2f} — supports {decision.lower()}")

        if inp.news_score >= 0.5:
            reasons.append(f"News sentiment score: {inp.news_score:.2f} — favorable")

        risk_wording = self._score_wording(inp.risk_score)
        if inp.risk_score >= 0.5:
            reasons.append(f"Risk score: {inp.risk_score:.2f} — {risk_wording}")
        elif inp.risk_score > 0:
            reasons.append(f"Risk score: {inp.risk_score:.2f} — elevated caution")

        if inp.portfolio_total_equity > 0:
            pnl_label = "profitable" if inp.portfolio_realized_pnl >= 0 else "loss-making"
            reasons.append(
                f"Portfolio equity: ${inp.portfolio_total_equity:,.0f} "
                f"({pnl_label}, exposure ${inp.portfolio_exposure:,.0f})"
            )
        if inp.performance_total_pnl > 0:
            reasons.append(
                f"Performance: Sharpe {inp.performance_sharpe:.2f}, "
                f"Profit factor {inp.performance_profit_factor:.2f}"
            )

        score_reasons = len([r for r in reasons if any(
            d.lower() in r.lower() for d in _SIGNAL_DIMENSIONS
        )])
        if score_reasons == 0:
            reasons.append("Insufficient signal strength from all dimensions")

        return reasons

    def _build_warnings(self, inp: ExplainInput) -> list[str]:
        warnings: list[str] = []

        if inp.risk_score < 0.4:
            warnings.append("Risk score is low — consider reducing position size")

        dims = self._dimension_scores(inp)
        high_dims = [k for k, v in dims.items() if v >= 0.5]
        low_dims = [k for k, v in dims.items() if v < 0.4 and v > 0]
        if len(high_dims) >= 3 and len(low_dims) >= 2:
            warnings.append("Mixed signals — high disagreement between dimensions")

        if inp.portfolio_exposure > inp.portfolio_total_equity * 4:
            warnings.append("Portfolio is over-leveraged — high exposure relative to equity")

        if inp.performance_sharpe < 0.5 and inp.performance_sharpe > 0:
            warnings.append("Historical Sharpe below 0.5 — risk-adjusted returns are weak")

        if inp.performance_profit_factor < 1.0 and inp.performance_profit_factor > 0:
            warnings.append("Profit factor below 1.0 — system is not historically profitable")

        if inp.portfolio_unrealized_pnl < -inp.portfolio_total_equity * 0.1:
            warnings.append("Large unrealized loss — consider reducing open positions")

        return warnings

    def _supporting_signals(self, inp: ExplainInput) -> list[str]:
        dims = self._dimension_scores(inp)
        return [name for name, score in dims.items() if score >= 0.5]

    def _build_risk_notes(self, inp: ExplainInput) -> list[str]:
        notes: list[str] = []

        if inp.risk_score >= 0.7:
            notes.append("Risk profile: LOW")
        elif inp.risk_score >= 0.4:
            notes.append("Risk profile: MODERATE")
        elif inp.risk_score > 0:
            notes.append("Risk profile: ELEVATED")
        else:
            notes.append("Risk profile: UNKNOWN")

        exposure_pct = (
            inp.portfolio_exposure / inp.portfolio_total_equity * 100
            if inp.portfolio_total_equity > 0
            else 0.0
        )
        notes.append(f"Portfolio exposure: {exposure_pct:.0f}% of equity")

        if inp.performance_max_drawdown > 0:
            notes.append(f"Historical max drawdown: {inp.performance_max_drawdown:.1f}%")

        return notes

    def _build_summary(
        self,
        inp: ExplainInput,
        decision: str,
        confidence: float,
        reasons: list[str],
    ) -> str:
        supporting = self._supporting_signals(inp)
        supporting_str = ", ".join(supporting) if supporting else "none"
        return (
            f"{decision} {inp.symbol} with {confidence:.1f}% confidence — "
            f"supported by {supporting_str}"
        )

    def _score_wording(self, score: float) -> str:
        if score >= 0.8:
            return "strong"
        if score >= 0.6:
            return "moderate"
        if score >= 0.4:
            return "neutral"
        if score > 0:
            return "weak"
        return "none"
