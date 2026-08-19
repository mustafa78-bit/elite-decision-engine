"""Tests for BinanceCandleStream."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from websockets.exceptions import ConnectionClosedOK

from market.stream.cache import CandleStreamCache
from market.stream.binance_ws import BinanceCandleStream


def test_format_stream_name_and_subscribe_payload():
    subs = [("BTC/USDT", "1h"), ("ETH-USDT", "15m")]
    cache = CandleStreamCache()
    stream = BinanceCandleStream(subscriptions=subs, cache=cache)

    payload = stream.build_subscribe_payload(request_id=42)
    assert payload == {
        "method": "SUBSCRIBE",
        "params": ["btcusdt@kline_1h", "ethusdt@kline_15m"],
        "id": 42,
    }


def test_process_kline_message():
    cache = CandleStreamCache()
    stream = BinanceCandleStream(subscriptions=[("BTCUSDT", "1h")], cache=cache)

    kline_msg = {
        "e": "kline",
        "E": 1600000001000,
        "s": "BTCUSDT",
        "k": {
            "t": 1600000000000,
            "T": 1600003599999,
            "s": "BTCUSDT",
            "i": "1h",
            "f": 100,
            "L": 200,
            "o": "50000.0",
            "c": "50500.0",
            "h": "51000.0",
            "l": "49500.0",
            "v": "12.345",
            "n": 100,
            "x": False,
            "q": "620000.0",
            "V": "6.0",
            "Q": "300000.0",
            "B": "0",
        },
    }

    stream._process_message(json.dumps(kline_msg))

    df = cache.get("BTCUSDT", "1h")
    assert df is not None
    assert len(df) == 1
    assert df.iloc[0]["timestamp"] == 1600000000000
    assert df.iloc[0]["open"] == 50000.0
    assert df.iloc[0]["high"] == 51000.0
    assert df.iloc[0]["low"] == 49500.0
    assert df.iloc[0]["close"] == 50500.0
    assert df.iloc[0]["volume"] == 12.345


def test_process_combined_stream_wrapped_message():
    cache = CandleStreamCache()
    stream = BinanceCandleStream(subscriptions=[("ETHUSDT", "15m")], cache=cache)

    wrapped_msg = {
        "stream": "ethusdt@kline_15m",
        "data": {
            "e": "kline",
            "s": "ETHUSDT",
            "k": {
                "t": 1700000000000,
                "s": "ETHUSDT",
                "i": "15m",
                "o": "3000.0",
                "h": "3050.0",
                "l": "2990.0",
                "c": "3020.0",
                "v": "50.0",
            },
        },
    }

    stream._process_message(json.dumps(wrapped_msg))

    df = cache.get("ETHUSDT", "15m")
    assert df is not None
    assert df.iloc[0]["close"] == 3020.0


def test_process_non_kline_and_malformed_messages():
    cache = CandleStreamCache()
    stream = BinanceCandleStream(subscriptions=[("BTCUSDT", "1h")], cache=cache)

    # Subscribe confirmation message
    stream._process_message(json.dumps({"result": None, "id": 1}))
    # Malformed JSON
    stream._process_message("NOT_VALID_JSON")
    # Non-dict JSON
    stream._process_message(json.dumps([1, 2, 3]))

    assert cache.get("BTCUSDT", "1h") is None


@pytest.mark.asyncio
async def test_run_loop_subscription_and_receiving():
    cache = CandleStreamCache()
    stream = BinanceCandleStream(subscriptions=[("BTCUSDT", "1h")], cache=cache)

    mock_ws = AsyncMock()
    kline_data = json.dumps({
        "e": "kline",
        "k": {
            "t": 1600000000000,
            "s": "BTCUSDT",
            "i": "1h",
            "o": "100", "h": "110", "l": "90", "c": "105", "v": "10",
        },
    })

    # Set up mock ws iterator
    async def msg_generator():
        yield kline_data
        # Stop loop after first message
        stream._running = False

    mock_ws.__aiter__.side_effect = msg_generator

    class MockConnectContext:
        async def __aenter__(self):
            return mock_ws

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("websockets.connect", return_value=MockConnectContext()):
        stream._running = True
        await stream._run_loop()

    # Assert subscription message sent
    mock_ws.send.assert_called_once()
    sent_payload = json.loads(mock_ws.send.call_args[0][0])
    assert sent_payload["method"] == "SUBSCRIBE"
    assert sent_payload["params"] == ["btcusdt@kline_1h"]

    # Assert cache updated
    df = cache.get("BTCUSDT", "1h")
    assert df is not None
    assert df.iloc[0]["close"] == 105.0


@pytest.mark.asyncio
async def test_reconnect_and_resubscribe_on_disconnect():
    cache = CandleStreamCache()
    stream = BinanceCandleStream(
        subscriptions=[("SOLUSDT", "1h")],
        cache=cache,
        backoff_factor=0.01,
        max_backoff=0.02,
    )

    connect_attempts = 0
    mock_ws = AsyncMock()

    async def msg_generator_1():
        # First connection immediately drops
        raise ConnectionClosedOK(rcvd=None, sent=None)
        yield ""  # pragma: no cover

    async def msg_generator_2():
        # Second connection yields one message then stops loop
        yield json.dumps({
            "e": "kline",
            "k": {
                "t": 1600000000000,
                "s": "SOLUSDT",
                "i": "1h",
                "o": "10", "h": "12", "l": "9", "c": "11", "v": "100",
            },
        })
        stream._running = False

    class DynamicConnectContext:
        async def __aenter__(self):
            nonlocal connect_attempts
            connect_attempts += 1
            if connect_attempts == 1:
                mock_ws.__aiter__.side_effect = msg_generator_1
            else:
                mock_ws.__aiter__.side_effect = msg_generator_2
            return mock_ws

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("websockets.connect", return_value=DynamicConnectContext()), \
         patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        stream._running = True
        await stream._run_loop()

    assert connect_attempts == 2
    assert mock_sleep.called
    assert cache.get("SOLUSDT", "1h") is not None


@pytest.mark.asyncio
async def test_context_manager_lifecycle():
    cache = CandleStreamCache()
    stream = BinanceCandleStream(subscriptions=[("BTCUSDT", "1h")], cache=cache)

    mock_run_loop = AsyncMock()
    with patch.object(stream, "_run_loop", mock_run_loop):
        async with stream:
            assert stream._running is True
            assert stream._task is not None

        assert stream._running is False
