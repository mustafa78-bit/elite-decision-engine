"""Paper trading execution layer.

This executor manages PAPER trades only. It never sends live exchange orders,
never calls external notification services, and only uses the existing
SQLAlchemy models from ``database.py``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Optional

from database import OPEN, TP_HIT, SL_HIT, CLOSED, FINAL_STATUSES, Trade, get_session
from market_data.collector import HyperliquidCollector
from notifications.dispatcher import NotificationDispatcher
from notifications.events import TradeEvent


STALE_TRADE_DAYS = 7


@dataclass(frozen=True)
class PaperTradeRequest:
    """Input data required to open a paper trade."""

    symbol: str
    side: str
    entry: float
    stop_loss: float
    take_profit: float
    signal_id: Optional[int] = None
    take_profit_2: Optional[float] = None
    risk_reward: Optional[float] = None


@dataclass(frozen=True)
class TradePnL:
    """Calculated paper trade profit and loss."""

    unrealized_pnl: float
    pnl_percentage: float
    realized_pnl: Optional[float] = None


@dataclass(frozen=True)
class TradeMonitorResult:
    """Result of monitoring one open paper trade."""

    trade_id: int
    symbol: str
    side: str
    current_price: float
    unrealized_pnl: float
    pnl_percentage: float
    status: str
    realized_pnl: Optional[float] = None


class PaperExecutor:
    """Manage paper trades and close them when TP or SL is reached."""

    def __init__(
        self,
        collector: Optional[HyperliquidCollector] = None,
        session_factory: Callable[[], Any] = get_session,
        logger: Optional[logging.Logger] = None,
        notifications: Optional[NotificationDispatcher] = None,
        market_service: Optional[Any] = None,
    ) -> None:
        """Create a paper executor with injectable infrastructure."""

        self.collector = collector or HyperliquidCollector()
        self.session_factory = session_factory
        self.logger = logger or logging.getLogger(__name__)
        self._pnl_percentages: dict[int, float] = {}
        self._realized_pnl: dict[int, float] = {}
        self.notifications = notifications or NotificationDispatcher()
        self.market_service = market_service

    def open_trade(
        self,
        symbol: str,
        side: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        signal_id: Optional[int] = None,
        take_profit_2: Optional[float] = None,
        risk_reward: Optional[float] = None,
    ) -> Optional[Trade]:
        """Open a paper trade unless the same symbol and side is already open."""

        request = PaperTradeRequest(
            symbol=symbol,
            side=side,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            signal_id=signal_id,
            take_profit_2=take_profit_2,
            risk_reward=risk_reward,
        )
        return self.open_trade_from_request(request)

    def open_trade_from_request(self, request: PaperTradeRequest) -> Optional[Trade]:
        """Open a paper trade from a request object."""

        self._validate_trade_request(request)
        symbol = self._normalize_symbol(request.symbol)
        side = self._normalize_side(request.side)

        session = self.session_factory()
        try:
            if self._has_duplicate_position(session, symbol, side):
                self.logger.info("Duplicate paper position skipped: %s %s", symbol, side)
                return None

            trade = Trade(
                signal_id=request.signal_id,
                symbol=symbol,
                side=side,
                entry=float(request.entry),
                stop=float(request.stop_loss),
                tp1=float(request.take_profit),
                tp2=(
                    float(request.take_profit_2)
                    if request.take_profit_2 is not None
                    else None
                ),
                rr=(
                    float(request.risk_reward)
                    if request.risk_reward is not None
                    else self._calculate_risk_reward(request)
                ),
                pnl=0.0,
                status=OPEN,
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)
            session.expunge(trade)
            self.logger.info("Opened paper trade %s %s at %.8f", symbol, side, request.entry)
            return trade
        except Exception:
            session.rollback()
            self.logger.exception("Failed to open paper trade: %s %s", symbol, side)
            return None
        finally:
            session.close()

    def get_open_trades(self) -> list[Trade]:
        """Load all currently open paper trades."""

        session = self.session_factory()
        try:
            trades = session.query(Trade).filter(Trade.status == OPEN).all()
            for trade in trades:
                session.expunge(trade)
            return trades
        except Exception:
            session.rollback()
            self.logger.exception("Failed to load open paper trades")
            return []
        finally:
            session.close()

    def monitor_open_trades(self) -> list[TradeMonitorResult]:
        """Monitor every open trade and close trades that hit TP or SL."""

        session = self.session_factory()
        try:
            trades = session.query(Trade).filter(Trade.status == OPEN).all()
            results = self._monitor_trades(session, trades)

            closed = []
            for t in trades:
                if str(t.status) in FINAL_STATUSES:
                    closed.append({
                        "trade_id": t.id,
                        "symbol": t.symbol,
                        "side": t.side,
                        "status": t.status,
                        "exit_price": t.exit_price,
                        "pnl": t.pnl,
                        "close_reason": t.close_reason,
                    })

            session.commit()

            for data in closed:
                try:
                    self.notifications.emit(TradeEvent.TRADE_CLOSED, data)
                except Exception:
                    self.logger.warning(
                        "Failed to emit TRADE_CLOSED notification for trade %s",
                        data.get("trade_id"),
                    )

            return results
        except Exception:
            session.rollback()
            self.logger.exception("Failed to monitor open paper trades")
            return []
        finally:
            session.close()

    def execute(self) -> list[TradeMonitorResult]:
        """Backward-compatible entry point for monitoring paper trades."""

        results = self.monitor_open_trades()
        self.logger.info("OPEN TRADES: %s", len(results))
        for result in results:
            self.logger.info("[PAPER] Processing trade: %s", result.trade_id)
        return results

    def close_trade(
        self,
        trade_id: int,
        exit_price: float,
        status: str = CLOSED,
        close_reason: Optional[str] = None,
    ) -> Optional[TradeMonitorResult]:
        """Manually close an open paper trade."""

        if exit_price is None or float(exit_price) <= 0:
            raise ValueError(f"Invalid exit_price for trade {trade_id}: {exit_price}")

        normalized_status = self._normalize_close_status(status)
        session = self.session_factory()
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade is None:
                self.logger.warning("Paper trade not found for close: %s", trade_id)
                session.close()
                return None
            if str(trade.status) in FINAL_STATUSES:
                session.close()
                raise ValueError(
                    f"Trade {trade_id} already in terminal status: {trade.status}"
                )

            realized_pnl = self.calculate_realized_pnl(trade, float(exit_price))
            self._close_trade_record(
                trade=trade,
                exit_price=float(exit_price),
                status=normalized_status,
                close_reason=close_reason or normalized_status,
                pnl=realized_pnl,
            )
            session.commit()

            try:
                self.notifications.emit(
                    TradeEvent.TRADE_CLOSED,
                    {
                        "trade_id": trade.id,
                        "symbol": trade.symbol,
                        "side": trade.side,
                        "status": normalized_status,
                        "exit_price": float(exit_price),
                        "pnl": realized_pnl.unrealized_pnl,
                        "close_reason": close_reason or normalized_status,
                    },
                )
            except Exception:
                self.logger.warning(
                    "Failed to emit TRADE_CLOSED notification for trade %s", trade_id,
                )

            self.logger.info("Closed paper trade %s with status %s", trade_id, normalized_status)
            return self._build_monitor_result(trade, float(exit_price), realized_pnl)
        except ValueError:
            raise
        except Exception:
            session.rollback()
            self.logger.exception("Failed to close paper trade: %s", trade_id)
            return None
        finally:
            session.close()

    def calculate_pnl(self, trade: Trade, current_price: float) -> TradePnL:
        """Calculate unrealized PnL and PnL percentage for a trade."""

        entry = float(trade.entry)
        side = self._normalize_side(str(trade.side))
        price_delta = float(current_price) - entry
        unrealized_pnl = price_delta if side == "LONG" else -price_delta
        pnl_percentage = (unrealized_pnl / entry) * 100 if entry != 0 else 0.0
        return TradePnL(
            unrealized_pnl=round(unrealized_pnl, 8),
            pnl_percentage=round(pnl_percentage, 4),
        )

    def calculate_realized_pnl(self, trade: Trade, exit_price: float) -> TradePnL:
        """Calculate realized PnL for a trade at a closing price."""

        pnl = self.calculate_pnl(trade, exit_price)
        return TradePnL(
            unrealized_pnl=pnl.unrealized_pnl,
            pnl_percentage=pnl.pnl_percentage,
            realized_pnl=pnl.unrealized_pnl,
        )

    def get_current_price(self, symbol: str) -> float:
        """Fetch the latest close price for a symbol from the configured collector."""

        if self.market_service is not None:
            return self.market_service.get_price(symbol)
        coin = self._collector_symbol(symbol)
        data = self.collector.get_ohlcv(symbol=coin, timeframe="1h", limit=2)
        if self._is_empty_market_data(data):
            raise ValueError(f"No market data returned for {symbol}")
        return float(data["close"].iloc[-1])

    def _monitor_trades(self, session: Any, trades: Iterable[Trade]) -> list[TradeMonitorResult]:
        results: list[TradeMonitorResult] = []
        for trade in trades:
            try:
                results.append(self._monitor_trade(session, trade))
            except Exception:
                self.logger.exception("Failed to monitor paper trade: %s", getattr(trade, "id", None))
        return results

    def _stale_trade(self, trade: Trade) -> bool:
        if trade.created_at is None:
            return False
        created = trade.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - created
        return age > timedelta(days=STALE_TRADE_DAYS)

    def _monitor_trade(self, session: Any, trade: Trade) -> TradeMonitorResult:
        if self._stale_trade(trade):
            self.logger.warning("Stale trade %s auto-closed after %d days", trade.id, STALE_TRADE_DAYS)
            current_price = self.get_current_price(str(trade.symbol))
            realized_pnl = self.calculate_realized_pnl(trade, current_price)
            self._close_trade_record(
                trade=trade,
                exit_price=current_price,
                status=CLOSED,
                close_reason="STALE",
                pnl=realized_pnl,
            )
            return self._build_monitor_result(trade, current_price, realized_pnl)

        current_price = self.get_current_price(str(trade.symbol))
        pnl = self.calculate_pnl(trade, current_price)
        trade.pnl = pnl.unrealized_pnl
        self._record_unrealized_pnl(trade, pnl)

        close_status = self._close_status_for_price(trade, current_price)
        if close_status is not None:
            realized_pnl = self.calculate_realized_pnl(trade, current_price)
            self._close_trade_record(
                trade=trade,
                exit_price=current_price,
                status=close_status,
                close_reason=close_status,
                pnl=realized_pnl,
            )
            self.logger.info(
                "Paper trade %s closed at %.8f with status %s",
                trade.id,
                current_price,
                close_status,
            )
            return self._build_monitor_result(trade, current_price, realized_pnl)
        else:
            session.add(trade)
            self.logger.debug(
                "Paper trade %s monitored at %.8f: pnl %.8f (%.4f%%)",
                trade.id,
                current_price,
                pnl.unrealized_pnl,
                pnl.pnl_percentage,
            )

        return self._build_monitor_result(trade, current_price, pnl)

    def _close_trade_record(
        self,
        trade: Trade,
        exit_price: float,
        status: str,
        close_reason: str,
        pnl: TradePnL,
    ) -> None:
        trade.status = status
        trade.exit_price = float(exit_price)
        trade.close_reason = close_reason
        trade.closed_at = datetime.now(timezone.utc)
        trade.pnl = pnl.unrealized_pnl
        if trade.id is not None:
            self._realized_pnl[int(trade.id)] = pnl.realized_pnl or pnl.unrealized_pnl
            self._pnl_percentages[int(trade.id)] = pnl.pnl_percentage

    def _close_status_for_price(self, trade: Trade, current_price: float) -> Optional[str]:
        side = self._normalize_side(str(trade.side))
        if trade.tp1 is None or trade.stop is None:
            self.logger.warning("Trade %s missing TP or SL; skipping close check", trade.id)
            return None

        take_profit = float(trade.tp1)
        stop_loss = float(trade.stop)

        if trade.tp2 is not None:
            tp2 = float(trade.tp2)
            if side == "LONG" and current_price >= tp2:
                return TP_HIT
            if side == "SHORT" and current_price <= tp2:
                return TP_HIT

        if side == "LONG":
            if current_price >= take_profit:
                return TP_HIT
            if current_price <= stop_loss:
                return SL_HIT
            return None

        if current_price <= take_profit:
            return TP_HIT
        if current_price >= stop_loss:
            return SL_HIT
        return None

    def _has_duplicate_position(self, session: Any, symbol: str, side: str) -> bool:
        existing = (
            session.query(Trade)
            .filter(Trade.symbol == symbol)
            .filter(Trade.side == side)
            .filter(Trade.status == OPEN)
            .first()
        )
        return existing is not None

    def _build_monitor_result(
        self,
        trade: Trade,
        current_price: float,
        pnl: TradePnL,
    ) -> TradeMonitorResult:
        return TradeMonitorResult(
            trade_id=int(trade.id),
            symbol=str(trade.symbol),
            side=str(trade.side),
            current_price=round(float(current_price), 8),
            unrealized_pnl=pnl.unrealized_pnl,
            pnl_percentage=pnl.pnl_percentage,
            status=str(trade.status),
            realized_pnl=self._realized_pnl.get(int(trade.id)) if trade.id is not None else None,
        )

    def _validate_trade_request(self, request: PaperTradeRequest) -> None:
        symbol = self._normalize_symbol(request.symbol)
        side = self._normalize_side(request.side)
        entry = float(request.entry)
        stop_loss = float(request.stop_loss)
        take_profit = float(request.take_profit)

        if not symbol:
            raise ValueError("symbol is required")
        if entry <= 0:
            raise ValueError("entry must be greater than zero")
        if side == "LONG" and not stop_loss < entry < take_profit:
            raise ValueError("LONG trades require stop_loss < entry < take_profit")
        if side == "SHORT" and not take_profit < entry < stop_loss:
            raise ValueError("SHORT trades require take_profit < entry < stop_loss")

        if request.take_profit_2 is not None:
            tp2 = float(request.take_profit_2)
            if side == "LONG" and not (tp2 > take_profit > entry > stop_loss):
                raise ValueError("LONG trades require stop < entry < tp1 < tp2")
            if side == "SHORT" and not (tp2 < take_profit < entry < stop_loss):
                raise ValueError("SHORT trades require tp2 < tp1 < entry < stop")

    @staticmethod
    def _calculate_risk_reward(request: PaperTradeRequest) -> float:
        risk = abs(float(request.entry) - float(request.stop_loss))
        reward = abs(float(request.take_profit) - float(request.entry))
        return round(reward / risk, 4) if risk > 0 else 0.0

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return str(symbol).upper().strip()

    @staticmethod
    def _normalize_side(side: str) -> str:
        normalized = str(side).upper().strip()
        if normalized not in {"LONG", "SHORT"}:
            raise ValueError("side must be LONG or SHORT")
        return normalized

    @staticmethod
    def _normalize_close_status(status: str) -> str:
        normalized = str(status).upper().strip()
        if normalized not in FINAL_STATUSES:
            raise ValueError(f"close status must be one of: {', '.join(sorted(FINAL_STATUSES))}")
        return normalized

    @staticmethod
    def _collector_symbol(symbol: str) -> str:
        normalized = PaperExecutor._normalize_symbol(symbol)
        return normalized[:-4] if normalized.endswith("USDT") else normalized

    @staticmethod
    def _is_empty_market_data(data: Any) -> bool:
        empty = getattr(data, "empty", None)
        if isinstance(empty, bool):
            return empty
        try:
            return len(data) == 0
        except TypeError:
            return data is None

    def _record_unrealized_pnl(self, trade: Trade, pnl: TradePnL) -> None:
        if trade.id is not None:
            self._pnl_percentages[int(trade.id)] = pnl.pnl_percentage

    @staticmethod
    def iter_open_trade_summaries(results: Iterable[TradeMonitorResult]) -> list[str]:
        """Format monitor results for CLI output."""

        return [
            (
                f"{result.trade_id} {result.symbol} {result.side} "
                f"{result.status} pnl={result.unrealized_pnl} "
                f"pnl_pct={result.pnl_percentage}"
            )
            for result in results
        ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor = PaperExecutor()
    for summary in executor.iter_open_trade_summaries(executor.execute()):
        executor.logger.info(summary)
