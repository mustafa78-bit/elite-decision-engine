"""Tests for Elite Terminal Backend."""

from unittest.mock import MagicMock, patch

import pandas as pd

from market.intelligence.models import IntelligenceBundle
from market.models import Asset, AssetMetadata
from services.terminal_service import TerminalService


class TestTerminalService:

    def setup_method(self):
        self.service = TerminalService()

    def test_get_market_health(self):
        mock_market = MagicMock()
        df = pd.DataFrame({"close": [100] * 50, "volume": [50] * 50})
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            price=50000, ohlcv=df,
            indicators={"rsi": 55, "volatility_score": 0.3, "volume_score": 0.7},
            features={"trend": "BULLISH"},
            context={
                "btc": {"btc_price": 50000, "btc_trend": "BULLISH", "available": True},
                "session": "NY",
                "funding": {"state": "NEUTRAL", "funding_rate": 0.0001},
            },
            intelligence=IntelligenceBundle(
                symbol="BTC",
                fear_greed={"value": 55, "label": "GREED", "confidence": 0.7},
            ),
        )
        mock_market.get_asset.return_value = asset
        self.service.market_service = mock_market
        result = self.service.get_market()
        assert result["status"] == "ACTIVE"
        assert result["price"] == 50000
        assert result["btc_trend"] == "BULLISH"
        assert result["fear_greed"] == "GREED"

    def test_get_market_health_empty(self):
        mock_market = MagicMock()
        empty = Asset(symbol="BTC", metadata=AssetMetadata(symbol="BTC"))
        mock_market.get_asset.return_value = empty
        self.service.market_service = mock_market
        result = self.service.get_market()
        assert result["status"] == "UNAVAILABLE"

    def test_get_open_trades_empty_when_db_fails(self):
        result = self.service._get_open_trades()
        assert isinstance(result, list)

    def test_get_risk_status(self):
        result = self.service._get_risk_status()
        assert "risk_score" in result
        assert "open_trades" in result

    def test_get_top_opportunities(self):
        mock_scanner = MagicMock()
        from scanner.models import Opportunity
        mock_scanner.top_opportunities.return_value = [
            Opportunity(
                symbol="BTCUSDT", side="LONG", strategy="trend",
                score=0.8, confidence=80.0, rank=1, price=50000,
                probability_score=75.0, risk_score=0.3,
            ),
        ]
        self.service.scanner = mock_scanner
        result = self.service._get_top_opportunities(n=5)
        assert len(result) == 1
        assert result[0]["symbol"] == "BTCUSDT"

    def test_get_overview_returns_all_sections(self):
        mock_market = MagicMock()
        df = pd.DataFrame({"close": [100] * 50, "volume": [50] * 50})
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            price=50000, ohlcv=df,
            indicators={"rsi": 55, "volatility_score": 0.3, "volume_score": 0.7},
            features={"trend": "BULLISH"},
            context={
                "btc": {"btc_price": 50000, "btc_trend": "BULLISH", "available": True},
                "session": "NY",
                "funding": {"state": "NEUTRAL"},
            },
        )
        mock_market.get_asset.return_value = asset
        self.service.market_service = mock_market

        mock_scanner = MagicMock()
        mock_scanner.top_opportunities.return_value = []
        self.service.scanner = mock_scanner

        overview = self.service.get_overview()
        assert "market" in overview
        assert "portfolio" in overview
        assert "performance" in overview
        assert "open_trades" in overview
        assert "recent_signals" in overview
        assert "top_opportunities" in overview
        assert "risk_status" in overview

    def test_recent_signals_empty_when_db_fails(self):
        result = self.service._get_recent_signals()
        assert isinstance(result, list)

    def test_portfolio_summary(self):
        result = self.service._get_portfolio_summary()
        assert isinstance(result, dict)

    def test_performance_summary(self):
        result = self.service._get_performance_summary()
        assert isinstance(result, dict)

    def test_get_open_trades_with_real_data(self, db_session, monkeypatch, session_factory):
        # current_price comes from market_service.get_price(), a live call --
        # mock it so this test is deterministic instead of depending on
        # real-time ETH price (previously this only "passed" by accident,
        # because a since-fixed bug made get_price() always fail and fall
        # back to entry_val).
        monkeypatch.setattr("services.terminal_service.get_session", session_factory)
        mock_market = MagicMock()
        mock_market.get_price.return_value = 3050.0
        self.service.market_service = mock_market
        from database import PaperTrade, Signal, Trade
        sig = Signal(id=10, symbol="ETHUSDT", side="LONG")
        db_session.add(sig)
        db_session.flush()
        trade = Trade(id=10, signal_id=10, symbol="ETHUSDT", side="LONG", entry=3000.0, status="OPEN")
        db_session.add(trade)
        db_session.flush()
        pt = PaperTrade(position_id=10, symbol="ETHUSDT", side="LONG", entry=3000.0, quantity=2.5, status="OPEN")
        db_session.add(pt)
        db_session.flush()
        result = self.service.get_open_trades()
        assert len(result) == 1
        open_t = result[0]
        assert open_t["id"] == 10
        assert open_t["symbol"] == "ETHUSDT"
        assert open_t["side"] == "LONG"
        assert open_t["entry_price"] == 3000.0
        assert open_t["quantity"] == 2.5
        assert open_t["current_price"] == 3050.0

    def test_get_open_trades_pnl_uses_real_dollar_value_not_raw_per_unit(self, db_session, monkeypatch, session_factory):
        # trade.pnl is a raw per-unit price delta; this endpoint already
        # fetches the real quantity from PaperTrade one line above -- it just
        # wasn't multiplying pnl by it.
        monkeypatch.setattr("services.terminal_service.get_session", session_factory)
        from database import PaperTrade, Signal, Trade
        sig = Signal(id=11, symbol="ETHUSDT", side="LONG")
        db_session.add(sig)
        db_session.flush()
        trade = Trade(id=11, signal_id=11, symbol="ETHUSDT", side="LONG", entry=3000.0, status="OPEN", pnl=80.0)
        db_session.add(trade)
        db_session.flush()
        pt = PaperTrade(position_id=11, symbol="ETHUSDT", side="LONG", entry=3000.0, quantity=0.25, status="OPEN")
        db_session.add(pt)
        db_session.flush()
        result = self.service.get_open_trades()
        assert len(result) == 1
        assert result[0]["pnl"] == 20.0

    def test_get_open_trades_pnl_falls_back_to_raw_value_without_matching_paper_trade(
        self, db_session, monkeypatch, session_factory
    ):
        # No PaperTrade row -- displayed "quantity" is honestly 0 (unknown),
        # but "pnl" must still fall back to the raw per-unit value (the same
        # qty=1.0 convention services/pnl.py uses everywhere else), not be
        # silently zeroed out just because quantity itself is unknown.
        monkeypatch.setattr("services.terminal_service.get_session", session_factory)
        from database import Signal, Trade
        sig = Signal(id=12, symbol="ETHUSDT", side="LONG")
        db_session.add(sig)
        db_session.flush()
        trade = Trade(id=12, signal_id=12, symbol="ETHUSDT", side="LONG", entry=3000.0, status="OPEN", pnl=45.0)
        db_session.add(trade)
        db_session.flush()
        result = self.service.get_open_trades()
        assert len(result) == 1
        assert result[0]["quantity"] == 0.0
        assert result[0]["pnl"] == 45.0

    def test_aggregator_reuses_scanner_and_market_service(self):
        service = TerminalService()
        assert service.aggregator.scanner is service.scanner
        assert service.aggregator.market_service is service.market_service

    def test_get_decision_returns_dict(self):
        from decision.models import DecisionResult
        mock_aggregator = MagicMock()
        mock_aggregator.analyze.return_value = DecisionResult(
            symbol="BTCUSDT", side="LONG", decision="APPROVE",
            score=0.8, confidence=75.0, reasons=["Strong trend"],
        )
        self.service.aggregator = mock_aggregator
        result = self.service.get_decision("BTCUSDT")
        assert result["symbol"] == "BTCUSDT"
        assert result["decision"] == "APPROVE"
        assert result["confidence"] == 75.0
        mock_aggregator.analyze.assert_called_once_with("BTCUSDT", "1h")

    def test_get_decision_returns_none_when_no_data(self):
        mock_aggregator = MagicMock()
        mock_aggregator.analyze.return_value = None
        self.service.aggregator = mock_aggregator
        assert self.service.get_decision("UNKNOWNCOIN") is None


