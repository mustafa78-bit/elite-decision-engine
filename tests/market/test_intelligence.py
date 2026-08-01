"""Tests for Market Intelligence modules."""

from unittest.mock import MagicMock, patch

from market.intelligence.exchange_flow import ExchangeFlowService
from market.intelligence.fear_greed import FearGreedService
from market.intelligence.liquidity import LiquidityContextAnalyzer
from market.intelligence.models import IntelligenceBundle
from market.intelligence.news import NewsService
from market.intelligence.service import IntelligenceService
from market.intelligence.whale import WhaleService
from market.models import Asset, AssetMetadata


class TestFearGreedService:

    def setup_method(self):
        self.service = FearGreedService()
        # Patch requests.get to raise an exception by default to test the heuristic/fallback paths
        self.patcher = patch("market.intelligence.fear_greed.requests.get")
        self.mock_get = self.patcher.start()
        self.mock_get.side_effect = Exception("Forced fallback for testing heuristic")

    def teardown_method(self):
        self.patcher.stop()

    def test_default_is_neutral(self):
        result = self.service.compute()
        assert result["value"] == 50
        assert result["label"] == "NEUTRAL"

    def test_api_success(self):
        self.patcher.stop()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Fear and Greed Index",
            "data": [
                {
                    "value": "78",
                    "value_classification": "Extreme Greed",
                    "timestamp": "1625097600",
                    "time_until_update": "3600"
                }
            ],
            "metadata": {"error": None}
        }
        with patch("market.intelligence.fear_greed.requests.get", return_value=mock_response) as mock_get:
            result = self.service.compute()
            mock_get.assert_called_once_with("https://api.alternative.me/fng/", timeout=5)
            assert result["value"] == 78
            assert result["label"] == "EXTREME_GREED"
            assert result["signals"] == ["API_SOURCE_ALTERNATIVE_ME"]
            assert result["confidence"] == 0.72
            assert "2021-07-01" in result["timestamp"]
        self.patcher.start()

    def test_api_failure_fallback(self):
        self.patcher.stop()
        with patch("market.intelligence.fear_greed.requests.get", side_effect=Exception("Connection timed out")):
            result = self.service.compute(rsi=25)
            assert result["value"] < 50
            assert "FEAR" in result["label"]
        self.patcher.start()

    def test_oversold_rsi(self):
        result = self.service.compute(rsi=25)
        assert result["value"] < 50
        assert "FEAR" in result["label"]

    def test_overbought_rsi(self):
        result = self.service.compute(rsi=75)
        assert result["value"] > 50
        assert "GREED" in result["label"]

    def test_extreme_oversold(self):
        result = self.service.compute(rsi=20, btc_trend="BEARISH")
        assert result["value"] <= 30
        assert "EXTREME_FEAR" in result["label"]

    def test_extreme_greed(self):
        result = self.service.compute(rsi=80, btc_trend="BULLISH", funding_rate=0.02)
        assert result["value"] >= 70
        assert "EXTREME_GREED" in result["label"]

    def test_confidence_reflects_extremity(self):
        neutral = self.service.compute()
        extreme = self.service.compute(rsi=20, btc_trend="BEARISH")
        assert extreme["confidence"] < neutral["confidence"]


class TestNewsService:

    def setup_method(self):
        self.service = NewsService()

    def test_no_data_returns_empty(self):
        articles = self.service.analyze("BTC")
        assert len(articles) == 0  # no btc_trend, no price_change

    def test_price_change_adds_article(self):
        articles = self.service.analyze("BTC", price=50000, price_change_24h=3.5)
        assert any("moved 3.5%" in a["headline"] for a in articles)

    def test_sentiment_score_positive(self):
        articles = [
            {"source": "test", "headline": "good", "sentiment": "positive", "relevance": 1.0},
        ]
        assert self.service.sentiment_score(articles) == 1.0

    def test_sentiment_score_negative(self):
        articles = [
            {"source": "test", "headline": "bad", "sentiment": "negative", "relevance": 1.0},
        ]
        assert self.service.sentiment_score(articles) == -1.0

    def test_sentiment_score_empty(self):
        assert self.service.sentiment_score([]) == 0.0


