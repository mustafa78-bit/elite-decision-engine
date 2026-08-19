"""Binance WebSocket client for real-time kline/candle streaming."""

import asyncio
import json
import logging
from typing import List, Tuple, Optional, Any
import websockets
from websockets.exceptions import ConnectionClosed

from market.stream.cache import CandleStreamCache

logger = logging.getLogger(__name__)

# Default Binance WebSocket Stream endpoint URL
DEFAULT_WS_URL = "wss://stream.binance.com:9443/ws"


class BinanceCandleStream:
    """
    WebSocket client streaming Binance klines into a CandleStreamCache.

    Maintains active WebSocket subscriptions for requested (symbol, timeframe) pairs,
    parsing incoming kline event ticks and writing/updating the cache.
    Automatically reconnects with exponential backoff on disconnect.
    """

    def __init__(
        self,
        subscriptions: List[Tuple[str, str]],
        cache: CandleStreamCache,
        ws_url: str = DEFAULT_WS_URL,
        backoff_factor: float = 2.0,
        max_backoff: float = 60.0,
    ):
        """
        Initialize stream client with list of (symbol, timeframe) pairs.

        :param subscriptions: List of tuples e.g. [("BTCUSDT", "1h"), ("ETHUSDT", "15m")]
        :param cache: CandleStreamCache instance to store candles into
        :param ws_url: Binance WS endpoint URL
        :param backoff_factor: Multiplier for exponential backoff retry
        :param max_backoff: Cap on backoff retry delay in seconds
        """
        self.subscriptions = subscriptions
        self.cache = cache
        self.ws_url = ws_url
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff

        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._ws: Any = None

    @staticmethod
    def _format_stream_name(symbol: str, timeframe: str) -> str:
        """Format stream name per Binance spec (e.g. btcusdt@kline_1h)."""
        sym = symbol.lower().replace("/", "").replace("-", "")
        return f"{sym}@kline_{timeframe}"

    def build_subscribe_payload(self, request_id: int = 1) -> dict:
        """Construct the SUBSCRIBE JSON RPC payload for all configured subscriptions."""
        params = [
            self._format_stream_name(symbol, tf)
            for symbol, tf in self.subscriptions
        ]
        return {
            "method": "SUBSCRIBE",
            "params": params,
            "id": request_id,
        }

    async def start(self) -> None:
        """Start the background stream processing task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop stream processing task and close active connection."""
        self._running = False
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception as e:
                logger.debug("Error closing WebSocket connection: %s", e)
            self._ws = None

        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def _run_loop(self) -> None:
        """Main loop managing connection, subscription, message receiving, and reconnection."""
        attempt = 0
        while self._running:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self._ws = ws
                    attempt = 0  # Reset backoff on successful connection
                    logger.info("Connected to Binance WebSocket at %s", self.ws_url)

                    # Send subscription request if subscriptions are specified
                    if self.subscriptions:
                        payload = self.build_subscribe_payload()
                        await ws.send(json.dumps(payload))
                        logger.info("Sent subscription request for %d streams", len(self.subscriptions))

                    async for message in ws:
                        if not self._running:
                            break
                        self._process_message(message)

            except ConnectionClosed as e:
                logger.warning("Binance WebSocket connection closed: %s", e)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Binance WebSocket error: %s", e)

            self._ws = None
            if not self._running:
                break

            attempt += 1
            delay = min(self.backoff_factor ** attempt, self.max_backoff)
            logger.info("Reconnecting to Binance WebSocket in %.2f seconds (attempt %d)", delay, attempt)
            await asyncio.sleep(delay)

    def _process_message(self, raw_message: str) -> None:
        """Parse raw incoming WebSocket message string and route to cache if kline event."""
        try:
            msg = json.loads(raw_message)
        except Exception as e:
            logger.warning("Failed to parse JSON message from Binance WS: %s", e)
            return

        # Check if message is a kline payload
        if not isinstance(msg, dict):
            return

        # Handle stream wrapper if combined stream format was used
        data = msg.get("data", msg)
        if not isinstance(data, dict):
            return

        if data.get("e") != "kline" or "k" not in data:
            # Non-kline message (e.g. subscribe confirmation result)
            return

        kline = data["k"]
        symbol = kline.get("s")  # Symbol, e.g. "BTCUSDT"
        timeframe = kline.get("i")  # Interval, e.g. "1h"

        if not symbol or not timeframe:
            return

        try:
            candle = {
                "timestamp": kline["t"],  # Kline start time (ms)
                "open": kline["o"],
                "high": kline["h"],
                "low": kline["l"],
                "close": kline["c"],
                "volume": kline["v"],
            }
            self.cache.update(symbol, timeframe, candle)
        except KeyError as e:
            logger.warning("Missing required field in kline payload: %s", e)
        except Exception as e:
            logger.error("Error updating cache from kline payload: %s", e)
