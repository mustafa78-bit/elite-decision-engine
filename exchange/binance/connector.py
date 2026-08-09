from __future__ import annotations

import hashlib
import hmac
import logging
import time
from datetime import UTC, datetime, timezone
from decimal import Decimal
from typing import Optional

import requests

from config import ACCOUNT_EQUITY
from exchange.base import ExchangeAdapter
from exchange.exceptions import (
    AuthenticationError,
    ExchangeConnectionError,
    ExchangeTimeoutError,
    MarketDataError,
    RateLimitError,
)
from exchange.models import Balance, Candle, Order, Position, Ticker

logger = logging.getLogger(__name__)

BASE_URL = "https://api.binance.com"


class BinanceExchange(ExchangeAdapter):
    """Binance exchange adapter using REST API."""

    name = "binance"

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        paper_mode: bool = True,
        timeout: int = 20,
    ) -> None:
        self.api_key = api_key or ""
        self.api_secret = api_secret or ""
        self.paper_mode = paper_mode
        self.timeout = timeout
        self._orders: dict[str, Order] = {}
        self._next_order_id = 1
        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _request(self, method: str, path: str, params: dict | None = None) -> dict | list:
        url = f"{BASE_URL}{path}"
        try:
            resp = self._session.request(method, url, params=params, timeout=self.timeout)
            if resp.status_code == 429:
                raise RateLimitError("Binance rate limit exceeded")
            if resp.status_code == 401:
                raise AuthenticationError("Invalid Binance API key")
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout as e:
            raise ExchangeTimeoutError(str(e)) from e
        except requests.exceptions.ConnectionError as e:
            raise ExchangeConnectionError(str(e)) from e
        except requests.exceptions.HTTPError as e:
            raise MarketDataError(str(e)) from e

    def _signed_request(self, method: str, path: str, params: dict | None = None) -> dict | list:
        if not self.api_secret:
            raise AuthenticationError("API secret required for authenticated requests")
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return self._request(method, path, params)

    def ticker(self, symbol: str) -> Ticker:
        try:
            data = self._request("GET", "/api/v3/ticker/24hr", {"symbol": symbol.upper()})
            if isinstance(data, dict):
                return Ticker(
                    symbol=str(data.get("symbol", symbol)),
                    bid=Decimal(str(data.get("bidPrice", "0"))),
                    ask=Decimal(str(data.get("askPrice", "0"))),
                    last=Decimal(str(data.get("lastPrice", "0"))),
                    volume_24h=Decimal(str(data.get("volume", "0"))),
                    high_24h=Decimal(str(data.get("highPrice", "0"))),
                    low_24h=Decimal(str(data.get("lowPrice", "0"))),
                    change_24h=Decimal(str(data.get("priceChangePercent", "0"))),
                )
            raise MarketDataError(f"Unexpected response for {symbol}")
        except Exception as e:
            if isinstance(e, MarketDataError):
                raise
            raise MarketDataError(str(e)) from e

    def candles(self, symbol: str, timeframe: str = "1h", limit: int = 200) -> list[Candle]:
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h",
            "12h": "12h", "1d": "1d", "1w": "1w",
        }
        interval = interval_map.get(timeframe, "1h")
        raw = self._request("GET", "/api/v3/klines", {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1000),
        })
        if not isinstance(raw, list):
            raise MarketDataError(f"Unexpected klines response for {symbol}")
        result: list[Candle] = []
        for entry in raw:
            result.append(Candle(
                symbol=symbol.upper(),
                timeframe=timeframe,
                open=Decimal(str(entry[1])),
                high=Decimal(str(entry[2])),
                low=Decimal(str(entry[3])),
                close=Decimal(str(entry[4])),
                volume=Decimal(str(entry[5])),
                timestamp=datetime.fromtimestamp(int(entry[0]) / 1000, tz=UTC),
            ))
        return result

    def account_balance(self) -> list[Balance]:
        if self.paper_mode:
            return [
                Balance(currency="USDT", total=Decimal(str(ACCOUNT_EQUITY)), available=Decimal(str(ACCOUNT_EQUITY)), wallet="SPOT"),
            ]
        try:
            data = self._signed_request("GET", "/api/v3/account")
            if isinstance(data, dict):
                result: list[Balance] = []
                for bal in data.get("balances", []):
                    free = Decimal(str(bal.get("free", "0")))
                    locked = Decimal(str(bal.get("locked", "0")))
                    total = free + locked
                    if total > Decimal("0"):
                        result.append(Balance(
                            currency=str(bal["asset"]),
                            total=total,
                            available=free,
                            locked=locked,
                            wallet="SPOT",
                        ))
                return result
            raise AuthenticationError("Failed to fetch account data")
        except AuthenticationError:
            raise
        except Exception as e:
            raise MarketDataError(str(e)) from e

    def positions(self, symbol: str | None = None) -> list[Position]:
        if self.paper_mode:
            from database import PaperOrder, Trade, get_session
            session = get_session()
            try:
                query = session.query(Trade).filter(Trade.status == "OPEN")
                if symbol:
                    query = query.filter(Trade.symbol == symbol)
                result: list[Position] = []
                ticker_cache = {}
                for t in query.all():
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
            order_id = f"binance_paper_{self._next_order_id}"
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
        raise NotImplementedError("Live Binance order placement not implemented")

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
