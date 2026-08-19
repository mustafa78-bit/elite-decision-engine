"""Unit tests for BinanceWSClient."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from market.stream.binance_ws import BinanceWSClient, normalize_stream_symbol
from market.stream.cache import CandleStreamCache


def test_normalize_stream_symbol():
    assert normalize_stream_symbol("BTC") == "BTCUSDT"
    assert normalize_stream_symbol("btc/usdt") == "BTCUSDT"
    assert normalize_stream_symbol("ETHUSDT") == "ETHUSDT"
    assert normalize_stream_symbol("SOLUSDC") == "SOLUSDC"


def test_binance_ws_subscriptions_and_url_building():
    cache = CandleStreamCache()
    client = BinanceWSClient(cache)

    assert client.get_subscriptions() == []
    assert client.build_stream_url() == "wss://stream.binance.com:9443/ws"

    client.add_subscription("BTC", "1h")
    assert client.get_subscriptions() == [("BTCUSDT", "1h")]
    assert client.build_stream_url() == "wss://stream.binance.com:9443/ws/btcusdt@kline_1h"

    client.add_subscription("ETHUSDT", "15m")
    assert client.get_subscriptions() == [("BTCUSDT", "1h"), ("ETHUSDT", "15m")]
    assert client.build_stream_url() == (
        "wss://stream.binance.com:9443/stream?streams=btcusdt@kline_1h/ethusdt@kline_15m"
    )

    client.remove_subscription("BTCUSDT", "1h")
    assert client.get_subscriptions() == [("ETHUSDT", "15m")]
    assert client.build_stream_url() == "wss://stream.binance.com:9443/ws/ethusdt@kline_15m"


def test_parse_single_kline_message():
    cache = CandleStreamCache()
    client = BinanceWSClient(cache)

    payload = {
        "e": "kline",
        "E": 1672515782136,
        "s": "BTCUSDT",
        "k": {
            "t": 1672515600000,
            "T": 1672519199999,
            "s": "BTCUSDT",
            "i": "1h",
            "o": "16500.00",
            "c": "16510.50",
            "h": "16520.00",
            "l": "16490.00",
            "v": "100.5",
            "x": False,
        },
    }

    parsed = client.parse_message(payload)
    assert parsed is not None
    assert parsed["symbol"] == "BTC"
    assert parsed["timeframe"] == "1h"
    assert parsed["timestamp"] == 1672515600000
    assert parsed["close"] == 16510.50
    assert parsed["is_closed"] is False

    # Verify cache was updated
    assert cache.has_symbol("BTC", "1h")
    df = cache.get_ohlcv("BTC", "1h")
    assert len(df) == 1
    assert df["close"].iloc[0] == 16510.50


def test_parse_combined_stream_kline_message():
    cache = CandleStreamCache()
    client = BinanceWSClient(cache)

    raw_json = json.dumps({
        "stream": "ethusdt@kline_15m",
        "data": {
            "e": "kline",
            "E": 1672515782136,
            "s": "ETHUSDT",
            "k": {
                "t": 1672515600000,
                "T": 1672516499999,
                "s": "ETHUSDT",
                "i": "15m",
                "o": "1200.00",
                "c": "1210.00",
                "h": "1215.00",
                "l": "1195.00",
                "v": "500.0",
                "x": True,
            },
        },
    })

    parsed = client.parse_message(raw_json)
    assert parsed is not None
    assert parsed["symbol"] == "ETH"
    assert parsed["timeframe"] == "15m"
    assert parsed["is_closed"] is True

    assert cache.has_symbol("ETHUSDT", "15m")


def test_parse_invalid_messages():
    cache = CandleStreamCache()
    client = BinanceWSClient(cache)

    assert client.parse_message("not json") is None
    assert client.parse_message({}) is None
    assert client.parse_message({"e": "depthUpdate"}) is None
    assert client.parse_message({"e": "kline", "k": "corrupt"}) is None


@pytest.mark.asyncio
async def test_binance_ws_client_lifecycle():
    cache = CandleStreamCache()
    client = BinanceWSClient(cache, symbols=["BTC"], timeframes=["1h"])

    assert not client.is_running
    assert not client.is_connected

    mock_ws = AsyncMock()

    async def msg_generator():
        yield json.dumps({
            "e": "kline",
            "k": {
                "s": "BTCUSDT",
                "i": "1h",
                "t": 1000,
                "o": "100",
                "h": "105",
                "l": "95",
                "c": "102",
                "v": "50",
                "x": True,
            },
        })
        while client.is_running:
            await asyncio.sleep(0.01)

    mock_ws.__aiter__.side_effect = lambda: msg_generator()

    with patch("websockets.connect", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_ws))):
        await client.start()
        assert client.is_running

        await asyncio.sleep(0.05)
        assert cache.has_symbol("BTC", "1h")

        await client.stop()
        assert not client.is_running
        assert not client.is_connected
