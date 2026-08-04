from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from database import FINAL_STATUSES, Trade, Signal, PaperTrade, get_session
from dto.analytics import KPIDTO

logger = logging.getLogger(__name__)


class KPIService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def get_kpis(self) -> list[KPIDTO]:
        session = self.session_factory()
        try:
            results = (
                session.query(Trade, PaperTrade)
                .outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
                .all()
            )
            signals = session.query(Signal).all()
            return self._compute(results, signals)
        finally:
            session.close()

    def _compute(self, trades_data: list[Any], signals: Optional[list[Signal]] = None) -> list[KPIDTO]:
        parsed_trades = []
        for item in trades_data:
            if isinstance(item, Trade):
                t, pt = item, None
            else:
                try:
                    t, pt = item
                except (TypeError, ValueError):
                    t, pt = item, None

            qty = float(pt.quantity) if (pt is not None and pt.quantity is not None) else 1.0
            pnl_val = (t.pnl or 0.0) * qty
            parsed_trades.append({
                "trade": t,
                "quantity": qty,
                "pnl_val": pnl_val,
            })

        closed = [item for item in parsed_trades if item["trade"].status in FINAL_STATUSES]
        open_t = [item for item in parsed_trades if item["trade"].status == "OPEN"]
        wins = [item for item in closed if item["pnl_val"] > 0]
        losses = [item for item in closed if item["pnl_val"] < 0]

        total_pnl = sum(item["pnl_val"] for item in closed)
        open_pnl = sum(item["pnl_val"] for item in open_t)
        gp = sum(item["pnl_val"] for item in wins)
        gl = abs(sum(item["pnl_val"] for item in losses))
        pf = gp / gl if gl > 0 else (999.99 if gp > 0 else 0.0)
        pnls = [item["pnl_val"] for item in closed]
        sharpe = self._sharpe(pnls)
        avg_pnl = total_pnl / len(closed) if closed else 0.0
        wr = (len(wins) / len(closed) * 100) if closed else 0.0
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

    def _max_drawdown(self, trades: list[dict[str, Any]]) -> float:
        import datetime
        def get_date(item):
            dt = item["trade"].created_at
            if dt is None:
                return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=datetime.timezone.utc)
            return dt

        sorted_trades = sorted(trades, key=get_date)
        peak = 0.0
        max_dd = 0.0
        running = 0.0
        for item in sorted_trades:
            running += item["pnl_val"]
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
