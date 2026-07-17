from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.cache import TTLCache
from dto.models import PortfolioDTO, PortfolioDetailsDTO, EquityPointDTO
from decision.trade_memory import TradeMemoryStore


class PortfolioService:

    def __init__(
        self,
        trade_memory: Optional[TradeMemoryStore] = None,
        initial_equity: float = 10000.0,
        cache_ttl: float = 30.0,
    ):
        self._trade_memory = trade_memory or TradeMemoryStore()
        self._initial_equity = initial_equity
        self._cache = TTLCache(default_ttl=cache_ttl)
        self._equity_history: List[EquityPointDTO] = []
        self._diagnostics: Dict[str, Any] = {
            "total_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def _record_equity(self) -> None:
        total_pnl = self._compute_total_pnl()
        equity = self._initial_equity + total_pnl
        self._equity_history.append(EquityPointDTO(
            timestamp=datetime.now(timezone.utc).isoformat(),
            equity=round(equity, 2),
        ))
        if len(self._equity_history) > 10000:
            self._equity_history = self._equity_history[-10000:]

    def _compute_total_pnl(self) -> float:
        all_trades = self._trade_memory.get_all()
        if not all_trades:
            return 0.0
        realized = sum(t.pnl for t in all_trades if not getattr(t, "is_open", False))
        return realized

    def get_portfolio(self, force_refresh: bool = False) -> PortfolioDetailsDTO:
        self._diagnostics["total_calls"] += 1
        if not force_refresh:
            cached = self._cache.get("portfolio")
            if cached is not None:
                self._diagnostics["cache_hits"] += 1
                return cached
        self._diagnostics["cache_misses"] += 1

        all_trades = self._trade_memory.get_all()
        wins = self._trade_memory.get_wins()
        losses = self._trade_memory.get_losses()
        total = len(all_trades)

        summary = PortfolioDTO(
            total_trades=total,
            win_rate=round(self._trade_memory.win_rate() * 100, 1) if total else 0.0,
            total_pnl=round(self._compute_total_pnl(), 2),
            average_pnl_pct=round(self._trade_memory.average_pnl_pct(), 2) if total else 0.0,
            open_trades=len([t for t in all_trades if getattr(t, "is_open", False)]),
            largest_win=round(max((t.pnl for t in wins), default=0), 2),
            largest_loss=round(min((t.pnl for t in losses), default=0), 2),
        )

        self._record_equity()
        detail = PortfolioDetailsDTO(
            summary=summary,
            equity_curve=list(self._equity_history[-100:]),
            daily_pnl=self._compute_daily_pnl(all_trades),
            unrealized_pnl=self._compute_unrealized_pnl(all_trades),
            realized_pnl=self._compute_realized_pnl(all_trades),
            profit_factor=self._compute_profit_factor(all_trades),
            exposure=self._compute_exposure(all_trades),
            asset_allocation=self._compute_asset_allocation(all_trades),
            position_summary=self._compute_position_summary(all_trades),
        )
        self._cache.set("portfolio", detail)
        return detail

    def _compute_daily_pnl(self, trades: list) -> float:
        today = datetime.now(timezone.utc).date()
        daily = [t.pnl for t in trades if hasattr(t, "created_at") and t.created_at.date() == today]
        return round(sum(daily), 2)

    def _compute_unrealized_pnl(self, trades: list) -> float:
        return 0.0

    def _compute_realized_pnl(self, trades: list) -> float:
        closed = [t.pnl for t in trades if not getattr(t, "is_open", True)]
        return round(sum(closed), 2)

    def _compute_profit_factor(self, trades: list) -> float:
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        if gross_loss == 0:
            return round(gross_profit, 2) if gross_profit > 0 else 0.0
        return round(gross_profit / gross_loss, 2)

    def _compute_exposure(self, trades: list) -> float:
        open_positions = [t for t in trades if getattr(t, "is_open", False)]
        return round(sum(abs(t.pnl) for t in open_positions), 2)

    def _compute_asset_allocation(self, trades: list) -> Dict[str, float]:
        allocation: Dict[str, float] = {}
        for t in trades:
            sym = t.symbol
            allocation[sym] = allocation.get(sym, 0) + abs(t.pnl)
        total = sum(allocation.values()) or 1
        return {k: round(v / total * 100, 1) for k, v in allocation.items()}

    def _compute_position_summary(self, trades: list) -> Dict[str, Any]:
        open_positions = [t for t in trades if getattr(t, "is_open", False)]
        closed_positions = [t for t in trades if not getattr(t, "is_open", False)]
        return {
            "open_count": len(open_positions),
            "closed_count": len(closed_positions),
            "symbols_open": list(set(t.symbol for t in open_positions)),
            "symbols_closed": list(set(t.symbol for t in closed_positions)),
        }

    def get_equity_curve(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._equity_history[-limit:]]

    def get_portfolio_summary(self) -> PortfolioDTO:
        return self.get_portfolio().summary

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            **self._diagnostics,
            "equity_points": len(self._equity_history),
            "trade_count": self._trade_memory.count(),
        }

    def invalidate_cache(self) -> None:
        self._cache.invalidate("portfolio")
