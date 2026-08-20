"""Hyperliquid WebSocket client for real-time candle market data streams."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import websockets

from market.stream.cache import CandleStreamCache, normalize_symbol, normalize_timeframe

logger = logging.getLogger(__name__)

_DEFAULT_URL = "wss://api.hyperliquid.xyz/ws"


def normalize_stream_symbol(symbol: str) -> str:
    """Normalize symbol to Hyperliquid's bare-coin-id convention (e.g.
    'BTCUSDT' -> 'BTC') -- Hyperliquid's own API expects the bare coin id,
    same convention market/provider/hyperliquid.py already strips before
    calling its REST collector."""
    clean = symbol.upper().replace("/", "").replace("-", "").strip()
    for suffix in ("USDT", "USDC", "BUSD", "USD", "PERP"):
        if clean.endswith(suffix) and len(clean) > len(suffix):
            return clean[: -len(suffix)]
    return clean


class HyperliquidWSClient:
    """WebSocket client streaming Hyperliquid candles into a CandleStreamCache."""

    def __init__(
        self,
        cache: CandleStreamCache,
        symbols: list[str] | None = None,
        timeframes: list[str] | None = None,
        base_url: str = _DEFAULT_URL,
    ) -> None:
        self.cache = cache
        self.base_url = base_url.rstrip("/")
        self._subscriptions: set[tuple[str, str]] = set()

        if symbols and timeframes:
            for sym in symbols:
                for tf in timeframes:
                    self.add_subscription(sym, tf)

        self._running = False
        self._connected = False
        self._task: asyncio.Task | None = None
        self._ws: Any = None

    def add_subscription(self, symbol: str, timeframe: str) -> None:
        """Add a symbol and timeframe to the subscription set."""
        sym = normalize_stream_symbol(symbol)
        tf = normalize_timeframe(timeframe)
        self._subscriptions.add((sym, tf))

    def remove_subscription(self, symbol: str, timeframe: str) -> None:
        """Remove a symbol and timeframe from the subscription set."""
        sym = normalize_stream_symbol(symbol)
        tf = normalize_timeframe(timeframe)
        self._subscriptions.discard((sym, tf))

    def get_subscriptions(self) -> list[tuple[str, str]]:
        """Return a sorted list of current subscriptions."""
        return sorted(self._subscriptions)

    def build_subscribe_messages(self) -> list[dict[str, Any]]:
        """Hyperliquid subscribes one (coin, interval) pair per message --
        unlike Binance/Bybit there's no batched multi-topic subscribe."""
        return [
            {
                "method": "subscribe",
                "subscription": {"type": "candle", "coin": sym, "interval": tf},
            }
            for sym, tf in sorted(self._subscriptions)
        ]

    def parse_message(self, raw_msg: str | dict[str, Any]) -> list[dict[str, Any]]:
        """Parse a Hyperliquid WebSocket candle push message and update the
        cache. Returns a list (possibly empty) of parsed candle dicts --
        Hyperliquid pushes an array of candle objects per message."""
        try:
            if isinstance(raw_msg, str):
                data = json.loads(raw_msg)
            elif isinstance(raw_msg, dict):
                data = raw_msg
            else:
                return []
        except Exception as e:
            logger.debug("Failed to parse Hyperliquid WS message: %s", e)
            return []

        if not isinstance(data, dict) or data.get("channel") != "candle":
            return []

        candles = data.get("data")
        if isinstance(candles, dict):
            candles = [candles]
        if not isinstance(candles, list):
            return []

        parsed: list[dict[str, Any]] = []
        now_ms = time.time() * 1000
        for kline in candles:
            if not isinstance(kline, dict):
                continue
            try:
                symbol = normalize_symbol(str(kline.get("s", "")))
                timeframe = normalize_timeframe(str(kline.get("i", "")))
                timestamp = int(kline.get("t", 0))
                close_time = float(kline.get("T", 0))
                open_ = float(kline.get("o", 0.0))
                high = float(kline.get("h", 0.0))
                low = float(kline.get("l", 0.0))
                close = float(kline.get("c", 0.0))
                volume = float(kline.get("v", 0.0))
                # Hyperliquid's candle push has no explicit "is this candle
                # closed" flag (unlike Binance's "x"/Bybit's "confirm") --
                # infer it from whether the candle's own close time has
                # already passed.
                is_closed = close_time > 0 and now_ms >= close_time

                if not symbol or not timeframe or timestamp <= 0:
                    continue

                self.cache.update_candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open_=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                    is_closed=is_closed,
                )
                parsed.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": timestamp,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "is_closed": is_closed,
                })
            except (ValueError, TypeError) as e:
                logger.debug("Invalid candle fields in Hyperliquid WS payload: %s", e)
                continue

        return parsed

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def start(self) -> asyncio.Task:
        """Start the WebSocket listener in a background task."""
        if self._running and self._task and not self._task.done():
            return self._task

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        return self._task

    async def stop(self) -> None:
        """Stop the WebSocket listener gracefully."""
        self._running = False
        self._connected = False

        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception as e:
                logger.debug("Error closing Hyperliquid WS connection: %s", e)
            self._ws = None

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run_loop(self) -> None:
        """Internal reconnect loop with backoff -- resubscribes to every
        (coin, interval) pair on every fresh connection."""
        backoff = 1.0
        max_backoff = 30.0

        while self._running:
            logger.info("Connecting to Hyperliquid WS stream: %s", self.base_url)
            try:
                async with websockets.connect(
                    self.base_url,
                    ping_interval=20,
                    ping_timeout=20,
                ) as ws:
                    self._ws = ws
                    self._connected = True
                    backoff = 1.0  # Reset backoff on success
                    logger.info("Connected to Hyperliquid WS stream: %s", self.base_url)

                    for msg in self.build_subscribe_messages():
                        await ws.send(json.dumps(msg))
                    if self._subscriptions:
                        logger.info("Sent Hyperliquid subscriptions for %d (coin, interval) pairs", len(self._subscriptions))

                    async for message in ws:
                        if not self._running:
                            break
                        self.parse_message(message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._connected = False
                self._ws = None
                if not self._running:
                    break
                logger.warning("Hyperliquid WS stream disconnected/error: %s. Reconnecting in %.1fs...", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, max_backoff)

        self._connected = False
        self._ws = None
