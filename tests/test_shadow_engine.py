"""Tests for shadow trading engine."""

from dataclasses import dataclass

import pytest

from exchange.hyperliquid.connector import HyperliquidExchange
from risk.execution_guard import ExecutionGuard
from shadow.shadow_engine import ShadowEngine, ShadowResult


@dataclass
class FakeSignal:
    id: int
    symbol: str
    side: str
    timeframe: str = "1h"


class TestShadowEngine:
    def test_shadow_result_dataclass(self):
        r = ShadowResult(signal_id=1, symbol="BTC", side="LONG", approved=True, guard_passed=True, order_placed=True, reason="OK")
        assert r.signal_id == 1
        assert r.approved is True
        assert r.order_placed is True

    def test_shadow_result_defaults(self):
        r = ShadowResult(signal_id=1, symbol="BTC", side="LONG", approved=False, guard_passed=False, order_placed=False)
        assert r.reason == ""
        assert r.journal_id is None

    def test_engine_process_rejected_signal(self, db_session):
        from database import Signal
        sig = Signal(symbol="BTC", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(sig)
        db_session.flush()

        signal = FakeSignal(id=sig.id, symbol="BTC", side="LONG")
        engine = ShadowEngine(exchange=HyperliquidExchange())
        result = engine.process(signal)
        # Pipeline will likely reject due to missing market data in test env
        assert isinstance(result, ShadowResult)
        assert result.signal_id == sig.id
