"""Tests for Elite Terminal Backend."""

from unittest.mock import MagicMock, patch
import pandas as pd

from services.terminal_service import TerminalService
from market.models import Asset, AssetMetadata
from market.intelligence.models import IntelligenceBundle


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
