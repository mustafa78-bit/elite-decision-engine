from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from database import Trade, FINAL_STATUSES, get_session

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session

    def summary(self) -> dict[str, Any]:
        session = self.session_factory()
        try:
            trades = session.query(Trade).all()
            return self._compute_summary(trades)
        finally:
            session.close()

    def distribution(self) -> dict[str, Any]:
        session = self.session_factory()
        try:
            trades = session.query(Trade).all()
            return self._compute_distribution(trades)
        finally:
            session.close()

    def performance(self) -> dict[str, Any]:
        session = self.session_factory()
        try:
            trades = session.query(Trade).all()
            return self._compute_performance(trades)
        finally:
            session.close()

    def risk_metrics(self) -> dict[str, Any]:
        session = self.session_factory()
        try:
            trades = session.query(Trade).all()
            return self._compute_risk(trades)
        finally:
            session.close()

    def full_portfolio(self) -> dict[str, Any]:
        session = self.session_factory()
        try:
            trades = session.query(Trade).all()
            return {
                "summary": self._compute_summary(trades),
                "distribution": self._compute_distribution(trades),
                "performance": self._compute_performance(trades),
                "risk": self._compute_risk(trades),
            }
        finally:
            session.close()

    def _compute_summary(self, trades: list[Trade]) -> dict[str, Any]:
        closed = [t for t in trades if t.status in FINAL_STATUSES]
        open_trades = [t for t in trades if t.status == "OPEN"]
        wins = [t for t in closed if t.pnl and t.pnl > 0]
        losses = [t for t in closed if t.pnl and t.pnl < 0]
        total_pnl = sum(t.pnl or 0 for t in closed)
        open_pnl = sum(t.pnl or 0 for t in open_trades)
        gp = sum(t.pnl or 0 for t in wins)
        gl = abs(sum(t.pnl or 0 for t in losses))
        pf = gp / gl if gl > 0 else (999.99 if gp > 0 else 0)
        wr = (len(wins) / len(closed) * 100) if closed else 0
        pnls = [t.pnl or 0 for t in closed]
        sharpe = self._sharpe(pnls)
        max_dd = self._max_drawdown(trades)
        current_dd = self._current_drawdown(trades)
        best = max((t.pnl or 0) for t in closed) if closed else 0
        worst = min((t.pnl or 0) for t in closed) if closed else 0
        avg_dur = self._avg_duration(closed)
        return {
            "total_balance": 0.0,
            "open_pnl": round(open_pnl, 2),
            "realized_pnl": round(total_pnl, 2),
            "total_pnl": round(total_pnl + open_pnl, 2),
            "total_trades": len(closed),
            "open_trades": len(open_trades),
            "win_rate": round(wr, 1),
            "profit_factor": round(pf, 2),
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown": round(max_dd, 2),
            "current_drawdown": round(current_dd, 2),
            "avg_trade_duration": avg_dur,
            "best_trade_pnl": round(best, 2),
            "worst_trade_pnl": round(worst, 2),
        }

    def _compute_distribution(self, trades: list[Trade]) -> dict[str, Any]:
        closed = [t for t in trades if t.status in FINAL_STATUSES]
        by_symbol: dict[str, list[Trade]] = {}
        for t in closed:
            by_symbol.setdefault(t.symbol or "?", []).append(t)
        symbol_data = []
        for sym, sts in sorted(by_symbol.items()):
            sw = [t for t in sts if t.pnl and t.pnl > 0]
            spnl = sum(t.pnl or 0 for t in sts)
            symbol_data.append({
                "symbol": sym, "trades": len(sts), "wins": len(sw),
                "pnl": round(spnl, 2),
                "win_rate": round(len(sw) / len(sts) * 100, 1),
            })
        long_count = sum(1 for t in closed if t.side and t.side.upper() == "LONG")
        short_count = sum(1 for t in closed if t.side and t.side.upper() == "SHORT")
        return {
            "by_symbol": symbol_data,
            "by_side": {"LONG": long_count, "SHORT": short_count},
        }

    def _compute_performance(self, trades: list[Trade]) -> dict[str, Any]:
        closed = [t for t in trades if t.status in FINAL_STATUSES]
        equity = self._equity_curve(closed)
        monthly = self._monthly_pnl(closed)
        daily = self._daily_pnl(closed)
        dd = self._drawdown_curve(closed)
        return {
            "equity_curve": equity,
            "monthly_pnl": monthly,
            "daily_pnl": daily,
            "drawdown_curve": dd,
        }

    def _compute_risk(self, trades: list[Trade]) -> dict[str, Any]:
        open_trades = [t for t in trades if t.status == "OPEN"]
        closed = [t for t in trades if t.status in FINAL_STATUSES]
        total_exposure = sum(abs(t.pnl or 0) for t in open_trades)
        pnls = [t.pnl or 0 for t in closed]
        var95 = self._value_at_risk(pnls, 0.95)
        downside = self._expected_downside(pnls)
        gp = sum(t.pnl or 0 for t in closed if t.pnl and t.pnl > 0)
        gl = abs(sum(t.pnl or 0 for t in closed if t.pnl and t.pnl < 0))
        md = self._max_drawdown(trades)
        rf = gp / md if md > 0 else 0
        by_sym: dict[str, float] = {}
        for t in open_trades:
            sym = t.symbol or "?"
            by_sym[sym] = by_sym.get(sym, 0) + abs(t.pnl or 0)
        total = sum(by_sym.values()) or 1
        concentration = {s: round(v / total, 4) for s, v in by_sym.items()}
        return {
            "current_exposure": round(total_exposure, 2),
            "max_exposure": round(max(total_exposure, 0), 2),
            "symbol_concentration": concentration,
            "risk_per_trade": round(self._avg_risk_per_trade(closed), 2),
            "var_95": round(var95, 2),
            "expected_downside": round(downside, 2),
            "recovery_factor": round(rf, 4),
        }

    def _sharpe(self, pnls: list[float]) -> float:
        if len(pnls) < 2:
            return 0.0
        import statistics
        m = statistics.mean(pnls)
        s = statistics.stdev(pnls)
        return (m / s) if s > 0 else 0.0

    def _max_drawdown(self, trades: list[Trade]) -> float:
        closed = [t for t in trades if t.status in FINAL_STATUSES]
        sorted_trades = sorted(closed, key=lambda t: t.created_at or datetime.min.replace(tzinfo=timezone.utc))
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

    def _current_drawdown(self, trades: list[Trade]) -> float:
        closed = [t for t in trades if t.status in FINAL_STATUSES]
        sorted_trades = sorted(closed, key=lambda t: t.created_at or datetime.min.replace(tzinfo=timezone.utc))
        peak = 0.0
        running = 0.0
        for t in sorted_trades:
            running += t.pnl or 0
            if running > peak:
                peak = running
        return peak - running

    def _equity_curve(self, trades: list[Trade]) -> list[dict[str, Any]]:
        sorted_trades = sorted(trades, key=lambda t: t.created_at or datetime.min.replace(tzinfo=timezone.utc))
        curve = []
        running = 0.0
        for t in sorted_trades:
            running += t.pnl or 0
            ts = t.closed_at or t.created_at
            curve.append({
                "timestamp": ts.isoformat() if ts else None,
                "equity": round(running, 2),
            })
        return curve

    def _monthly_pnl(self, trades: list[Trade]) -> list[dict[str, Any]]:
        monthly: dict[str, float] = {}
        for t in trades:
            ts = t.closed_at or t.created_at
            if ts:
                key = ts.strftime("%Y-%m")
                monthly[key] = monthly.get(key, 0) + (t.pnl or 0)
        return [{"month": k, "pnl": round(v, 2)} for k, v in sorted(monthly.items())]

    def _daily_pnl(self, trades: list[Trade]) -> list[dict[str, Any]]:
        daily: dict[str, float] = {}
        for t in trades:
            ts = t.closed_at or t.created_at
            if ts:
                key = ts.strftime("%Y-%m-%d")
                daily[key] = daily.get(key, 0) + (t.pnl or 0)
        return [{"date": k, "pnl": round(v, 2)} for k, v in sorted(daily.items())]

    def _drawdown_curve(self, trades: list[Trade]) -> list[dict[str, Any]]:
        sorted_trades = sorted(trades, key=lambda t: t.created_at or datetime.min.replace(tzinfo=timezone.utc))
        curve = []
        peak = 0.0
        running = 0.0
        for t in sorted_trades:
            running += t.pnl or 0
            if running > peak:
                peak = running
            dd = peak - running
            curve.append({
                "timestamp": (t.closed_at or t.created_at).isoformat() if (t.closed_at or t.created_at) else None,
                "drawdown": round(dd, 2),
            })
        return curve

    def _value_at_risk(self, pnls: list[float], confidence: float = 0.95) -> float:
        if not pnls:
            return 0.0
        sorted_pnls = sorted(pnls)
        idx = int(len(sorted_pnls) * (1 - confidence))
        return sorted_pnls[min(idx, len(sorted_pnls) - 1)]

    def _expected_downside(self, pnls: list[float]) -> float:
        negatives = [p for p in pnls if p < 0]
        if not negatives:
            return 0.0
        return sum(negatives) / len(negatives)

    def _avg_risk_per_trade(self, trades: list[Trade]) -> float:
        entries = [abs(t.entry or 0) for t in trades if t.entry]
        if not entries:
            return 0.0
        return sum(entries) / len(entries)

    def _avg_duration(self, trades: list[Trade]) -> Optional[str]:
        durations = []
        for t in trades:
            if t.created_at and t.closed_at:
                dur = (t.closed_at - t.created_at).total_seconds()
                durations.append(dur)
        if not durations:
            return None
        avg_sec = sum(durations) / len(durations)
        hours = int(avg_sec // 3600)
        mins = int((avg_sec % 3600) // 60)
        return f"{hours}h {mins}m"