class TestWhaleService:

    def setup_method(self):
        self.service = WhaleService()

    def test_high_volume_detected(self):
        signals = self.service.detect("BTC", volume_score=0.95, volatility_score=0.5)
        types = [s["type"] for s in signals]
        assert "HIGH_VOLUME" in types

    def test_whale_move_detected(self):
        signals = self.service.detect("BTC", volume_score=0.9, volatility_score=0.9)
        types = [s["type"] for s in signals]
        assert "WHALE_MOVE" in types

    def test_no_signals_low_volume(self):
        signals = self.service.detect("BTC", volume_score=0.3, volatility_score=0.3)
        assert len(signals) == 0


class TestExchangeFlowService:

    def setup_method(self):
        self.service = ExchangeFlowService()

    def test_high_volume_outflow(self):
        result = self.service.analyze("BTC", volume_score=0.9)
        assert result["direction"] == "NET_OUTFLOW"

    def test_low_volume_inflow(self):
        result = self.service.analyze("BTC", volume_score=0.2)
        assert result["direction"] == "NET_INFLOW"

    def test_bullish_volatile_inflow(self):
        result = self.service.analyze("BTC", volume_score=0.5, volatility_score=0.8, trend="BULLISH")
        assert result["direction"] == "NET_INFLOW"

    def test_neutral_flow(self):
        result = self.service.analyze("BTC")
        assert result["direction"] in ("NET_INFLOW", "NET_OUTFLOW", "NEUTRAL")


class TestLiquidityContextAnalyzer:

    def setup_method(self):
        self.service = LiquidityContextAnalyzer()
        # Patch fetch_binance_depth to return None by default to test the heuristic/fallback paths
        self.patcher = patch("market.intelligence.liquidity.fetch_binance_depth", return_value=None)
        self.patcher.start()

    def teardown_method(self):
        self.patcher.stop()

    def test_high_liquidity(self):
        result = self.service.analyze("BTC", volume_score=0.9, liquidity="HIGH")
        assert result["level"] == "HIGH"
        assert result["score"] > 0.7

    def test_binance_depth_success_high_liquidity(self):
        self.patcher.stop()
        mock_depth = {
            "lastUpdateId": 12345,
            "bids": [
                ["50000.00", "10.0"],  # $500k at best bid
                ["49800.00", "20.0"],  # $996k at lower bid
                ["49500.00", "30.0"],  # $1.485M at lower bid
            ],
            "asks": [
                ["50050.00", "10.0"],  # $500.5k at best ask
                ["50200.00", "20.0"],  # $1.004M at higher ask
                ["50500.00", "30.0"],  # $1.515M at higher ask
            ]
        }
        with patch("market.intelligence.liquidity.fetch_binance_depth", return_value=mock_depth):
            result = self.service.analyze("BTC")
            assert "API_SOURCE_BINANCE_ORDER_BOOK" in result["signals"]
            assert result["level"] == "HIGH"
            assert result["score"] > 0.7
        self.patcher.start()

    def test_binance_depth_success_low_liquidity(self):
        self.patcher.stop()
        # Mock low liquidity with wide spread
        mock_depth = {
            "lastUpdateId": 12345,
            "bids": [
                ["49000.00", "0.01"],  # Very shallow and wide spread
            ],
            "asks": [
                ["51000.00", "0.01"],
            ]
        }
        with patch("market.intelligence.liquidity.fetch_binance_depth", return_value=mock_depth):
            result = self.service.analyze("BTC")
            assert "API_SOURCE_BINANCE_ORDER_BOOK" in result["signals"]
            # Wide spread should lower the score and trigger warning
            assert "WIDE_SPREAD_WARNING" in result["signals"]
            assert result["level"] == "LOW"
            assert result["score"] < 0.4
        self.patcher.start()

    def test_low_liquidity(self):
        result = self.service.analyze("BTC", volume_score=0.2, liquidity="LOW")
        assert result["level"] == "LOW"
        assert result["score"] < 0.4

    def test_medium_liquidity(self):
        result = self.service.analyze("BTC", liquidity="MEDIUM")
        assert result["level"] == "MEDIUM"

    def test_atr_penalty(self):
        no_atr = self.service.analyze("BTC", liquidity="HIGH", volume_score=0.8)
        with_atr = self.service.analyze("BTC", liquidity="HIGH", volume_score=0.8, atr=300, price=5000)
        assert with_atr["score"] <= no_atr["score"]


