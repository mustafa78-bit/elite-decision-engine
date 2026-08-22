"""Regression test for the event-loop freeze fixed 2026-08-22.

_broadcast_market() used to call get_mip().get_asset("BTC") directly --
synchronous, and on a cache miss running the full news/whale/funding/OI
intelligence enrichment fan-out (real blocking requests.get() calls),
confirmed taking 26-56s under real load (scanner/core.py's own comment).
Called every 30s from an async function with no asyncio.to_thread
wrapping, that froze the ENTIRE event loop for the full duration --
confirmed live as the real cause of 41 overnight backend freezes a
process watchdog had to recover from.

This test proves the fix directly: a slow, blocking get_asset() call must
NOT prevent other concurrently-scheduled async work from running.
"""

import asyncio
import time
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

import api.main as main_module
from api.websocket.manager import WebSocketManager
from market.models.asset import Asset, AssetMetadata


def _make_btc_asset() -> Asset:
    df = pd.DataFrame({
        "timestamp": [1, 2, 3],
        "open": [100.0, 101.0, 102.0],
        "high": [103.0, 104.0, 105.0],
        "low": [99.0, 100.0, 101.0],
        "close": [101.0, 102.0, 103.0],
        "volume": [10.0, 11.0, 12.0],
    })
    return Asset(
        symbol="BTC",
        metadata=AssetMetadata(symbol="BTC"),
        price=103.0,
        ohlcv=df,
        indicators={"ema20": 100, "ema50": 98, "ema200": 95, "atr": 1.0, "rsi": 55},
        context={"btc": {"btc_trend": "NEUTRAL"}},
    )


@pytest.fixture
def mock_manager(monkeypatch):
    manager = MagicMock(spec=WebSocketManager)
    manager.broadcast = AsyncMock()
    monkeypatch.setattr(main_module, "manager", manager)
    return manager


BLOCKING_CALL_SECONDS = 0.3


def _slow_get_asset(symbol: str) -> Asset:
    # Stands in for the real, slow, synchronous news/whale/funding/OI
    # enrichment fan-out on a cache miss.
    time.sleep(BLOCKING_CALL_SECONDS)
    return _make_btc_asset()


async def test_broadcast_market_does_not_block_the_event_loop(monkeypatch, mock_manager):
    mock_mip = MagicMock()
    mock_mip.get_asset = _slow_get_asset
    monkeypatch.setattr(main_module, "get_mip", lambda: mock_mip)

    tick_count = 0

    async def ticker():
        nonlocal tick_count
        while True:
            await asyncio.sleep(0.02)
            tick_count += 1

    ticker_task = asyncio.create_task(ticker())
    try:
        await main_module._broadcast_market()
    finally:
        ticker_task.cancel()
        with suppress(asyncio.CancelledError):
            await ticker_task

    # BLOCKING_CALL_SECONDS / 0.02s per tick -- if the event loop were
    # blocked for the full sleep (the bug), tick_count would be 0 or 1
    # (only whatever squeezed in before the blocking call started).
    assert tick_count >= 5, (
        f"only {tick_count} ticks completed during a {BLOCKING_CALL_SECONDS}s blocking "
        "get_asset() call -- the event loop was blocked, not just the caller"
    )
