from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from database import Trade, get_session
from dto.analytics import (
    AnalyticsDTO,
    DailyAnalyticsDTO,
    DrawdownAnalyticsDTO,
    HeatmapDataDTO,
    KPIDTO,
    MonthlyAnalyticsDTO,
    PerformanceTrendDTO,
    RiskAnalyticsDTO,
    StrategyAnalyticsDTO,
    SymbolAnalyticsDTO,
    WeeklyAnalyticsDTO,
    WinLossAnalyticsDTO,
)

logger = logging.getLogger(__name__)

_CLOSED_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})


class AnalyticsService:
    """Comprehensive analytics engine for trading performance analysis."""

    def __init__(
        self,
        session_factory: Optional[Callable[[], Any]] = None,
        portfolio_engine: Optional[Any] = None,
        performance_engine: Optional[Any] = None,
    ):
        self.session_factory = session_factory or get_session
        self._portfolio = portfolio_engine
        self._performance = performance_engine

    def full_analytics(self, limit: int = 1000) -> AnalyticsDTO:
        session = self.session_factory()
        try:
            trades = (
                session.query(Trade)
                .order_by(Trade.created_at.desc())
                .limit(limit)
                .all()
            )
            return AnalyticsDTO(
                daily=self._daily_analytics(trades),
                weekly=self._weekly_analytics(trades),
                monthly=self._monthly_analytics(trades),
                win_loss=self._win_loss_analytics(trades),
                by_symbol=self._symbol_analytics(trades),
                by_strategy=self._strategy_analytics(trades),
                risk=self._risk_analytics(trades, session),
                drawdown=self._drawdown_analytics(trades),
                heatmap=self._heatmap_data(trades),
                trends=self._performance_trends(trades),
                kpis=self._compute_kpis(trades),
            )
        finally:
            session.close()

    def _daily_analytics(self, trades: list[Trade]) -> list[DailyAnalyticsDTO]:
        daily: dict[str, list[Trade]] = defaultdict(list)
        for t in trades:
            if t.created_at:
                day = t.created_at.strftime("%Y-%m-%d") if hasattr(t.created_at, "strftime") else str(t.created_at)[:10]
                daily[day].append(t)

        result = []
        for day in sorted(daily.keys(), reverse=True)[:30]:
            day_trades = daily[day]
            closed = [t for t in day_trades if t.status in _CLOSED_STATUSES]
            wins = [t for t in closed if t.pnl and t.pnl > 0]
            losses = [t for t in closed if t.pnl and t.pnl < 0]
            total_pnl = sum(t.pnl or 0 for t in closed)
            result.append(DailyAnalyticsDTO(
                date=day,
                total_trades=len(day_trades),
                wins=len(wins),
                losses=len(losses),
                win_rate=round((len(wins) / len(closed) * 100), 1) if closed else 0,
                pnl=round(total_pnl, 2),
                avg_pnl=round(total_pnl / len(closed), 2) if closed else 0,
            ))
        return result

    def _weekly_analytics(self, trades: list[Trade]) -> list[WeeklyAnalyticsDTO]:
        weekly: dict[str, list[Trade]] = defaultdict(list)
        for t in trades:
            if t.created_at:
                iso = t.created_at.isocalendar() if hasattr(t.created_at, "isocalendar") else datetime(2024, 1, 1).isocalendar()
                week_key = f"{iso[0]}-W{iso[1]:02d}"
                weekly[week_key].append(t)

        result = []
        for wk in sorted(weekly.keys(), reverse=True)[:12]:
            wk_trades = weekly[wk]
            closed = [t for t in wk_trades if t.status in _CLOSED_STATUSES]
            wins = [t for t in closed if t.pnl and t.pnl > 0]
            losses = [t for t in closed if t.pnl and t.pnl < 0]
            total_pnl = sum(t.pnl or 0 for t in closed)
            result.append(WeeklyAnalyticsDTO(
                week=wk,
                total_trades=len(wk_trades),
                wins=len(wins),
                losses=len(losses),
                win_rate=round((len(wins) / len(closed) * 100), 1) if closed else 0,
                pnl=round(total_pnl, 2),
                avg_pnl=round(total_pnl / len(closed), 2) if closed else 0,
            ))
        return result

    def _monthly_analytics(self, trades: list[Trade]) -> list[MonthlyAnalyticsDTO]:
        monthly: dict[str, list[Trade]] = defaultdict(list)
        for t in trades:
            if t.created_at:
                month_key = t.created_at.strftime("%Y-%m") if hasattr(t.created_at, "strftime") else str(t.created_at)[:7]
                monthly[month_key].append(t)

        result = []
        for mo in sorted(monthly.keys(), reverse=True)[:12]:
            mo_trades = monthly[mo]
            closed = [t for t in mo_trades if t.status in _CLOSED_STATUSES]
            wins = [t for t in closed if t.pnl and t.pnl > 0]
            losses = [t for t in closed if t.pnl and t.pnl < 0]
            total_pnl = sum(t.pnl or 0 for t in closed)
            result.append(MonthlyAnalyticsDTO(
                month=mo,
                total_trades=len(mo_trades),
                wins=len(wins),
                losses=len(losses),
                win_rate=round((len(wins) / len(closed) * 100), 1) if closed else 0,
                pnl=round(total_pnl, 2),
                avg_pnl=round(total_pnl / len(closed), 2) if closed else 0,
            ))
        return result

    def _win_loss_analytics(self, trades: list[Trade]) -> WinLossAnalyticsDTO:
        closed = [t for t in trades if t.status in _CLOSED_STATUSES]
        wins = [t for t in closed if t.pnl and t.pnl > 0]
        losses = [t for t in closed if t.pnl and t.pnl < 0]
        total_closed = len(closed)

        if not closed:
            return WinLossAnalyticsDTO()

        gross_profit = sum(t.pnl or 0 for t in wins)
        gross_loss = abs(sum(t.pnl or 0 for t in losses))

        return WinLossAnalyticsDTO(
            total_wins=len(wins),
            total_losses=len(losses),
            win_rate=round((len(wins) / total_closed * 100), 1) if total_closed else 0,
            avg_win=round((sum(t.pnl or 0 for t in wins) / len(wins)), 2) if wins else 0,
            avg_loss=round((abs(sum(t.pnl or 0 for t in losses)) / len(losses)), 2) if losses else 0,
            largest_win=round(max(t.pnl or 0 for t in wins), 2) if wins else 0,
            largest_loss=round(min(t.pnl or 0 for t in losses), 2) if losses else 0,
            gross_profit=round(gross_profit, 2),
            gross_loss=round(gross_loss, 2),
            profit_factor=round(gross_profit / gross_loss, 2) if gross_loss > 0 else (999.99 if gross_profit > 0 else 0),
            avg_holding_time_win=0.0,
            avg_holding_time_loss=0.0,
        )

    def _symbol_analytics(self, trades: list[Trade]) -> list[SymbolAnalyticsDTO]:
        by_symbol: dict[str, list[Trade]] = defaultdict(list)
        for t in trades:
            by_symbol[t.symbol or "UNKNOWN"].append(t)

        result = []
        for symbol, sym_trades in sorted(by_symbol.items()):
            closed = [t for t in sym_trades if t.status in _CLOSED_STATUSES]
            wins = [t for t in closed if t.pnl and t.pnl > 0]
            losses = [t for t in closed if t.pnl and t.pnl < 0]
            total_pnl = sum(t.pnl or 0 for t in closed)
            gross_profit = sum(t.pnl or 0 for t in wins)
            gross_loss = abs(sum(t.pnl or 0 for t in losses))
            result.append(SymbolAnalyticsDTO(
                symbol=symbol,
                total_trades=len(closed),
                wins=len(wins),
                losses=len(losses),
                win_rate=round((len(wins) / len(closed) * 100), 1) if closed else 0,
                total_pnl=round(total_pnl, 2),
                avg_pnl=round(total_pnl / len(closed), 2) if closed else 0,
                profit_factor=round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0,
            ))
        return sorted(result, key=lambda x: x.total_pnl, reverse=True)

    def _strategy_analytics(self, trades: list[Trade]) -> list[StrategyAnalyticsDTO]:
        by_side: dict[str, list[Trade]] = defaultdict(list)
        for t in trades:
            side = t.side or "UNKNOWN"
            by_side[side].append(t)

        result = []
        for strategy, side_trades in by_side.items():
            closed = [t for t in side_trades if t.status in _CLOSED_STATUSES]
            wins = [t for t in closed if t.pnl and t.pnl > 0]
            losses = [t for t in closed if t.pnl and t.pnl < 0]
            total_pnl = sum(t.pnl or 0 for t in closed)
            pnls = [t.pnl or 0 for t in closed]
            sharpe = self._compute_sharpe(pnls)
            dd = self._compute_max_drawdown(pnls)
            result.append(StrategyAnalyticsDTO(
                strategy_name=strategy,
                total_trades=len(closed),
                wins=len(wins),
                losses=len(losses),
                win_rate=round((len(wins) / len(closed) * 100), 1) if closed else 0,
                total_pnl=round(total_pnl, 2),
                avg_pnl=round(total_pnl / len(closed), 2) if closed else 0,
                sharpe=round(sharpe, 4),
                max_drawdown=round(dd, 2),
                overall_score=round(abs(total_pnl) / (dd + 1) if dd > 0 else total_pnl, 4) if total_pnl else 0,
            ))
        return sorted(result, key=lambda x: x.overall_score, reverse=True)

    def _risk_analytics(self, trades: list[Trade], session: Any) -> RiskAnalyticsDTO:
        open_trades = [t for t in trades if t.status == "OPEN"]
        rejected_signals = 0
        rejection_reasons: dict[str, int] = {}
        total_signals = 0

        from database import Signal
        try:
            signals = session.query(Signal).all()
            total_signals = len(signals)
            for s in signals:
                if s.status == "REJECTED":
                    rejected_signals += 1
                    reason = getattr(s, "reason", "UNKNOWN") or "UNKNOWN"
                    rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        except Exception:
            pass

        symbol_exposure: dict[str, float] = {}
        for t in open_trades:
            sym = t.symbol or "UNKNOWN"
            symbol_exposure[sym] = symbol_exposure.get(sym, 0) + (t.entry or 0)

        from config import MAX_OPEN_TRADES, MAX_PORTFOLIO_EXPOSURE, MAX_DAILY_LOSS, MAX_EXPOSURE_PER_SYMBOL

        return RiskAnalyticsDTO(
            max_open_trades=MAX_OPEN_TRADES,
            current_open_trades=len(open_trades),
            symbol_exposure=symbol_exposure,
            portfolio_exposure=round(sum(symbol_exposure.values()), 2),
            max_portfolio_exposure=MAX_PORTFOLIO_EXPOSURE,
            daily_loss=self._daily_loss(trades),
            max_daily_loss=MAX_DAILY_LOSS,
            risk_score=round(len(open_trades) / MAX_OPEN_TRADES, 2) if MAX_OPEN_TRADES > 0 else 0,
            rejection_rate=round((rejected_signals / total_signals * 100), 1) if total_signals > 0 else 0,
            total_rejections=rejected_signals,
            rejection_reasons=rejection_reasons,
        )

    def _drawdown_analytics(self, trades: list[Trade]) -> DrawdownAnalyticsDTO:
        closed = [t for t in trades if t.status in _CLOSED_STATUSES]
        closed_sorted = sorted(closed, key=lambda t: t.created_at or datetime.min)
        pnls = [t.pnl or 0 for t in closed_sorted]

        if not pnls:
            return DrawdownAnalyticsDTO()

        peak = 0.0
        max_dd = 0.0
        cumulative = 0.0
        dd_start = 0.0
        in_drawdown = False
        recovery_count = 0
        total_recovery_time = 0.0
        longest_dd = 0.0
        dd_start_idx = 0

        for i, p in enumerate(pnls):
            cumulative += p
            if cumulative > peak:
                peak = cumulative
                if in_drawdown:
                    recovery_count += 1
                    dd_duration = i - dd_start_idx
                    total_recovery_time += dd_duration
                    longest_dd = max(longest_dd, dd_duration)
                    in_drawdown = False
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
            if dd > 0 and not in_drawdown:
                in_drawdown = True
                dd_start_idx = i

        initial_eq = 10000.0
        max_dd_pct = round((max_dd / peak * 100), 2) if peak > 0 else 0

        from config import ACCOUNT_EQUITY
        current_peak = peak
        current_eq = initial_eq + cumulative
        current_dd = max(0, current_peak - current_eq)
        current_dd_pct = round((current_dd / current_peak * 100), 2) if current_peak > 0 else 0

        return DrawdownAnalyticsDTO(
            max_drawdown=round(max_dd, 2),
            max_drawdown_pct=max_dd_pct,
            current_drawdown=round(current_dd, 2),
            current_drawdown_pct=current_dd_pct,
            recovery_count=recovery_count,
            avg_recovery_time_hours=round((total_recovery_time / recovery_count) / 60, 2) if recovery_count > 0 else 0,
            longest_drawdown_hours=round(longest_dd / 60, 2) if longest_dd > 0 else 0,
        )

    def _heatmap_data(self, trades: list[Trade]) -> list[HeatmapDataDTO]:
        by_symbol_day: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for t in trades:
            if t.created_at and t.pnl is not None:
                sym = t.symbol or "UNKNOWN"
                day = t.created_at.strftime("%Y-%m-%d") if hasattr(t.created_at, "strftime") else "UNKNOWN"
                by_symbol_day[sym][day] += t.pnl

        result = []
        for symbol, days in by_symbol_day.items():
            total_pnl = sum(days.values())
            result.append(HeatmapDataDTO(
                symbol=symbol,
                metric="pnl",
                values=dict(sorted(days.items())),
                intensity=min(1.0, max(0.0, (total_pnl + 1000) / 2000)),
            ))
        return result

    def _performance_trends(self, trades: list[Trade]) -> list[PerformanceTrendDTO]:
        daily_data = self._daily_analytics(trades)
        pnl_values = [d.pnl for d in daily_data]

        direction = "stable"
        change_pct = 0.0
        if len(pnl_values) >= 2:
            first_half = sum(pnl_values[:len(pnl_values)//2])
            second_half = sum(pnl_values[len(pnl_values)//2:])
            if second_half > first_half and first_half != 0:
                direction = "improving"
                change_pct = round((second_half - first_half) / abs(first_half) * 100, 1)
            elif second_half < first_half and first_half != 0:
                direction = "declining"
                change_pct = round((second_half - first_half) / abs(first_half) * 100, 1)

        return [
            PerformanceTrendDTO(
                metric="pnl",
                daily_values=[{"date": d.date, "value": d.pnl} for d in daily_data[:30]],
                weekly_values=[{"week": w.week, "value": w.pnl} for w in self._weekly_analytics(trades)[:12]],
                monthly_values=[{"month": m.month, "value": m.pnl} for m in self._monthly_analytics(trades)[:12]],
                trend_direction=direction,
                change_pct=change_pct,
            )
        ]

    def _compute_kpis(self, trades: list[Trade]) -> list[KPIDTO]:
        closed = [t for t in trades if t.status in _CLOSED_STATUSES]
        wins = [t for t in closed if t.pnl and t.pnl > 0]
        losses = [t for t in closed if t.pnl and t.pnl < 0]
        total_pnl = sum(t.pnl or 0 for t in closed)

        return [
            KPIDTO(name="Total PnL", value=round(total_pnl, 2), unit="USD", trend=self._pnl_trend(trades), status="positive" if total_pnl > 0 else "negative" if total_pnl < 0 else "neutral"),
            KPIDTO(name="Win Rate", value=round((len(wins) / len(closed) * 100), 1) if closed else 0, unit="%", trend="stable", status="good"),
            KPIDTO(name="Total Trades", value=len(closed), unit="count", trend="stable", status="neutral"),
            KPIDTO(name="Avg PnL", value=round(total_pnl / len(closed), 2) if closed else 0, unit="USD", trend="stable", status="neutral"),
            KPIDTO(name="Profit Factor", value=round(self._profit_factor(wins, losses), 2), unit="ratio", trend="stable", status="good"),
            KPIDTO(name="Max Drawdown", value=round(self._compute_max_drawdown([t.pnl or 0 for t in closed]), 2), unit="USD", trend="stable", status="warning"),
        ]

    def _daily_loss(self, trades: list[Trade]) -> float:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
        return round(
            sum(
                abs(t.pnl or 0)
                for t in trades
                if t.pnl and t.pnl < 0
                and t.closed_at is not None
                and t.closed_at >= today
            ),
            2,
        )

    def _pnl_trend(self, trades: list[Trade]) -> str:
        daily = self._daily_analytics(trades)
        recent = [d.pnl for d in daily[:7]]
        if len(recent) < 2:
            return "stable"
        recent_avg = sum(recent) / len(recent)
        if recent_avg > 0:
            return "improving"
        elif recent_avg < 0:
            return "declining"
        return "stable"

    def _profit_factor(self, wins: list[Trade], losses: list[Trade]) -> float:
        gp = sum(t.pnl or 0 for t in wins)
        gl = abs(sum(t.pnl or 0 for t in losses))
        return gp / gl if gl > 0 else (999.99 if gp > 0 else 0)

    def _compute_sharpe(self, pnls: list[float]) -> float:
        if len(pnls) < 2:
            return 0.0
        import statistics
        mean = statistics.mean(pnls)
        std = statistics.stdev(pnls)
        return (mean / std) if std > 0 else 0.0

    def _compute_max_drawdown(self, pnls: list[float]) -> float:
        if not pnls:
            return 0.0
        peak = 0.0
        max_dd = 0.0
        cumulative = 0.0
        for p in pnls:
            cumulative += p
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        return max_dd
