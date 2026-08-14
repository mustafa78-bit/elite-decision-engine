from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Optional

from database import FINAL_STATUSES, Trade, get_session
from dto.analytics import (
    KPIDTO,
    AnalyticsDTO,
    DailyAnalyticsDTO,
    DrawdownAnalyticsDTO,
    HeatmapDataDTO,
    MonthlyAnalyticsDTO,
    PerformanceTrendDTO,
    RiskAnalyticsDTO,
    StrategyAnalyticsDTO,
    SymbolAnalyticsDTO,
    WeeklyAnalyticsDTO,
    WinLossAnalyticsDTO,
)
from services.pnl import get_trades_with_dollar_pnl, get_trades_with_exposure

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Comprehensive analytics engine for trading performance analysis."""

    def __init__(
        self,
        session_factory: Callable[[], Any] | None = None,
        portfolio_engine: Any | None = None,
        performance_engine: Any | None = None,
    ):
        self.session_factory = session_factory or get_session
        self._portfolio = portfolio_engine
        self._performance = performance_engine

    def full_analytics(self, limit: int = 1000, user_id: int | None = None) -> AnalyticsDTO:
        session = self.session_factory()
        try:
            filters = ()
            if user_id is not None:
                from sqlalchemy import or_
                filters = (or_(Trade.user_id == user_id, Trade.user_id.is_(None)),)
            trades_with_pnl = get_trades_with_dollar_pnl(session, *filters)

            def get_created_at(t_pnl):
                t = t_pnl[0]
                if not t.created_at:
                    return datetime.min
                if t.created_at.tzinfo is not None:
                    return t.created_at.replace(tzinfo=None)
                return t.created_at

            # Sort by created_at desc and apply limit manually or in python
            trades_with_pnl.sort(key=get_created_at, reverse=True)
            trades_with_pnl = trades_with_pnl[:limit]

            return AnalyticsDTO(
                daily=self._daily_analytics(trades_with_pnl),
                weekly=self._weekly_analytics(trades_with_pnl),
                monthly=self._monthly_analytics(trades_with_pnl),
                win_loss=self._win_loss_analytics(trades_with_pnl),
                by_symbol=self._symbol_analytics(trades_with_pnl),
                by_strategy=self._strategy_analytics(trades_with_pnl),
                risk=self._risk_analytics(trades_with_pnl, session, user_id),
                drawdown=self._drawdown_analytics(trades_with_pnl),
                heatmap=self._heatmap_data(trades_with_pnl),
                trends=self._performance_trends(trades_with_pnl),
                kpis=self._compute_kpis(trades_with_pnl),
            )
        finally:
            session.close()

    def _daily_analytics(self, trades: list[tuple[Trade, float]]) -> list[DailyAnalyticsDTO]:
        daily: dict[str, list[tuple[Trade, float]]] = defaultdict(list)
        for t_pnl in trades:
            t = t_pnl[0]
            if t.created_at:
                day = t.created_at.strftime("%Y-%m-%d") if hasattr(t.created_at, "strftime") else str(t.created_at)[:10]
                daily[day].append(t_pnl)

        result = []
        for day in sorted(daily.keys(), reverse=True)[:30]:
            day_trades = daily[day]
            closed = [t_pnl for t_pnl in day_trades if t_pnl[0].status in FINAL_STATUSES]
            wins = [t_pnl for t_pnl in closed if t_pnl[1] > 0]
            losses = [t_pnl for t_pnl in closed if t_pnl[1] < 0]
            total_pnl = sum(t_pnl[1] for t_pnl in closed)
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

    def _weekly_analytics(self, trades: list[tuple[Trade, float]]) -> list[WeeklyAnalyticsDTO]:
        weekly: dict[str, list[tuple[Trade, float]]] = defaultdict(list)
        for t_pnl in trades:
            t = t_pnl[0]
            if t.created_at:
                iso = t.created_at.isocalendar() if hasattr(t.created_at, "isocalendar") else datetime(2024, 1, 1).isocalendar()
                week_key = f"{iso[0]}-W{iso[1]:02d}"
                weekly[week_key].append(t_pnl)

        result = []
        for wk in sorted(weekly.keys(), reverse=True)[:12]:
            wk_trades = weekly[wk]
            closed = [t_pnl for t_pnl in wk_trades if t_pnl[0].status in FINAL_STATUSES]
            wins = [t_pnl for t_pnl in closed if t_pnl[1] > 0]
            losses = [t_pnl for t_pnl in closed if t_pnl[1] < 0]
            total_pnl = sum(t_pnl[1] for t_pnl in closed)
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

    def _monthly_analytics(self, trades: list[tuple[Trade, float]]) -> list[MonthlyAnalyticsDTO]:
        monthly: dict[str, list[tuple[Trade, float]]] = defaultdict(list)
        for t_pnl in trades:
            t = t_pnl[0]
            if t.created_at:
                month_key = t.created_at.strftime("%Y-%m") if hasattr(t.created_at, "strftime") else str(t.created_at)[:7]
                monthly[month_key].append(t_pnl)

        result = []
        for mo in sorted(monthly.keys(), reverse=True)[:12]:
            mo_trades = monthly[mo]
            closed = [t_pnl for t_pnl in mo_trades if t_pnl[0].status in FINAL_STATUSES]
            wins = [t_pnl for t_pnl in closed if t_pnl[1] > 0]
            losses = [t_pnl for t_pnl in closed if t_pnl[1] < 0]
            total_pnl = sum(t_pnl[1] for t_pnl in closed)
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

    def _win_loss_analytics(self, trades: list[tuple[Trade, float]]) -> WinLossAnalyticsDTO:
        closed = [t_pnl for t_pnl in trades if t_pnl[0].status in FINAL_STATUSES]
        wins = [t_pnl for t_pnl in closed if t_pnl[1] > 0]
        losses = [t_pnl for t_pnl in closed if t_pnl[1] < 0]
        total_closed = len(closed)

        if not closed:
            return WinLossAnalyticsDTO()

        gross_profit = sum(t_pnl[1] for t_pnl in wins)
        gross_loss = abs(sum(t_pnl[1] for t_pnl in losses))

        return WinLossAnalyticsDTO(
            total_wins=len(wins),
            total_losses=len(losses),
            win_rate=round((len(wins) / total_closed * 100), 1) if total_closed else 0,
            avg_win=round((sum(t_pnl[1] for t_pnl in wins) / len(wins)), 2) if wins else 0,
            avg_loss=round((abs(sum(t_pnl[1] for t_pnl in losses)) / len(losses)), 2) if losses else 0,
            largest_win=round(max(t_pnl[1] for t_pnl in wins), 2) if wins else 0,
            largest_loss=round(min(t_pnl[1] for t_pnl in losses), 2) if losses else 0,
            gross_profit=round(gross_profit, 2),
            gross_loss=round(gross_loss, 2),
            profit_factor=round(gross_profit / gross_loss, 2) if gross_loss > 0 else (999.99 if gross_profit > 0 else 0),
            avg_holding_time_win=0.0,
            avg_holding_time_loss=0.0,
        )

    def _symbol_analytics(self, trades: list[tuple[Trade, float]]) -> list[SymbolAnalyticsDTO]:
        by_symbol: dict[str, list[tuple[Trade, float]]] = defaultdict(list)
        for t_pnl in trades:
            by_symbol[t_pnl[0].symbol or "UNKNOWN"].append(t_pnl)

        result = []
        for symbol, sym_trades in sorted(by_symbol.items()):
            closed = [t_pnl for t_pnl in sym_trades if t_pnl[0].status in FINAL_STATUSES]
            wins = [t_pnl for t_pnl in closed if t_pnl[1] > 0]
            losses = [t_pnl for t_pnl in closed if t_pnl[1] < 0]
            total_pnl = sum(t_pnl[1] for t_pnl in closed)
            gross_profit = sum(t_pnl[1] for t_pnl in wins)
            gross_loss = abs(sum(t_pnl[1] for t_pnl in losses))
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

    def _strategy_analytics(self, trades: list[tuple[Trade, float]]) -> list[StrategyAnalyticsDTO]:
        by_side: dict[str, list[tuple[Trade, float]]] = defaultdict(list)
        for t_pnl in trades:
            side = t_pnl[0].side or "UNKNOWN"
            by_side[side].append(t_pnl)

        result = []
        for strategy, side_trades in by_side.items():
            closed = [t_pnl for t_pnl in side_trades if t_pnl[0].status in FINAL_STATUSES]
            wins = [t_pnl for t_pnl in closed if t_pnl[1] > 0]
            losses = [t_pnl for t_pnl in closed if t_pnl[1] < 0]
            total_pnl = sum(t_pnl[1] for t_pnl in closed)
            pnls = [t_pnl[1] for t_pnl in closed]
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

    def _risk_analytics(
        self, trades: list[tuple[Trade, float]], session: Any, user_id: int | None = None,
    ) -> RiskAnalyticsDTO:
        open_trades = [t_pnl for t_pnl in trades if t_pnl[0].status == "OPEN"]
        rejected_signals = 0
        rejection_reasons: dict[str, int] = {}
        total_signals = 0

        from sqlalchemy import or_

        from database import Signal
        try:
            signal_query = session.query(Signal)
            if user_id is not None:
                signal_query = signal_query.filter(
                    or_(Signal.user_id == user_id, Signal.user_id.is_(None))
                )
            signals = signal_query.all()
            total_signals = len(signals)
            for s in signals:
                if s.status == "REJECTED":
                    rejected_signals += 1
                    reason = getattr(s, "reason", "UNKNOWN") or "UNKNOWN"
                    rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        except Exception:
            pass

        exposure_filters = (Trade.status == "OPEN",)
        if user_id is not None:
            exposure_filters = exposure_filters + (
                or_(Trade.user_id == user_id, Trade.user_id.is_(None)),
            )
        open_trades_with_exposure = get_trades_with_exposure(session, *exposure_filters)
        symbol_exposure: dict[str, float] = {}
        for t, exposure in open_trades_with_exposure:
            sym = t.symbol or "UNKNOWN"
            symbol_exposure[sym] = symbol_exposure.get(sym, 0) + exposure

        from config import MAX_DAILY_LOSS, MAX_EXPOSURE_PER_SYMBOL, MAX_OPEN_TRADES, MAX_PORTFOLIO_EXPOSURE

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

    def _drawdown_analytics(self, trades: list[tuple[Trade, float]]) -> DrawdownAnalyticsDTO:
        closed = [t_pnl for t_pnl in trades if t_pnl[0].status in FINAL_STATUSES]
        closed_sorted = sorted(closed, key=lambda t_pnl: t_pnl[0].created_at or datetime.min)
        pnls = [t_pnl[1] for t_pnl in closed_sorted]

        if not pnls:
            return DrawdownAnalyticsDTO()

        peak = 0.0
        max_dd = 0.0
        cumulative = 0.0
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

    def _heatmap_data(self, trades: list[tuple[Trade, float]]) -> list[HeatmapDataDTO]:
        by_symbol_day: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for t_pnl in trades:
            t = t_pnl[0]
            if t.created_at and t_pnl[1] is not None:
                sym = t.symbol or "UNKNOWN"
                day = t.created_at.strftime("%Y-%m-%d") if hasattr(t.created_at, "strftime") else "UNKNOWN"
                by_symbol_day[sym][day] += t_pnl[1]

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

    def _performance_trends(self, trades: list[tuple[Trade, float]]) -> list[PerformanceTrendDTO]:
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

    def _compute_kpis(self, trades: list[tuple[Trade, float]]) -> list[KPIDTO]:
        closed = [t_pnl for t_pnl in trades if t_pnl[0].status in FINAL_STATUSES]
        wins = [t_pnl for t_pnl in closed if t_pnl[1] > 0]
        losses = [t_pnl for t_pnl in closed if t_pnl[1] < 0]
        total_pnl = sum(t_pnl[1] for t_pnl in closed)

        return [
            KPIDTO(name="Total PnL", value=round(total_pnl, 2), unit="USD", trend=self._pnl_trend(trades), status="positive" if total_pnl > 0 else "negative" if total_pnl < 0 else "neutral"),
            KPIDTO(name="Win Rate", value=round((len(wins) / len(closed) * 100), 1) if closed else 0, unit="%", trend="stable", status="good"),
            KPIDTO(name="Total Trades", value=len(closed), unit="count", trend="stable", status="neutral"),
            KPIDTO(name="Avg PnL", value=round(total_pnl / len(closed), 2) if closed else 0, unit="USD", trend="stable", status="neutral"),
            KPIDTO(name="Profit Factor", value=round(self._profit_factor(wins, losses), 2), unit="ratio", trend="stable", status="good"),
            KPIDTO(name="Max Drawdown", value=round(self._compute_max_drawdown([t_pnl[1] for t_pnl in closed]), 2), unit="USD", trend="stable", status="warning"),
        ]

    def _daily_loss(self, trades: list[tuple[Trade, float]]) -> float:
        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        def is_today(closed_at):
            if closed_at is None:
                return False
            ca = closed_at.replace(tzinfo=None) if closed_at.tzinfo else closed_at
            ts = today.replace(tzinfo=None)
            return ca >= ts


        return round(
            sum(
                abs(t_pnl[1])
                for t_pnl in trades
                if t_pnl[1] < 0
                and is_today(t_pnl[0].closed_at)
            ),
            2,
        )

    def _pnl_trend(self, trades: list[tuple[Trade, float]]) -> str:
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

    def _profit_factor(self, wins: list[tuple[Trade, float]], losses: list[tuple[Trade, float]]) -> float:
        gp = sum(t_pnl[1] for t_pnl in wins)
        gl = abs(sum(t_pnl[1] for t_pnl in losses))
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
