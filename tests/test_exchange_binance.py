"""Tests for Binance exchange connector."""

from decimal import Decimal

import pytest

from exchange.binance.connector import BinanceExchange
from exchange.exceptions import (
    AuthenticationError,
    ExchangeConnectionError,
    MarketDataError,
)
from exchange.models import Order


class TestBinanceExchange:
    def test_implements_adapter(self):
        ex = BinanceExchange()
        assert ex.name == "binance"
        assert ex.trading_enabled() is True

    def test_account_balance_paper(self):
        ex = BinanceExchange()
        balances = ex.account_balance()
        assert len(balances) >= 1
        assert balances[0].currency == "USDT"

    def test_ticker_fails_without_network(self):
        ex = BinanceExchange(timeout=1)
        with pytest.raises((MarketDataError, ExchangeConnectionError)):
            ex.ticker("THISISFAKE123")

    def test_candles_fails_without_network(self):
        ex = BinanceExchange(timeout=1)
        with pytest.raises((MarketDataError, ExchangeConnectionError)):
            ex.candles("THISISFAKE123")

    def test_create_order_paper(self):
        ex = BinanceExchange()
        order = Order(id="", symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"), price=Decimal("50000"))
        filled = ex.create_order(order)
        assert filled.status == "FILLED"
        assert filled.filled_quantity == Decimal("0.1")

    def test_cancel_order(self):
        ex = BinanceExchange()
        order = Order(id="", symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        filled = ex.create_order(order)
        assert ex.cancel_order(filled.id, "BTCUSDT") is True

    def test_cancel_nonexistent(self):
        ex = BinanceExchange()
        assert ex.cancel_order("nonexistent", "BTCUSDT") is False

    def test_order_status(self):
        ex = BinanceExchange()
        order = Order(id="", symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        filled = ex.create_order(order)
        result = ex.order_status(filled.id, "BTCUSDT")
        assert result is not None
        assert result.status == "FILLED"

    def test_order_status_nonexistent(self):
        ex = BinanceExchange()
        assert ex.order_status("nonexistent", "BTCUSDT") is None

    def test_order_history(self):
        ex = BinanceExchange()
        o1 = Order(id="", symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=Decimal("0.1"))
        o2 = Order(id="", symbol="ETHUSDT", side="SELL", order_type="MARKET", quantity=Decimal("1"))
        ex.create_order(o1)
        ex.create_order(o2)
        assert len(ex.order_history("BTCUSDT")) == 1
        assert len(ex.order_history("ETHUSDT")) == 1

    def test_authenticated_requests_fail_without_secret(self):
        ex = BinanceExchange(api_key="test_key")
        with pytest.raises(AuthenticationError):
            ex._signed_request("GET", "/api/v3/account")

    def test_positions_with_paper_order(self, db_session, monkeypatch):
        from database import PaperOrder, Signal, Trade
        # Seed Signal for DB integrity if checked
        sig = Signal(id=1, symbol="BTCUSDT", side="BUY", approved=True)
        db_session.add(sig)
        db_session.flush()

        trade = Trade(id=10, signal_id=1, symbol="BTCUSDT", side="LONG", entry=50000.0, status="OPEN")
        db_session.add(trade)
        db_session.flush()

        # Create matching PaperOrder
        order = PaperOrder(id=100, symbol="BTCUSDT", side="BUY", quantity=1.5, filled_quantity=1.2, status="FILLED", trade_id=10)
        db_session.add(order)
        db_session.flush()

        ex = BinanceExchange()
        # Mock ticker to return a specific Ticker object
        from exchange.models import Ticker
        monkeypatch.setattr(ex, "ticker", lambda sym: Ticker(
            symbol=sym, bid=Decimal("51000"), ask=Decimal("51100"), last=Decimal("51050"),
            volume_24h=Decimal("0"), high_24h=Decimal("0"), low_24h=Decimal("0"), change_24h=Decimal("0")
        ))

        pos_list = ex.positions()
        assert len(pos_list) == 1
        pos = pos_list[0]
        assert pos.symbol == "BTCUSDT"
        assert pos.quantity == Decimal("1.2")  # filled_quantity from PaperOrder
        assert pos.entry_price == Decimal("50000.0")
        assert pos.current_price == Decimal("51050")

    def test_positions_no_paper_order(self, db_session, monkeypatch):
        from database import Signal, Trade
        sig = Signal(id=2, symbol="ETHUSDT", side="BUY", approved=True)
        db_session.add(sig)
        db_session.flush()

        trade = Trade(id=20, signal_id=2, symbol="ETHUSDT", side="LONG", entry=3000.0, status="OPEN")
        db_session.add(trade)
        db_session.flush()

        ex = BinanceExchange()
        from exchange.models import Ticker
        monkeypatch.setattr(ex, "ticker", lambda sym: Ticker(
            symbol=sym, bid=Decimal("3050"), ask=Decimal("3060"), last=Decimal("3055"),
            volume_24h=Decimal("0"), high_24h=Decimal("0"), low_24h=Decimal("0"), change_24h=Decimal("0")
        ))

        pos_list = ex.positions()
        # trade with id 20 has no matching PaperOrder, so it should fallback to Decimal("0") quantity
        assert len(pos_list) == 1
        pos = pos_list[0]
        assert pos.symbol == "ETHUSDT"
        assert pos.quantity == Decimal("0")
        assert pos.current_price == Decimal("3055")

    def test_positions_ticker_exception(self, db_session, monkeypatch):
        from database import Signal, Trade
        sig = Signal(id=3, symbol="SOLUSDT", side="BUY", approved=True)
        db_session.add(sig)
        db_session.flush()

        trade = Trade(id=30, signal_id=3, symbol="SOLUSDT", side="LONG", entry=150.0, status="OPEN")
        db_session.add(trade)
        db_session.flush()

        ex = BinanceExchange()
        def mock_ticker_raise(sym):
            raise Exception("Network Timeout")
        monkeypatch.setattr(ex, "ticker", mock_ticker_raise)

        pos_list = ex.positions()
        assert len(pos_list) == 1
        pos = pos_list[0]
        assert pos.symbol == "SOLUSDT"
        assert pos.quantity == Decimal("0")
        assert pos.entry_price == Decimal("150.0")
        assert pos.current_price == Decimal("150.0")  # fallback to entry price
