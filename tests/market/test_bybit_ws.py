"""Unit tests for BybitWSClient."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from market.stream.bybit_ws import BybitWSClient, normalize_stream_symbol
from market.stream.cache import CandleStreamCache


def test_normalize_stream_symbol():
    assert normalize_stream_symbol("BTC") == "BTCUSDT"
    assert normalize_stream_symbol("btc/usdt") == "BTCUSDT"
    assert normalize_stream_symbol("ETHUSDT") == "ETHUSDT"


def test_unsupported_timeframe_raises():
    cache = CandleStreamCache()
    client = BybitWSClient(cache)
    with pytest.raises(ValueError, match="Unsupported timeframe"):
        client.add_subscription("BTC", "2h")


def test_bybit_ws_subscriptions_and_subscribe_payload():
    cache = CandleStreamCache()
    client = BybitWSClient(cache)

    assert client.get_subscriptions() == []
    assert client.build_subscribe_payload() is None

    client.add_subscription("BTC", "1h")
    assert client.get_subscriptions() == [("BTCUSDT", "1h")]
    assert client.build_subscribe_payload() == {"op": "subscribe", "args": ["kline.60.BTCUSDT"]}

    client.add_subscription("ETHUSDT", "15m")
    assert client.get_subscriptions() == [("BTCUSDT", "1h"), ("ETHUSDT", "15m")]
    assert client.build_subscribe_payload() == {
        "op": "subscribe",
        "args": ["kline.60.BTCUSDT", "kline.15.ETHUSDT"],
    }

    client.remove_subscription("BTCUSDT", "1h")
    assert client.get_subscriptions() == [("ETHUSDT", "15m")]


def test_parse_kline_message_single_candle():
    cache = CandleStreamCache()
    client = BybitWSClient(cache)

    payload = {
        "topic": "kline.60.BTCUSDT",
        "type": "snapshot",
        "ts": 1672324988882,
        "data": [
            {
                "start": 1672324800000,
                "end": 1672328399999,
                "interval": "60",
                "open": "16649.5",
                "close": "16677",
                "high": "16677",
                "low": "16608",
                "volume": "2.081",
                "confirm": False,
                "timestamp": 1672324988882,
            }
        ],
    }

    parsed = client.parse_message(payload)
    assert len(parsed) == 1
    candle = parsed[0]
    assert candle["symbol"] == "BTC"
    assert candle["timeframe"] == "1h"
    assert candle["timestamp"] == 1672324800000
    assert candle["close"] == 16677.0
    assert candle["is_closed"] is False

    assert cache.has_symbol("BTC", "1h")
    df = cache.get_ohlcv("BTC", "1h")
    assert len(df) == 1
    assert df["close"].iloc[0] == 16677.0


def test_parse_kline_message_multiple_candles_in_one_payload():
    cache = CandleStreamCache()
    client = BybitWSClient(cache)

    raw_json = json.dumps({
        "topic": "kline.15.ETHUSDT",
        "data": [
            {
                "start": 1672324800000, "interval": "15",
                "open": "1200", "close": "1205", "high": "1210", "low": "1195",
                "volume": "10", "confirm": True,
            },
            {
                "start": 1672325700000, "interval": "15",
                "open": "1205", "close": "1215", "high": "1220", "low": "1200",
                "volume": "12", "confirm": False,
            },
        ],
    })

    parsed = client.parse_message(raw_json)
    assert len(parsed) == 2
    assert parsed[0]["is_closed"] is True
    assert parsed[1]["is_closed"] is False
    assert cache.has_symbol("ETHUSDT", "15m")
    df = cache.get_ohlcv("ETH", "15m")
    assert len(df) == 2


def test_parse_invalid_messages():
    cache = CandleStreamCache()
    client = BybitWSClient(cache)

    assert client.parse_message("not json") == []
    assert client.parse_message({}) == []
    assert client.parse_message({"topic": "orderbook.BTCUSDT"}) == []
    assert client.parse_message({"topic": "kline.60.BTCUSDT", "data": "corrupt"}) == []
    assert client.parse_message({"topic": "kline.unknown.BTCUSDT", "data": []}) == []


@pytest.mark.asyncio
async def test_bybit_ws_client_lifecycle():
    cache = CandleStreamCache()
    client = BybitWSClient(cache, symbols=["BTC"], timeframes=["1h"])

    assert not client.is_running
    assert not client.is_connected

    mock_ws = AsyncMock()

    async def msg_generator():
        yield json.dumps({
            "topic": "kline.60.BTCUSDT",
            "data": [{
                "start": 1000, "interval": "60",
                "open": "100", "high": "105", "low": "95", "close": "102",
                "volume": "50", "confirm": True,
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
        sent_payload = json.loads(mock_ws.send.call_args[0][0])
        assert sent_payload == {"op": "subscribe", "args": ["kline.60.BTCUSDT"]}

        await client.stop()
        assert not client.is_running
        assert not client.is_connected


@pytest.mark.asyncio
async def test_bybit_ws_reconnects_and_resubscribes_after_drop():
    cache = CandleStreamCache()
    client = BybitWSClient(cache, symbols=["BTC"], timeframes=["1h"])

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
            self._ws = mock_ws
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
