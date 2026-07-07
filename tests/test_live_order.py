"""Deterministic unit tests for LiveOrderStatus enum."""

from __future__ import annotations

from execution.live_order import LiveOrderStatus


class TestLiveOrderStatus:

    def test_enum_values(self):
        assert LiveOrderStatus.NEW.value == "NEW"
        assert LiveOrderStatus.PENDING.value == "PENDING"
        assert LiveOrderStatus.PARTIALLY_FILLED.value == "PARTIALLY_FILLED"
        assert LiveOrderStatus.FILLED.value == "FILLED"
        assert LiveOrderStatus.CANCELED.value == "CANCELED"
        assert LiveOrderStatus.REJECTED.value == "REJECTED"
        assert LiveOrderStatus.EXPIRED.value == "EXPIRED"

    def test_enum_membership(self):
        assert LiveOrderStatus.NEW in LiveOrderStatus
        assert LiveOrderStatus.FILLED in LiveOrderStatus

    def test_enum_from_string(self):
        assert LiveOrderStatus("NEW") == LiveOrderStatus.NEW
        assert LiveOrderStatus("FILLED") == LiveOrderStatus.FILLED
        assert LiveOrderStatus("CANCELED") == LiveOrderStatus.CANCELED

    def test_enum_is_str_enum(self):
        assert isinstance(LiveOrderStatus.NEW.value, str)

    def test_enum_all_values_are_strings(self):
        for status in LiveOrderStatus:
            assert isinstance(status.value, str)
