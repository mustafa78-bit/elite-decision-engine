from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from database import Trade, get_session

logger = logging.getLogger(__name__)


@dataclass
class StrategyComparison:
    name: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe: float = 0.0


@dataclass
class BestConditions:
    regime: str = ""
    volatility_class: str = ""
    trend: str = ""
    win_rate: float = 0.0
    total_trades: int = 0


@dataclass
class FailureAnalysis:
    common_regime: str = ""
    common_side: str = ""
    avg_loss: float = 0.0
    total_losses: int = 0
    top_reasons: list[str] = field(default_factory=list)


class PerformanceIntelligence:
    """Analyze trade performance with strategy comparison, best conditions, and failure analysis."""

    def __init__(self, session_factory: Callable[[], Any] | None = None,
                 session: Session | None = None) -> None:
        self.session_factory = session_factory or get_session
        self._session = session

    def analyze(self, limit: int = 500) -> dict[str, Any]:
        """Run full performance intelligence analysis."""
        if self._session is not None:
            trades = self._session.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
        else:
            session = self.session_factory()
            try:
                trades = session.query(Trade).order_by(Trade.created_at.desc()).limit(limit).all()
            finally:
                session.close()

        if not trades:
            return {"strategy_comparison": [], "best_conditions": [], "failure_analysis": {}, "summary": {}}

        closed = [t for t in trades if t.status in ("CLOSED", "TP_HIT", "SL_HIT")]
        wins = [t for t in closed if t.pnl and t.pnl > 0]
        losses = [t for t in closed if t.pnl and t.pnl < 0]

        return {
            "strategy_comparison": self._compare_strategies(trades),
            "best_conditions": self._find_best_conditions(trades),
            "failure_analysis": self._analyze_failures(losses),
            "summary": self._summary(trades, closed, wins, losses),
        }

    def _compare_strategies(self, trades: list[Trade]) -> list[dict[str, Any]]:
        groups: dict[str, list[Trade]] = {}
        for t in trades:
            side = str(t.side or "UNKNOWN")
            if side not in groups:
                groups[side] = []
            groups[side].append(t)

        comparisons: list[dict[str, Any]] = []
        for name, group in groups.items():
            closed = [t for t in group if t.status in ("CLOSED", "TP_HIT", "SL_HIT")]
            wins = [t for t in closed if t.pnl and t.pnl > 0]
            losses = [t for t in closed if t.pnl and t.pnl < 0]
            pnls = [t.pnl or 0 for t in closed]

            comparisons.append({
                "name": name,
                "total_trades": len(closed),
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": round((len(wins) / len(closed) * 100), 1) if closed else 0,
                "total_pnl": round(sum(t.pnl or 0 for t in group), 2),
                "avg_pnl": round(sum(pnls) / len(pnls), 2) if pnls else 0,
                "max_drawdown": round(self._max_drawdown(pnls), 2),
                "sharpe": round(self._sharpe(pnls), 4),
            })

        return sorted(comparisons, key=lambda x: x["win_rate"], reverse=True)

    def _find_best_conditions(self, trades: list[Trade]) -> list[dict[str, Any]]:
        closed = [t for t in trades if t.status in ("CLOSED", "TP_HIT", "SL_HIT")]
        if not closed:
            return []

        conditions: dict[str, dict[str, Any]] = {}
        for t in closed:
            key = str(t.close_reason or "UNKNOWN")
            if key not in conditions:
                conditions[key] = {"condition": key, "total": 0, "wins": 0, "total_pnl": 0.0}
            conditions[key]["total"] += 1
            if t.pnl and t.pnl > 0:
                conditions[key]["wins"] += 1
            conditions[key]["total_pnl"] += t.pnl or 0

        result = []
        for key, data in conditions.items():
            data["win_rate"] = round((data["wins"] / data["total"]) * 100, 1) if data["total"] > 0 else 0
            data["avg_pnl"] = round(data["total_pnl"] / data["total"], 2) if data["total"] > 0 else 0
            result.append(data)

        return sorted(result, key=lambda x: x["win_rate"], reverse=True)[:5]

    def _analyze_failures(self, losses: list[Trade]) -> dict[str, Any]:
        if not losses:
            return {"common_regime": "N/A", "common_side": "N/A", "avg_loss": 0.0, "total_losses": 0, "top_reasons": []}

        sides: dict[str, int] = {}
        reasons: dict[str, int] = {}
        total_loss = 0.0

        for t in losses:
            side = str(t.side or "UNKNOWN")
            sides[side] = sides.get(side, 0) + 1
            reason = str(t.close_reason or "UNKNOWN")
            reasons[reason] = reasons.get(reason, 0) + 1
            total_loss += abs(t.pnl or 0)

        top_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:3]
        common_side = max(sides, key=sides.get) if sides else "N/A"

        return {
            "common_regime": "N/A",
            "common_side": common_side,
            "avg_loss": round(total_loss / len(losses), 2),
            "total_losses": len(losses),
            "top_reasons": [{"reason": r, "count": c} for r, c in top_reasons],
        }

    def _summary(self, trades: list[Trade], closed: list[Trade], wins: list[Trade], losses: list[Trade]) -> dict[str, Any]:
        pnls = [t.pnl or 0 for t in closed]
        return {
            "total_trades": len(trades),
            "closed_trades": len(closed),
            "open_trades": len(trades) - len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round((len(wins) / len(closed) * 100), 1) if closed else 0,
            "total_pnl": round(sum(t.pnl or 0 for t in trades), 2),
            "avg_pnl": round(sum(pnls) / len(pnls), 2) if pnls else 0,
            "max_drawdown": round(self._max_drawdown(pnls), 2),
            "sharpe": round(self._sharpe(pnls), 4),
            "profit_factor": self._profit_factor(wins, losses),
        }

    def _max_drawdown(self, pnls: list[float]) -> float:
        if not pnls:
            return 0.0
        running_max = 0.0
        max_dd = 0.0
        cumulative = 0.0
        for p in pnls:
            cumulative += p
            if cumulative > running_max:
                running_max = cumulative
            dd = running_max - cumulative
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def _sharpe(self, pnls: list[float]) -> float:
        if len(pnls) < 2:
            return 0.0
        import statistics
        mean = statistics.mean(pnls)
        std = statistics.stdev(pnls)
        return (mean / std) if std > 0 else 0.0

    def _profit_factor(self, wins: list[Trade], losses: list[Trade]) -> float:
        gross_win = sum(t.pnl or 0 for t in wins)
        gross_loss = abs(sum(t.pnl or 0 for t in losses))
        return round(gross_win / gross_loss, 2) if gross_loss > 0 else 0.0