class TestTerminalAPI:

    def test_router_imports(self):
        from api.routes.terminal import router
        assert router is not None

    def test_scanner_event_imports(self):
        from api.events import ScannerEvent, ScannerPayload
        event = ScannerEvent()
        assert event.event == "SCANNER_UPDATE"
        payload = ScannerPayload()
        assert payload.symbol == ""

    def test_get_open_trades_endpoint(self, api_client, db_session):
        from database import PaperTrade, Signal, Trade
        sig = Signal(id=20, symbol="BTCUSDT", side="SHORT")
        db_session.add(sig)
        db_session.flush()
        trade = Trade(id=20, signal_id=20, symbol="BTCUSDT", side="SHORT", entry=60000.0, status="OPEN")
        db_session.add(trade)
        db_session.flush()
        pt = PaperTrade(position_id=20, symbol="BTCUSDT", side="SHORT", entry=60000.0, quantity=0.5, status="OPEN")
        db_session.add(pt)
        db_session.flush()
        resp = api_client.get("/terminal/open-trades")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["id"] == 20
        assert body[0]["symbol"] == "BTCUSDT"
        assert body[0]["side"] == "SHORT"
        assert body[0]["entry_price"] == 60000.0
        assert body[0]["quantity"] == 0.5

    def test_decision_endpoint_returns_result(self, api_client, monkeypatch):
        mock_service = MagicMock()
        mock_service.get_decision.return_value = {
            "symbol": "BTCUSDT", "side": "LONG", "decision": "APPROVE",
            "confidence": 82.0, "reasons": ["Strong trend"], "warnings": [],
            "signals": [], "timeline": [], "intelligence_summary": {},
            "feature_summary": {}, "score": 0.8, "probability": 0.7,
            "risk_score": 0.2, "timestamp": "2026-08-07T00:00:00+00:00",
        }
        monkeypatch.setattr("api.routes.terminal._service", mock_service)
        resp = api_client.get("/terminal/decision/BTCUSDT")
        assert resp.status_code == 200
        body = resp.json()
        assert body["symbol"] == "BTCUSDT"
        assert body["decision"] == "APPROVE"
        mock_service.get_decision.assert_called_once_with("BTCUSDT", "1h")

    def test_decision_endpoint_404_when_no_data(self, api_client, monkeypatch):
        mock_service = MagicMock()
        mock_service.get_decision.return_value = None
        monkeypatch.setattr("api.routes.terminal._service", mock_service)
        resp = api_client.get("/terminal/decision/UNKNOWNCOIN")
        assert resp.status_code == 404
