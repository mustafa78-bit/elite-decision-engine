"""Unit tests for HyperliquidWSClient."""

import asyncio
import json
import time
from unittest.mock import AsyncMock, patch

import pytest

from market.stream.cache import CandleStreamCache
from market.stream.hyperliquid_ws import HyperliquidWSClient, normalize_stream_symbol


def test_normalize_stream_symbol():
    assert normalize_stream_symbol("BTCUSDT") == "BTC"
    assert normalize_stream_symbol("btc/usdt") == "BTC"
    assert normalize_stream_symbol("BTC") == "BTC"


def test_hyperliquid_ws_subscriptions_and_messages():
    cache = CandleStreamCache()
    client = HyperliquidWSClient(cache)

    assert client.get_subscriptions() == []
    assert client.build_subscribe_messages() == []

    client.add_subscription("BTCUSDT", "1h")
    assert client.get_subscriptions() == [("BTC", "1h")]
    assert client.build_subscribe_messages() == [
        {"method": "subscribe", "subscription": {"type": "candle", "coin": "BTC", "interval": "1h"}}
    ]

    client.add_subscription("ETHUSDT", "15m")
    msgs = client.build_subscribe_messages()
    assert len(msgs) == 2

    client.remove_subscription("BTCUSDT", "1h")
    assert client.get_subscriptions() == [("ETH", "15m")]


def test_parse_candle_message_closed_candle():
    cache = CandleStreamCache()
    client = HyperliquidWSClient(cache)

    past_close_time = (time.time() - 3600) * 1000  # already closed, in the past
    payload = {
        "channel": "candle",
        "data": [{
            "t": 1672324800000,
            "T": past_close_time,
            "s": "BTC",
            "i": "1h",
            "o": "16649.5",
            "c": "16677",
            "h": "16677",
            "l": "16608",
            "v": "2.081",
            "n": 42,
        }],
    }

    parsed = client.parse_message(payload)
    assert len(parsed) == 1
    candle = parsed[0]
    assert candle["symbol"] == "BTC"
    assert candle["timeframe"] == "1h"
    assert candle["close"] == 16677.0
    assert candle["is_closed"] is True

    assert cache.has_symbol("BTC", "1h")
    df = cache.get_ohlcv("BTC", "1h")
    assert len(df) == 1


def test_parse_candle_message_forming_candle_not_closed():
    cache = CandleStreamCache()
    client = HyperliquidWSClient(cache)

    future_close_time = (time.time() + 3600) * 1000  # still forming
    payload = {
        "channel": "candle",
        "data": [{
            "t": 1672324800000,
            "T": future_close_time,
            "s": "ETH",
            "i": "15m",
            "o": "1200",
            "c": "1210",
            "h": "1215",
            "l": "1195",
            "v": "500",
        }],
    }

    parsed = client.parse_message(payload)
    assert len(parsed) == 1
    assert parsed[0]["is_closed"] is False


def test_parse_invalid_messages():
    cache = CandleStreamCache()
    client = HyperliquidWSClient(cache)

    assert client.parse_message("not json") == []
    assert client.parse_message({}) == []
    assert client.parse_message({"channel": "trades", "data": []}) == []
    assert client.parse_message({"channel": "candle", "data": "corrupt"}) == []
    assert client.parse_message({"channel": "candle", "data": [{"s": "", "i": "1h"}]}) == []


@pytest.mark.asyncio
async def test_hyperliquid_ws_client_lifecycle():
    cache = CandleStreamCache()
    client = HyperliquidWSClient(cache, symbols=["BTC"], timeframes=["1h"])

    assert not client.is_running
    assert not client.is_connected

    mock_ws = AsyncMock()

    async def msg_generator():
        yield json.dumps({
            "channel": "candle",
            "data": [{
                "t": 1000, "T": (time.time() + 3600) * 1000,
                "s": "BTC", "i": "1h",
                "o": "100", "h": "105", "l": "95", "c": "102", "v": "50",
            }],
        })
        while client.is_running:
            await asyncio.sleep(0.01)

    mock_ws.__aiter__.side_effect = lambda: msg_generator()

    with patch("websockets.connect", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_ws))):
        await client.start()
        assert client.is_running

        await asyncio.sleep(0.05)
        assert cache.has_symbol("BTC", "1h")
        mock_ws.send.assert_called_once()
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent == {"method": "subscribe", "subscription": {"type": "candle", "coin": "BTC", "interval": "1h"}}

        await client.stop()
        assert not client.is_running
        assert not client.is_connected


@pytest.mark.asyncio
async def test_hyperliquid_ws_reconnects_and_resubscribes_after_drop():
    cache = CandleStreamCache()
    client = HyperliquidWSClient(cache, symbols=["BTC"], timeframes=["1h"])

    call_count = 0

    class _FailThenSucceedConnect:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("simulated drop")
            mock_ws = AsyncMock()

            async def empty_gen():
                while client.is_running:
                    await asyncio.sleep(0.01)

            mock_ws.__aiter__.side_effect = lambda: empty_gen()
            return mock_ws

        async def __aexit__(self, *a):
            return False

    with patch("websockets.connect", side_effect=_FailThenSucceedConnect):
        await client.start()
        # First connect attempt fails immediately; the client's own backoff
        # (starts at 1.0s) must elapse in real time before it retries.
        await asyncio.sleep(1.2)
        assert call_count >= 2
        await client.stop()
