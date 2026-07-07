"""Deterministic unit tests for HyperliquidReadOnlyAdapter.

HTTP calls are mocked. No internet, no API, no secrets.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests
from requests import Response

from core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState
from core.retry import RetryPolicy
from execution.hyperliquid_adapter import (
    AccountState,
    Balance,
    ExchangeStatus,
    HyperliquidReadOnlyAdapter,
    OpenOrder,
    Position,
)


def _mock_response(json_data: dict | list, status_code: int = 200) -> Response:
    resp = Response()
    resp.status_code = status_code
    resp._json = json_data

    def _json(**kwargs):
        return resp._json

    resp.json = _json
    return resp


def _make_adapter(json_data: dict | list) -> tuple[HyperliquidReadOnlyAdapter, MagicMock]:
    session = MagicMock()
    session.post.return_value = _mock_response(json_data)
    adapter = HyperliquidReadOnlyAdapter(session=session)
    return adapter, session


ACCOUNT_STATE_RESPONSE = {
    "assetPositions": [
        {
            "position": {
                "coin": "BTC",
                "szi": "0.5",
                "entryPx": "50000.0",
                "unrealizedPnl": "250.0",
                "realizedPnl": "100.0",
                "leverage": {"type": "isolated", "value": 10},
                "liquidationPx": "45000.0",
                "margin": "2500.0",
            },
            "type": "oneWay",
        },
    ],
    "accountValue": "12500.0",
    "withdrawable": "10000.0",
    "totalMarginUsed": "2500.0",
}

OPEN_ORDERS_RESPONSE = [
    {
        "coin": "BTC",
        "side": "B",
        "limitPx": "49000.0",
        "sz": "0.1",
        "orderType": "Limit",
        "oid": 12345,
        "status": "open",
        "timestamp": 1700000000000,
    },
]

EXCHANGE_STATUS_RESPONSE = {
    "status": "ok",
    "contractsOpen": 42,
}

META_RESPONSE = {
    "universe": [
        {"name": "BTC", "index": 0, "szDecimals": 5},
        {"name": "ETH", "index": 1, "szDecimals": 4},
    ],
}

ORDER_STATUS_RESPONSE = {
    "order": {
        "oid": 12345,
        "status": "filled",
    },
}


class TestHyperliquidReadOnlyAdapter:

    def test_get_account_state_returns_dataclass(self):
        adapter, session = _make_adapter(ACCOUNT_STATE_RESPONSE)
        state = adapter.get_account_state("0xABC")
        assert isinstance(state, AccountState)
        assert state.address == "0xABC"
        assert state.account_value == 12500.0
        assert state.withdrawable == 10000.0

    def test_get_account_state_parses_positions(self):
        adapter, session = _make_adapter(ACCOUNT_STATE_RESPONSE)
        state = adapter.get_account_state("0xABC")
        assert len(state.positions) == 1
        pos = state.positions[0]
        assert pos.coin == "BTC"
        assert pos.size == 0.5
        assert pos.entry_px == 50000.0
        assert pos.unrealized_pnl == 250.0
        assert pos.realized_pnl == 100.0

    def test_get_account_state_sends_correct_payload(self):
        adapter, session = _make_adapter(ACCOUNT_STATE_RESPONSE)
        adapter.get_account_state("0xABC")
        session.post.assert_called_once()
        _, kwargs = session.post.call_args
        assert kwargs["json"] == {"type": "clearinghouseState", "user": "0xABC"}

    def test_get_account_state_empty_positions(self):
        adapter, session = _make_adapter({"assetPositions": [], "accountValue": "10000.0", "withdrawable": "8000.0"})
        state = adapter.get_account_state("0xABC")
        assert len(state.positions) == 0
        assert state.account_value == 10000.0

    def test_get_open_orders_returns_list_of_openorder(self):
        adapter, session = _make_adapter(OPEN_ORDERS_RESPONSE)
        orders = adapter.get_open_orders("0xABC")
        assert len(orders) == 1
        order = orders[0]
        assert isinstance(order, OpenOrder)
        assert order.coin == "BTC"
        assert order.side == "B"
        assert order.limit_px == 49000.0
        assert order.sz == 0.1
        assert order.order_type == "Limit"
        assert order.order_id == 12345
        assert order.status == "open"

    def test_get_open_orders_empty(self):
        adapter, session = _make_adapter([])
        orders = adapter.get_open_orders("0xABC")
        assert orders == []

    def test_get_open_orders_sends_correct_payload(self):
        adapter, session = _make_adapter(OPEN_ORDERS_RESPONSE)
        adapter.get_open_orders("0xABC")
        _, kwargs = session.post.call_args
        assert kwargs["json"] == {"type": "openOrders", "user": "0xABC"}

    def test_get_positions_returns_list_of_position(self):
        adapter, session = _make_adapter(ACCOUNT_STATE_RESPONSE)
        positions = adapter.get_positions("0xABC")
        assert len(positions) == 1
        pos = positions[0]
        assert isinstance(pos, Position)
        assert pos.coin == "BTC"

    def test_get_positions_empty(self):
        adapter, session = _make_adapter({"assetPositions": [], "accountValue": "10000.0", "withdrawable": "8000.0"})
        positions = adapter.get_positions("0xABC")
        assert positions == []

    def test_get_balance_returns_list_with_usd(self):
        adapter, session = _make_adapter(ACCOUNT_STATE_RESPONSE)
        balances = adapter.get_balance("0xABC")
        usd = next((b for b in balances if b.coin == "USD"), None)
        assert usd is not None
        assert usd.total == 12500.0
        assert usd.withdrawable == 10000.0

    def test_get_balance_includes_spot_assets(self):
        resp = {
            "accountValue": "12500.0",
            "withdrawable": "10000.0",
            "spotAssets": [
                {"coin": "USDC", "total": "5000.0", "withdrawable": "5000.0"},
            ],
        }
        adapter, session = _make_adapter(resp)
        balances = adapter.get_balance("0xABC")
        assert len(balances) == 2
        usdc = next((b for b in balances if b.coin == "USDC"), None)
        assert usdc is not None
        assert usdc.total == 5000.0

    def test_get_exchange_status_returns_dataclass(self):
        adapter, session = _make_adapter(EXCHANGE_STATUS_RESPONSE)
        status = adapter.get_exchange_status()
        assert isinstance(status, ExchangeStatus)
        assert status.status == "ok"
        assert status.contracts_open == 42

    def test_get_exchange_status_sends_correct_payload(self):
        adapter, session = _make_adapter(EXCHANGE_STATUS_RESPONSE)
        adapter.get_exchange_status()
        _, kwargs = session.post.call_args
        assert kwargs["json"] == {"type": "exchangeStatus"}

    def test_get_metadata_returns_dict(self):
        adapter, session = _make_adapter(META_RESPONSE)
        meta = adapter.get_metadata()
        assert "universe" in meta
        assert len(meta["universe"]) == 2

    def test_get_metadata_sends_correct_payload(self):
        adapter, session = _make_adapter(META_RESPONSE)
        adapter.get_metadata()
        _, kwargs = session.post.call_args
        assert kwargs["json"] == {"type": "meta"}

    def test_get_order_status_returns_dict(self):
        adapter, session = _make_adapter(ORDER_STATUS_RESPONSE)
        result = adapter.get_order_status("0xABC", 12345)
        assert result["order"]["oid"] == 12345
        assert result["order"]["status"] == "filled"

    def test_get_order_status_sends_correct_payload(self):
        adapter, session = _make_adapter(ORDER_STATUS_RESPONSE)
        adapter.get_order_status("0xABC", 12345)
        _, kwargs = session.post.call_args
        assert kwargs["json"] == {"type": "orderStatus", "user": "0xABC", "oid": 12345}

    def test_http_error_raises(self):
        session = MagicMock()
        resp = _mock_response({}, status_code=403)
        session.post.return_value = resp
        adapter = HyperliquidReadOnlyAdapter(session=session)
        with pytest.raises(Exception):
            adapter.get_exchange_status()

    def test_session_default_is_requests_session(self):
        adapter = HyperliquidReadOnlyAdapter()
        assert adapter.session is not None
        assert isinstance(adapter.session, __import__("requests").Session)

    def test_safe_float_handles_none(self):
        assert HyperliquidReadOnlyAdapter._safe_float(None) == 0.0

    def test_safe_float_handles_string(self):
        assert HyperliquidReadOnlyAdapter._safe_float("123.45") == 123.45

    def test_safe_float_handles_invalid(self):
        assert HyperliquidReadOnlyAdapter._safe_float("not-a-number") == 0.0

    def test_account_state_dataclass(self):
        s = AccountState(address="0xABC", account_value=100.0, withdrawable=50.0)
        assert s.address == "0xABC"
        assert s.account_value == 100.0
        assert s.withdrawable == 50.0

    def test_open_order_dataclass(self):
        o = OpenOrder(coin="BTC", side="A", limit_px=50000.0, sz=1.0, order_id=1)
        assert o.coin == "BTC"
        assert o.side == "A"
        assert o.limit_px == 50000.0
        assert o.sz == 1.0

    def test_position_dataclass(self):
        p = Position(coin="BTC", size=0.5, entry_px=50000.0, unrealized_pnl=100.0)
        assert p.coin == "BTC"
        assert p.size == 0.5

    def test_balance_dataclass(self):
        b = Balance(coin="USD", total=10000.0, withdrawable=8000.0)
        assert b.coin == "USD"
        assert b.total == 10000.0

    def test_exchange_status_dataclass(self):
        s = ExchangeStatus(status="ok", contracts_open=10)
        assert s.status == "ok"
        assert s.contracts_open == 10

    def test_logging_on_account_state(self):
        adapter, session = _make_adapter(ACCOUNT_STATE_RESPONSE)
        adapter.logger = MagicMock()
        adapter.get_account_state("0xABC")
        adapter.logger.info.assert_called()

    def test_logging_on_open_orders(self):
        adapter, session = _make_adapter(OPEN_ORDERS_RESPONSE)
        adapter.logger = MagicMock()
        adapter.get_open_orders("0xABC")
        adapter.logger.info.assert_called()

    def test_logging_on_exchange_status(self):
        adapter, session = _make_adapter(EXCHANGE_STATUS_RESPONSE)
        adapter.logger = MagicMock()
        adapter.get_exchange_status()
        adapter.logger.info.assert_called()

    @patch("execution.hyperliquid_adapter.requests.Session")
    def test_default_session_created(self, mock_session_class):
        mock_session_class.return_value = MagicMock()
        adapter = HyperliquidReadOnlyAdapter()
        assert adapter.session is not None

    def test_multiple_calls_use_same_session(self):
        session = MagicMock()
        session.post.return_value = _mock_response({})
        adapter = HyperliquidReadOnlyAdapter(session=session)
        adapter.get_exchange_status()
        adapter.get_metadata()
        assert session.post.call_count == 2


class TestHyperliquidAdapterRetry:

    def test_retry_succeeds_after_temporary_failures(self):
        session = MagicMock()
        responses = [
            _mock_response({}, status_code=503),
            _mock_response({}, status_code=503),
            _mock_response({"status": "ok", "contractsOpen": 5}),
        ]
        session.post.side_effect = responses
        retry = RetryPolicy(
            max_attempts=4,
            base_delay=0.01,
            max_delay=1.0,
            backoff_multiplier=2.0,
            retry_exceptions=(requests.exceptions.HTTPError,),
        )
        adapter = HyperliquidReadOnlyAdapter(
            session=session,
            retry_policy=retry,
        )
        status = adapter.get_exchange_status()
        assert status.status == "ok"

    def test_retry_exhausted_raises(self):
        session = MagicMock()
        session.post.return_value = _mock_response({}, status_code=503)
        retry = RetryPolicy(
            max_attempts=2,
            base_delay=0.01,
            max_delay=1.0,
            backoff_multiplier=2.0,
            retry_exceptions=(requests.exceptions.HTTPError,),
        )
        adapter = HyperliquidReadOnlyAdapter(
            session=session,
            retry_policy=retry,
        )
        with pytest.raises(Exception):
            adapter.get_exchange_status()


class TestHyperliquidAdapterCircuitBreaker:

    def test_circuit_blocks_after_repeated_failures(self):
        session = MagicMock()
        session.post.return_value = _mock_response({}, status_code=503)
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60.0)
        retry = RetryPolicy(
            max_attempts=1,
            base_delay=0.01,
            retry_exceptions=(requests.exceptions.HTTPError,),
        )
        adapter = HyperliquidReadOnlyAdapter(
            session=session,
            retry_policy=retry,
            circuit_breaker=cb,
        )

        with pytest.raises(Exception):
            adapter.get_exchange_status()
        assert cb.state == CircuitState.CLOSED

        with pytest.raises(Exception):
            adapter.get_exchange_status()
        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerOpenError):
            adapter.get_exchange_status()

    def test_circuit_allows_successful_calls(self):
        session = MagicMock()
        session.post.return_value = _mock_response({"status": "ok", "contractsOpen": 5})
        cb = CircuitBreaker(failure_threshold=3)
        adapter = HyperliquidReadOnlyAdapter(
            session=session,
            circuit_breaker=cb,
        )
        status = adapter.get_exchange_status()
        assert status.status == "ok"
        assert cb.state == CircuitState.CLOSED
