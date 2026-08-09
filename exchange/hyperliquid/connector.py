from __future__ import annotations

import logging
from datetime import UTC, datetime, timezone
from decimal import Decimal
from typing import Optional

import pandas as pd
import requests

from config import ACCOUNT_EQUITY
from exchange.base import ExchangeAdapter
from exchange.exceptions import ExchangeConnectionError, MarketDataError
from exchange.models import Balance, Candle, Order, Position, Ticker
from market_data.collector import HyperliquidCollector

logger = logging.getLogger(__name__)


class HyperliquidExchange(ExchangeAdapter):
    """Hyperliquid exchange adapter wrapping the existing collector."""

    name = "hyperliquid"

    def __init__(
        self,
        collector: HyperliquidCollector | None = None,
        paper_mode: bool = True,
    ) -> None:
        self.collector = collector or HyperliquidCollector()
        self.paper_mode = paper_mode
        self._orders: dict[str, Order] = {}
        self._next_order_id = 1

    def ticker(self, symbol: str) -> Ticker:
        try:
            df = self.collector.get_ohlcv(symbol=symbol, timeframe="1h", limit=2)
            if df.empty:
                raise MarketDataError(f"No data for {symbol}")
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            close = Decimal(str(last["close"]))
            prev_close = Decimal(str(prev["close"]))
            change = ((close - prev_close) / prev_close) * Decimal("100") if prev_close else Decimal("0")
            return Ticker(
                symbol=symbol,
                bid=close * Decimal("0.999"),
                ask=close * Decimal("1.001"),
                last=close,
                volume_24h=Decimal(str(df["volume"].sum())),
                high_24h=Decimal(str(df["high"].max())),
                low_24h=Decimal(str(df["low"].min())),
                change_24h=change,
            )
        except requests.RequestException as e:
            raise ExchangeConnectionError(str(e)) from e

    def candles(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> list[Candle]:
        try:
            df = self.collector.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
            if df.empty:
                raise MarketDataError(f"No candles for {symbol}")
            result: list[Candle] = []
            for _, row in df.iterrows():
                ts = datetime.fromtimestamp(int(row["timestamp"]) / 1000, tz=UTC) if "timestamp" in row else datetime.now(UTC)
                result.append(Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=Decimal(str(row["volume"])),
                    timestamp=ts,
                ))
            return result
        except requests.RequestException as e:
            raise ExchangeConnectionError(str(e)) from e

    def account_balance(self) -> list[Balance]:
        return [
            Balance(
                currency="USDT",
                total=Decimal(str(ACCOUNT_EQUITY)),
                available=Decimal(str(ACCOUNT_EQUITY)),
                wallet="SPOT",
            )
        ]

    def positions(self, symbol: str | None = None) -> list[Position]:
        if self.paper_mode:
            from database import PaperOrder, Trade, get_session
            session = get_session()
            try:
                query = session.query(Trade).filter(Trade.status == "OPEN")
                if symbol:
                    query = query.filter(Trade.symbol == symbol)
                trades = query.all()
                result: list[Position] = []
                ticker_cache = {}
                for t in trades:
                    # Look up matching PaperOrder for the open Trade
                    orders = session.query(PaperOrder).filter(PaperOrder.trade_id == t.id).all()
                    qty = Decimal("0")
                    if orders:
                        # Prioritize: FILLED, PARTIALLY_FILLED, PENDING, other. Tie-breaker: largest id (most recent)
                        status_weights = {
                            "FILLED": 4,
                            "PARTIALLY_FILLED": 3,
                            "PENDING": 2,
                        }
                        sorted_orders = sorted(
                            orders,
                            key=lambda o: (status_weights.get(str(o.status).upper(), 1), o.id or 0),
                            reverse=True
                        )
                        best_order = sorted_orders[0]
                        val = best_order.filled_quantity if best_order.filled_quantity is not None else best_order.quantity
                        qty = Decimal(str(val or 0))
                    else:
                        logger.debug("Quantity is unknown for trade id %s; no matching PaperOrder found.", t.id)

                    # Ticker fetching with per-symbol caching within this call
                    sym = str(t.symbol)
                    current_price = Decimal(str(t.entry))
                    if sym not in ticker_cache:
                        try:
                            ticker_cache[sym] = self.ticker(sym).last
                        except Exception as e:
                            logger.warning("Failed to fetch current price for %s: %s", sym, e)
                            ticker_cache[sym] = None

                    if ticker_cache[sym] is not None:
                        current_price = ticker_cache[sym]

                    result.append(Position(
                        symbol=sym,
                        side=str(t.side),
                        quantity=qty,
                        entry_price=Decimal(str(t.entry)),
                        current_price=current_price,
                        # t.pnl is a raw per-unit price delta, not a dollar
                        # amount (this codebase's convention, see
                        # services/pnl.py) -- must be scaled by real qty,
                        # already computed above for Position.quantity.
                        unrealized_pnl=Decimal(str(t.pnl or 0)) * qty,
                    ))
                return result
            finally:
                session.close()
        return []

    def create_order(self, order: Order) -> Order:
        if self.paper_mode:
            order_id = f"paper_{self._next_order_id}"
            self._next_order_id += 1
            filled = Order(
                id=order_id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                price=order.price,
                status="FILLED",
                filled_quantity=order.quantity,
                avg_fill_price=order.price,
                client_order_id=order.client_order_id,
            )
            self._orders[order_id] = filled
            return filled
        raise NotImplementedError("Live order placement not implemented")

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        if order_id in self._orders:
            self._orders.pop(order_id)
            return True
        return False

    def order_status(self, order_id: str, symbol: str) -> Order | None:
        return self._orders.get(order_id)

    def order_history(self, symbol: str, limit: int = 50) -> list[Order]:
        return [o for o in self._orders.values() if o.symbol == symbol][:limit]

    def trading_enabled(self) -> bool:
        return self.paper_mode
