from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from database import PaperTrade, Trade
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
from services.analytics_service import AnalyticsService
from services.kpi_service import KPIService


def _paper_trade_for(trade: Trade, quantity: float = 1.0) -> PaperTrade:
    """A matching PaperTrade (quantity=1.0 by default) so trade.pnl reads as
    a real dollar amount -- AnalyticsService excludes trades with no
    matching PaperTrade rather than guessing a quantity (see services/pnl.py)."""
    return PaperTrade(
        position_id=trade.id, symbol=trade.symbol, side=trade.side,
        entry=trade.entry, quantity=quantity, status=trade.status, pnl=trade.pnl,
    )


class TestAnalyticsDTOs:

    def test_daily_analytics_to_dict(self):
        dto = DailyAnalyticsDTO(date="2024-01-01", total_trades=5, wins=3, losses=2, win_rate=60.0, pnl=500.0, avg_pnl=100.0)
        d = dto.to_dict()
        assert d["date"] == "2024-01-01"
        assert d["win_rate"] == 60.0

    def test_weekly_analytics_to_dict(self):
        dto = WeeklyAnalyticsDTO(week="2024-W01", total_trades=10, pnl=1000.0)
        d = dto.to_dict()
        assert d["week"] == "2024-W01"

    def test_monthly_analytics_to_dict(self):
        dto = MonthlyAnalyticsDTO(month="2024-01", total_trades=20, pnl=2000.0)
        d = dto.to_dict()
        assert d["month"] == "2024-01"

    def test_win_loss_to_dict(self):
        dto = WinLossAnalyticsDTO(total_wins=10, total_losses=5, win_rate=66.7, profit_factor=2.5)
        d = dto.to_dict()
        assert d["win_rate"] == 66.7
        assert d["profit_factor"] == 2.5

    def test_symbol_analytics_to_dict(self):
        dto = SymbolAnalyticsDTO(symbol="BTCUSDT", total_trades=10, total_pnl=5000.0)
        d = dto.to_dict()
        assert d["symbol"] == "BTCUSDT"

    def test_strategy_analytics_to_dict(self):
        dto = StrategyAnalyticsDTO(strategy_name="LONG", win_rate=60.0, sharpe=1.5)
        d = dto.to_dict()
        assert d["strategy_name"] == "LONG"

    def test_risk_analytics_to_dict(self):
        dto = RiskAnalyticsDTO(max_open_trades=3, current_open_trades=1, risk_score=0.33)
        d = dto.to_dict()
        assert d["max_open_trades"] == 3

    def test_drawdown_analytics_to_dict(self):
        dto = DrawdownAnalyticsDTO(max_drawdown=1000.0, max_drawdown_pct=10.0)
        d = dto.to_dict()
        assert d["max_drawdown"] == 1000.0

    def test_heatmap_to_dict(self):
        dto = HeatmapDataDTO(symbol="BTCUSDT", metric="pnl", values={"2024-01-01": 500.0}, intensity=0.5)
        d = dto.to_dict()
        assert d["symbol"] == "BTCUSDT"

    def test_performance_trend_to_dict(self):
        dto = PerformanceTrendDTO(metric="pnl", daily_values=[{"date": "2024-01-01", "value": 100}], trend_direction="improving", change_pct=10.0)
        d = dto.to_dict()
        assert d["trend_direction"] == "improving"

    def test_kpi_to_dict(self):
        dto = KPIDTO(name="Total PnL", value=5000.0, unit="USD", trend="improving", status="positive")
        d = dto.to_dict()
        assert d["name"] == "Total PnL"
        assert d["unit"] == "USD"

    def test_analytics_dto_empty(self):
        dto = AnalyticsDTO()
        d = dto.to_dict()
        assert d["daily"] == []
        assert d["win_loss"] is None
        assert d["risk"] is None

    def test_analytics_dto_with_data(self):
        dto = AnalyticsDTO(
            daily=[DailyAnalyticsDTO(date="2024-01-01", pnl=100)],
            win_loss=WinLossAnalyticsDTO(total_wins=1),
        )
        d = dto.to_dict()
        assert len(d["daily"]) == 1
        assert d["win_loss"]["total_wins"] == 1