class TestIntelligenceBundle:

    def test_empty_bundle(self):
        bundle = IntelligenceBundle(symbol="BTC")
        assert bundle.feature_count == 0
        assert bundle.confidence == 0.0
        assert bundle.available_features == []

    def test_feature_count(self):
        bundle = IntelligenceBundle(
            symbol="BTC",
            funding={"risk_score": 0.5},
            fear_greed={"confidence": 0.8},
            liquidity_context={"score": 0.7},
            market_session="NY",
        )
        assert bundle.feature_count == 4

    def test_confidence_averages_scores(self):
        bundle = IntelligenceBundle(
            symbol="BTC",
            funding={"risk_score": 0.8},
            fear_greed={"confidence": 0.6},
        )
        assert bundle.confidence == 0.7

    def test_available_features(self):
        bundle = IntelligenceBundle(
            symbol="BTC",
            funding={"risk_score": 0.5},
            market_session="NY",
        )
        features = bundle.available_features
        assert "funding" in features
        assert "market_session" in features
        assert "news" not in features


class TestIntelligenceService:

    def setup_method(self):
        self.service = IntelligenceService()

    def test_enrich_empty_asset(self):
        asset = Asset(symbol="BTC", metadata=AssetMetadata(symbol="BTC"))
        result = self.service.enrich(asset)
        assert result is asset  # same object returned
        assert result.intelligence is None  # because price=0 and ohlcv=None

    def test_enrich_with_full_asset(self):
        import pandas as pd

        df = pd.DataFrame({
            "close": [49000, 49500, 50000, 50500, 51000],
            "volume": [100, 110, 120, 130, 140],
        })
        asset = Asset(
            symbol="BTC",
            metadata=AssetMetadata(symbol="BTC"),
            price=50000.0,
            ohlcv=df,
            indicators={"rsi": 55, "volatility_score": 0.3, "volume_score": 0.7, "atr": 500},
            features={"trend": "BULLISH", "liquidity": "HIGH", "momentum": "STRONG", "volatility_class": "NORMAL", "risk": "LOW"},
            context={
                "btc": {"btc_price": 50000, "btc_trend": "BULLISH"},
                "session": "NY",
                "funding": {"state": "NEUTRAL"},
            },
        )
        result = self.service.enrich(asset)
        assert result is asset
        assert result.intelligence is not None
        assert result.intelligence.symbol == "BTC"
        assert "fear_greed" in result.intelligence.available_features
        assert result.intelligence.fear_greed.get("value", 0) > 0

    def test_enrich_with_mock_collectors(self):
        import pandas as pd

        mock_funding = MagicMock()
        mock_rate = MagicMock()
        mock_rate.rate = 0.0005
        mock_rate.annualized_rate = 0.5475
        mock_funding.fetch_for_symbol.return_value = mock_rate

        mock_oi = MagicMock()
        mock_oi.fetch_with_trend.return_value = {
            "value": 1000000000, "trend": "INCREASING", "strength": 0.7,
        }

        service = IntelligenceService(
            funding_collector=mock_funding,
            oi_collector=mock_oi,
        )

        df = pd.DataFrame({
            "close": [49000, 49500, 50000, 50500, 51000],
            "volume": [100, 110, 120, 130, 140],
        })
        asset = Asset(
            symbol="BTC",
            metadata=AssetMetadata(symbol="BTC"),
            price=50000.0,
            ohlcv=df,
            indicators={"rsi": 55, "volatility_score": 0.3, "volume_score": 0.7, "atr": 500},
            features={"trend": "BULLISH", "liquidity": "HIGH", "momentum": "STRONG", "volatility_class": "NORMAL", "risk": "LOW"},
            context={"btc": {"btc_price": 50000, "btc_trend": "BULLISH"}, "session": "NY", "funding": {"state": "NEUTRAL"}},
        )
        result = service.enrich(asset)
        assert result.intelligence is not None
        assert result.intelligence.funding
        assert result.intelligence.open_interest
