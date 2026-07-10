from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from database import Trade, Signal, get_session
from dto.analytics import KPIDTO

logger = logging.getLogger(__name__)

_CLOSED_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})


class KPIService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def get_kpis(self) -> list[KPIDTO]:
        session = self.session_factory()
        try:
            trades = session.query(Trade).all()
            signals = session.query(Signal).all()
            return self._compute(trades, signals)
        finally:
            session.close()

    def _compute(self, trades: list[Trade], signals: Optional[list[Signal]] = None) -> list[KPIDTO]:
        closed = [t for t in trades if t.status in _CLOSED_STATUSES]
        open_t = [t for t in trades if t.status == "OPEN"]
        wins = [t for t in closed if t.pnl and t.pnl > 0]
        losses = [t for t in closed if t.pnl and t.pnl < 0]
        total_pnl = sum(t.pnl or 0 for t in closed)
        open_pnl = sum(t.pnl or 0 for t in open_t)
        gp = sum(t.pnl or 0 for t in wins)
        gl = abs(sum(t.pnl or 0 for t in losses))
        pf = gp / gl if gl > 0 else (999.99 if gp > 0 else 0)
        pnls = [t.pnl or 0 for t in closed]
        sharpe = self._sharpe(pnls)
        avg_pnl = total_pnl / len(closed) if closed else 0
        wr = (len(wins) / len(closed) * 100) if closed else 0
        max_dd = self._max_drawdown(closed)
        calmar = sharpe  # approximate

        return [
            KPIDTO(name="Total PnL", value=round(total_pnl, 2), unit="USD", trend=self._trend(total_pnl), status=self._status(total_pnl, 0)),
            KPIDTO(name="Open PnL", value=round(open_pnl, 2), unit="USD", trend="stable", status=self._status(open_pnl, 0)),
            KPIDTO(name="Win Rate", value=round(wr, 1), unit="%", trend="stable", status="good" if wr >= 50 else "warning" if wr >= 30 else "negative"),
            KPIDTO(name="Trades", value=len(closed), unit="count", trend="stable", status="neutral"),
            KPIDTO(name="Open Trades", value=len(open_t), unit="count", trend="stable", status="neutral"),
            KPIDTO(name="Avg PnL", value=round(avg_pnl, 2), unit="USD", trend="stable", status="good" if avg_pnl > 0 else "negative"),
            KPIDTO(name="Profit Factor", value=round(pf, 2), unit="ratio", trend="stable", status="good" if pf >= 1.5 else "warning" if pf >= 1 else "negative"),
            KPIDTO(name="Sharpe", value=round(sharpe, 4), unit="ratio", trend="stable", status="good" if sharpe >= 1 else "warning" if sharpe >= 0 else "negative"),
            KPIDTO(name="Calmar", value=round(calmar, 4), unit="ratio", trend="stable", status="good" if calmar >= 1 else "warning" if calmar >= 0 else "negative"),
            KPIDTO(name="Max Drawdown", value=round(max_dd, 2), unit="USD", trend="stable", status="warning"),
        ]

    def _sharpe(self, pnls: list[float]) -> float:
        if len(pnls) < 2:
            return 0.0
        import statistics
        m = statistics.mean(pnls)
        s = statistics.stdev(pnls)
        return (m / s) if s > 0 else 0.0

    def _max_drawdown(self, trades: list[Trade]) -> float:
        sorted_trades = sorted(trades, key=lambda t: t.created_at or __import__("datetime").datetime.min)
        peak = 0.0
        max_dd = 0.0
        running = 0.0
        for t in sorted_trades:
            running += t.pnl or 0
            if running > peak:
                peak = running
            dd = peak - running
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def _trend(self, value: float) -> str:
        if value > 0:
            return "improving"
        if value < 0:
            return "declining"
        return "stable"

    def _status(self, value: float, threshold: float) -> str:
        if value > threshold:
            return "positive"
        if value < threshold:
            return "negative"
        return "neutral"