class TestAnalyticsService:

    def test_analytics_service_empty_db(self, db_session):
        service = AnalyticsService(session_factory=lambda: db_session)
        analytics = service.full_analytics(limit=100)
        assert analytics.daily == []
        assert analytics.weekly == []
        assert analytics.monthly == []
        assert analytics.win_loss is not None
        assert analytics.win_loss.total_wins == 0
        assert analytics.by_symbol == []
        assert analytics.by_strategy == []
        assert analytics.risk is not None
        assert analytics.drawdown is not None

    def test_analytics_service_with_trades(self, db_session):
        now = datetime.now(UTC)

        trades_data = [
            dict(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                 tp1=52000, rr=2.0, status="TP_HIT", pnl=2000.0,
                 created_at=now - timedelta(days=2), closed_at=now - timedelta(days=2)),
            dict(symbol="ETHUSDT", side="SHORT", entry=3000, stop=3100,
                 tp1=2800, rr=2.0, status="SL_HIT", pnl=-500.0,
                 created_at=now - timedelta(days=1), closed_at=now - timedelta(days=1)),
            dict(symbol="BTCUSDT", side="LONG", entry=51000, stop=50000,
                 tp1=53000, rr=2.0, status="OPEN", pnl=0.0,
                 created_at=now - timedelta(hours=1)),
        ]

        trades = []
        for td in trades_data:
            t = Trade(**td)
            db_session.add(t)
            trades.append(t)
        db_session.flush()
        for t in trades:
            db_session.add(_paper_trade_for(t))
        db_session.flush()

        service = AnalyticsService(session_factory=lambda: db_session)
        analytics = service.full_analytics(limit=100)

        assert analytics.win_loss is not None
        assert analytics.win_loss.total_wins == 1
        assert analytics.win_loss.total_losses == 1
        assert analytics.win_loss.win_rate == 50.0
        assert analytics.win_loss.total_wins == 1
        assert len(analytics.daily) > 0

    def test_symbol_analytics_grouping(self, db_session):
        now = datetime.now(UTC)
        trades_data = [
            dict(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                 tp1=52000, rr=2.0, status="TP_HIT", pnl=2000.0, created_at=now),
            dict(symbol="BTCUSDT", side="LONG", entry=51000, stop=50000,
                 tp1=53000, rr=2.0, status="SL_HIT", pnl=-500.0, created_at=now),
            dict(symbol="ETHUSDT", side="LONG", entry=3000, stop=2900,
                 tp1=3200, rr=2.0, status="TP_HIT", pnl=400.0, created_at=now),
        ]
        trades = []
        for td in trades_data:
            t = Trade(**td)
            db_session.add(t)
            trades.append(t)
        db_session.flush()
        for t in trades:
            db_session.add(_paper_trade_for(t))
        db_session.flush()

        service = AnalyticsService(session_factory=lambda: db_session)
        analytics = service.full_analytics()

        assert len(analytics.by_symbol) == 2
        btc = next(s for s in analytics.by_symbol if s.symbol == "BTCUSDT")
        eth = next(s for s in analytics.by_symbol if s.symbol == "ETHUSDT")
        assert btc.total_trades == 2
        assert btc.wins == 1
        assert eth.total_trades == 1
        assert eth.wins == 1

    def test_strategy_analytics_by_side(self, db_session):
        now = datetime.now(UTC)
        trades = []
        for i in range(5):
            t = Trade(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                       tp1=52000, rr=2.0, status="TP_HIT", pnl=1000.0, created_at=now)
            db_session.add(t)
            trades.append(t)
        for i in range(3):
            t = Trade(symbol="BTCUSDT", side="SHORT", entry=50000, stop=51000,
                       tp1=48000, rr=2.0, status="TP_HIT", pnl=800.0, created_at=now)
            db_session.add(t)
            trades.append(t)
        db_session.flush()
        for t in trades:
            db_session.add(_paper_trade_for(t))
        db_session.flush()

        service = AnalyticsService(session_factory=lambda: db_session)
        analytics = service.full_analytics()

        assert len(analytics.by_strategy) == 2
        long_s = next(s for s in analytics.by_strategy if s.strategy_name == "LONG")
        short_s = next(s for s in analytics.by_strategy if s.strategy_name == "SHORT")
        assert long_s.total_trades == 5
        assert short_s.total_trades == 3

    def test_drawdown_analytics(self, db_session):
        now = datetime.now(UTC)
        for i, pnl in enumerate([1000, 2000, -500, 1500, -1000, 500]):
            db_session.add(Trade(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                                  tp1=52000, rr=2.0, status="TP_HIT" if pnl > 0 else "SL_HIT",
                                  pnl=pnl if pnl > 0 else pnl, created_at=now + timedelta(hours=i)))
        db_session.flush()

        service = AnalyticsService(session_factory=lambda: db_session)
        analytics = service.full_analytics()

        assert analytics.drawdown is not None
        assert analytics.drawdown.max_drawdown >= 0

    def test_kpi_service_empty(self, db_session):
        service = KPIService(session_factory=lambda: db_session)
        kpis = service.get_kpis()
        assert len(kpis) == 10
        assert kpis[0].name == "Total PnL"
        assert kpis[0].value == 0.0

    def test_kpi_service_with_data(self, db_session):
        now = datetime.now(UTC)
        for pnl in [1000, 2000, -500]:
            db_session.add(Trade(symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
                                  tp1=52000, rr=2.0,
                                  status="TP_HIT" if pnl > 0 else "SL_HIT",
                                  pnl=pnl, created_at=now))
        db_session.flush()

        service = KPIService(session_factory=lambda: db_session)
        kpis = service.get_kpis()
        assert kpis[0].value == 2500.0
        assert kpis[2].value == 66.7

    def test_risk_analytics_rejection_rate(self, db_session):
        from database import Signal
        for status in ("REJECTED", "REJECTED", "OPEN", "EXECUTED"):
            db_session.add(Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status=status))
        db_session.flush()

        service = AnalyticsService(session_factory=lambda: db_session)
        analytics = service.full_analytics()

        assert analytics.risk is not None
        assert analytics.risk.total_rejections == 2

    def test_analytics_service_mixed_quantities(self, db_session):
        from database import PaperTrade, Trade
        now = datetime.now(UTC)

        # 1. Closed trade with quantity = 2.5 (real dollar pnl = 100.0 * 2.5 = 250.0)
        t1 = Trade(
            symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
            tp1=52000, rr=2.0, status="TP_HIT", pnl=100.0,
            created_at=now, closed_at=now
        )
        db_session.add(t1)
        db_session.flush()
        pt1 = PaperTrade(
            position_id=t1.id, symbol="BTCUSDT", side="LONG",
            entry=50000, quantity=2.5, status="CLOSED", pnl=250.0
        )
        db_session.add(pt1)

        # 2. Closed trade with quantity = 0.5 (real dollar pnl = -200.0 * 0.5 = -100.0)
        t2 = Trade(
            symbol="BTCUSDT", side="LONG", entry=50000, stop=49000,
            tp1=52000, rr=2.0, status="SL_HIT", pnl=-200.0,
            created_at=now, closed_at=now
        )
        db_session.add(t2)
        db_session.flush()
        pt2 = PaperTrade(
            position_id=t2.id, symbol="BTCUSDT", side="LONG",
            entry=50000, quantity=0.5, status="CLOSED", pnl=-100.0
        )
        db_session.add(pt2)

        # 3. Closed trade with NO matching PaperTrade record -- real quantity
        # unknown, must be excluded entirely (not a guessed quantity=1.0
        # fallback).
        t3 = Trade(
            symbol="ETHUSDT", side="LONG", entry=3000, stop=2900,
            tp1=3200, rr=2.0, status="TP_HIT", pnl=50.0,
            created_at=now, closed_at=now
        )
        db_session.add(t3)
        db_session.flush()

        service = AnalyticsService(session_factory=lambda: db_session)
        analytics = service.full_analytics()

        # t3 (no matching PaperTrade) is excluded entirely -- only t1/t2 count.
        assert analytics.win_loss is not None
        assert analytics.win_loss.gross_profit == 250.0  # t1 only
        assert analytics.win_loss.gross_loss == 100.0  # abs(-100.0) (t2)
        assert analytics.win_loss.profit_factor == 2.5  # 250 / 100
