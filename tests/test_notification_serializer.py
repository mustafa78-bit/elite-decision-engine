import json

from notifications.serializer import serialize_event


def test_serialize_event_returns_json_string():
    result = serialize_event("TRADE_OPENED", {"symbol": "BTCUSDT"})
    assert isinstance(result, str)


def test_serialize_event_contains_event_field():
    result = json.loads(serialize_event("TRADE_OPENED", {"symbol": "BTCUSDT"}))
    assert result["event"] == "TRADE_OPENED"


def test_serialize_event_contains_timestamp():
    result = json.loads(serialize_event("TRADE_OPENED", {"symbol": "BTCUSDT"}))
    assert "timestamp" in result
    assert isinstance(result["timestamp"], str)
    assert result["timestamp"].endswith("+00:00") or "T" in result["timestamp"]


def test_serialize_event_preserves_payload():
    payload = {"symbol": "BTCUSDT", "side": "LONG", "entry": 50000.0}
    result = json.loads(serialize_event("TRADE_CLOSED", payload))
    assert result["payload"] == payload
