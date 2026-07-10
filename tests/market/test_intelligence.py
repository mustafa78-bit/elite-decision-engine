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

    def test_default_is_neutral(self):
        result = self.service.compute()
        assert result["value"] == 50
        assert result["label"] == "NEUTRAL"

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

    def test_high_liquidity(self):
        result = self.service.analyze("BTC", volume_score=0.9, liquidity="HIGH")
        assert result["level"] == "HIGH"
        assert result["score"] > 0.7

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
