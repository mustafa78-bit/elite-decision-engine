"""Bybit WebSocket client for real-time kline/candle market data streams."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import websockets

from market.stream.cache import CandleStreamCache, normalize_symbol

logger = logging.getLogger(__name__)

_DEFAULT_URL = "wss://stream.bybit.com/v5/public/linear"

# Bybit V5's kline WS "interval" values are the same plain minute-counts/
# calendar-letters as its REST API (see market/provider/bybit.py's
# _INTERVAL_MAP) -- not the "15m"/"1h"/"4h"/"1d" strings this app uses
# everywhere else.
_INTERVAL_MAP: dict[str, str] = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "4h": "240",
    "1d": "D",
    "1w": "W",
}
_REVERSE_INTERVAL_MAP = {v: k for k, v in _INTERVAL_MAP.items()}


def normalize_stream_symbol(symbol: str) -> str:
    """Normalize symbol for Bybit's linear-perp WS streams (e.g. 'BTC' -> 'BTCUSDT')."""
    clean = symbol.upper().replace("/", "").replace("-", "").strip()
    if not clean.endswith("USDT"):
        clean += "USDT"
    return clean


class BybitWSClient:
    """WebSocket client streaming Bybit V5 linear-perp klines into a CandleStreamCache."""

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
        interval = _INTERVAL_MAP.get(timeframe)
        if interval is None:
            raise ValueError(f"Unsupported timeframe for BybitWSClient: {timeframe!r}")
        sym = normalize_stream_symbol(symbol)
        self._subscriptions.add((sym, timeframe))

    def remove_subscription(self, symbol: str, timeframe: str) -> None:
        """Remove a symbol and timeframe from the subscription set."""
        sym = normalize_stream_symbol(symbol)
        self._subscriptions.discard((sym, timeframe))

    def get_subscriptions(self) -> list[tuple[str, str]]:
        """Return a sorted list of current subscriptions."""
        return sorted(self._subscriptions)

    def _format_topic(self, symbol: str, timeframe: str) -> str:
        sym = normalize_stream_symbol(symbol)
        interval = _INTERVAL_MAP[timeframe]
        return f"kline.{interval}.{sym}"

    def build_subscribe_payload(self) -> dict[str, Any] | None:
        """Construct the SUBSCRIBE JSON-RPC payload for all active subscriptions."""
        if not self._subscriptions:
            return None
        args = [self._format_topic(sym, tf) for sym, tf in sorted(self._subscriptions)]
        return {"op": "subscribe", "args": args}

    def parse_message(self, raw_msg: str | dict[str, Any]) -> list[dict[str, Any]]:
        """Parse a Bybit WebSocket kline push message and update the cache.

        Returns a list (possibly empty) of parsed candle dicts -- Bybit's
        "data" array can carry more than one candle per message.
        """
        try:
            if isinstance(raw_msg, str):
                data = json.loads(raw_msg)
            elif isinstance(raw_msg, dict):
                data = raw_msg
            else:
                return []
        except Exception as e:
            logger.debug("Failed to parse Bybit WS message: %s", e)
            return []

        if not isinstance(data, dict):
            return []

        topic = data.get("topic", "")
        if not isinstance(topic, str) or not topic.startswith("kline."):
            return []

        parts = topic.split(".")
        if len(parts) != 3:
            return []
        _, interval, sym = parts
        timeframe = _REVERSE_INTERVAL_MAP.get(interval)
        symbol = normalize_symbol(sym)
        if not timeframe or not symbol:
            return []

        candles = data.get("data")
        if not isinstance(candles, list):
            return []

        parsed: list[dict[str, Any]] = []
        for kline in candles:
            if not isinstance(kline, dict):
                continue
            try:
                timestamp = int(kline.get("start", 0))
                open_ = float(kline.get("open", 0.0))
                high = float(kline.get("high", 0.0))
                low = float(kline.get("low", 0.0))
                close = float(kline.get("close", 0.0))
                volume = float(kline.get("volume", 0.0))
                is_closed = bool(kline.get("confirm", False))

                if timestamp <= 0:
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
                logger.debug("Invalid kline fields in Bybit WS payload: %s", e)
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
                logger.debug("Error closing Bybit WS connection: %s", e)
            self._ws = None

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run_loop(self) -> None:
        """Internal reconnect loop with backoff -- resubscribes on every
        fresh connection since Bybit's public streams don't persist
        subscriptions across a reconnect."""
        backoff = 1.0
        max_backoff = 30.0

        while self._running:
            logger.info("Connecting to Bybit WS stream: %s", self.base_url)
            try:
                async with websockets.connect(
                    self.base_url,
                    ping_interval=20,
                    ping_timeout=20,
                ) as ws:
                    self._ws = ws
                    self._connected = True
                    backoff = 1.0  # Reset backoff on success
                    logger.info("Connected to Bybit WS stream: %s", self.base_url)

                    payload = self.build_subscribe_payload()
                    if payload is not None:
                        await ws.send(json.dumps(payload))
                        logger.info("Sent Bybit subscription for %d topics", len(payload["args"]))

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
                logger.warning("Bybit WS stream disconnected/error: %s. Reconnecting in %.1fs...", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, max_backoff)

        self._connected = False
        self._ws = None
