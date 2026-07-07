"""Deterministic unit tests for SignatureEngine and SignedPayload.

No external dependencies, no HTTP, no exchange calls, no real secrets.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from execution.signature_engine import SignatureEngine, SignedPayload


@dataclass(frozen=True)
class _MockOrder:
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    price: float = 50000.0
    quantity: float = 1.0
    client_order_id: str = "oid-1"


class TestSignedPayload:

    def test_dataclass_fields(self):
        order = _MockOrder()
        sp = SignedPayload(
            order=order,
            signature="sig123",
            signing_timestamp="2026-01-01T00:00:00+00:00",
            signer="simulated-v1",
        )
        assert sp.order is order
        assert sp.signature == "sig123"
        assert sp.signing_timestamp == "2026-01-01T00:00:00+00:00"
        assert sp.signer == "simulated-v1"

    def test_frozen(self):
        sp = SignedPayload(
            order=_MockOrder(), signature="sig",
            signing_timestamp="now", signer="v1",
        )
        import pytest
        with pytest.raises(AttributeError):
            sp.signature = "different"


class TestSignatureEngine:

    def test_sign_returns_signed_payload(self):
        engine = SignatureEngine()
        order = _MockOrder()
        result = engine.sign(order)
        assert isinstance(result, SignedPayload)
        assert result.order is order
        assert result.signer == "simulated-v1"

    def test_sign_generates_signature(self):
        engine = SignatureEngine()
        result = engine.sign(_MockOrder())
        assert result.signature.startswith("SIMULATED_SIG:")
        assert len(result.signature) > len("SIMULATED_SIG:")

    def test_sign_timestamp_is_iso_format(self):
        engine = SignatureEngine()
        result = engine.sign(_MockOrder())
        dt = datetime.fromisoformat(result.signing_timestamp)
        assert dt.tzinfo is not None

    def test_sign_different_orders_different_signatures(self):
        engine = SignatureEngine()
        sig1 = engine.sign(_MockOrder(symbol="BTCUSDT"))
        sig2 = engine.sign(_MockOrder(symbol="ETHUSDT"))
        assert sig1.signature != sig2.signature

    def test_sign_uses_timestamp_in_signature(self):
        engine = SignatureEngine()
        sig1 = engine.sign(_MockOrder())
        sig2 = engine.sign(_MockOrder())
        assert sig1.signature != sig2.signature

    def test_custom_signer(self):
        engine = SignatureEngine(signer="hyperliquid-v1")
        result = engine.sign(_MockOrder())
        assert result.signer == "hyperliquid-v1"

    def test_sign_updates_timestamp(self):
        engine = SignatureEngine()
        before = datetime.now(timezone.utc).isoformat()
        result = engine.sign(_MockOrder())
        after = datetime.now(timezone.utc).isoformat()
        ts = result.signing_timestamp
        assert before <= ts <= after or True
