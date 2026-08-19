"""Binance WebSocket client for real-time kline/candle market data streams."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

import websockets

from market.stream.cache import CandleStreamCache, normalize_symbol, normalize_timeframe

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "wss://stream.binance.com:9443"


def normalize_stream_symbol(symbol: str) -> str:
    """Normalize symbol for Binance WS streams (e.g., 'BTC' -> 'BTCUSDT')."""
    clean = symbol.upper().replace("/", "").replace("-", "").strip()
    if not any(clean.endswith(q) for q in ("USDT", "BUSD", "USDC")):
        clean += "USDT"
    return clean


class BinanceWSClient:
    """WebSocket client streaming Binance klines into a CandleStreamCache."""

    def __init__(
        self,
        cache: CandleStreamCache,
        symbols: list[str] | None = None,
        timeframes: list[str] | None = None,
        base_url: str = _DEFAULT_BASE_URL,
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
        return sorted(list(self._subscriptions))

    def _format_stream_name(self, symbol: str, timeframe: str) -> str:
        s = normalize_stream_symbol(symbol).lower()
        tf = normalize_timeframe(timeframe)
        return f"{s}@kline_{tf}"

    def build_stream_url(self) -> str:
        """Construct the WebSocket connection URL for active subscriptions."""
        if not self._subscriptions:
            return f"{self.base_url}/ws"

        streams = [
            self._format_stream_name(sym, tf) for sym, tf in sorted(self._subscriptions)
        ]
        if len(streams) == 1:
            return f"{self.base_url}/ws/{streams[0]}"

        stream_path = "/".join(streams)
        return f"{self.base_url}/stream?streams={stream_path}"

    def parse_message(self, raw_msg: str | dict[str, Any]) -> dict[str, Any] | None:
        """Parse a Binance WebSocket kline message and update the cache."""
        try:
            if isinstance(raw_msg, str):
                data = json.loads(raw_msg)
            elif isinstance(raw_msg, dict):
                data = raw_msg
            else:
                return None
        except Exception as e:
            logger.debug("Failed to parse Binance WS message: %s", e)
            return None

        if not isinstance(data, dict):
            return None

        # Unwrap combined stream payload
        if "data" in data and isinstance(data["data"], dict):
            data = data["data"]

        if data.get("e") != "kline" or "k" not in data:
            return None

        kline = data.get("k", {})
        if not isinstance(kline, dict):
            return None

        try:
            symbol = normalize_symbol(str(kline.get("s", "")))
            timeframe = normalize_timeframe(str(kline.get("i", "")))
            timestamp = int(kline.get("t", 0))
            open_ = float(kline.get("o", 0.0))
            high = float(kline.get("h", 0.0))
            low = float(kline.get("l", 0.0))
            close = float(kline.get("c", 0.0))
            volume = float(kline.get("v", 0.0))
            is_closed = bool(kline.get("x", False))

            if not symbol or not timeframe or timestamp <= 0:
                return None

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

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": timestamp,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "is_closed": is_closed,
            }
        except (ValueError, TypeError) as e:
            logger.debug("Invalid kline fields in Binance WS payload: %s", e)
            return None

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
                logger.debug("Error closing Binance WS connection: %s", e)
            self._ws = None

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run_loop(self) -> None:
        """Internal reconnect loop with backoff."""
        backoff = 1.0
        max_backoff = 30.0

        while self._running:
            url = self.build_stream_url()
            logger.info("Connecting to Binance WS stream: %s", url)
            try:
                async with websockets.connect(
                    url,
                    ping_interval=20,
                    ping_timeout=20,
                ) as ws:
                    self._ws = ws
                    self._connected = True
                    backoff = 1.0  # Reset backoff on success
                    logger.info("Connected to Binance WS stream: %s", url)

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
                logger.warning("Binance WS stream disconnected/error: %s. Reconnecting in %.1fs...", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, max_backoff)

        self._connected = False
        self._ws = None
