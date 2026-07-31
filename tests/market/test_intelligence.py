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

    @patch("market.intelligence.news.NewsService._fetch_rss_items")
    def test_no_data_returns_empty(self, mock_fetch_rss):
        mock_fetch_rss.return_value = []
        articles = self.service.analyze("BTC")
        assert len(articles) == 0  # no btc_trend, no price_change, feed is empty

    @patch("market.intelligence.news.NewsService._fetch_rss_items")
    def test_price_change_adds_article(self, mock_fetch_rss):
        mock_fetch_rss.return_value = []
        articles = self.service.analyze("BTC", price=50000, price_change_24h=3.5)
        assert any("moved 3.5%" in a["headline"] for a in articles)

    @patch("market.intelligence.news.NewsService._fetch_rss_items")
    @patch("services.ai.provider_factory.create_provider")
    def test_rss_sentiment_with_llm(self, mock_create_provider, mock_fetch_rss):
        # Mock RSS feed entries
        mock_fetch_rss.return_value = [
            {"title": "Bitcoin surges past $60k", "published": "2026-07-31T00:00:00Z"},
            {"title": "BTC drops 5%", "published": "2026-07-31T00:00:00Z"},
        ]
        # Mock NVIDIA Provider
        mock_provider = MagicMock()
        mock_provider._api_key = "test_key"
        mock_provider.generate.return_value = MagicMock(
            content='[{"headline": "Bitcoin surges past $60k", "sentiment": "positive"}, {"headline": "BTC drops 5%", "sentiment": "negative"}]'
        )
        mock_create_provider.return_value = mock_provider

        articles = self.service.analyze("BTC")
        assert len(articles) == 2
        assert articles[0]["headline"] == "Bitcoin surges past $60k"
        assert articles[0]["sentiment"] == "positive"
        assert articles[1]["headline"] == "BTC drops 5%"
        assert articles[1]["sentiment"] == "negative"

    @patch("market.intelligence.news.NewsService._fetch_rss_items")
    def test_rss_sentiment_fallback_rules(self, mock_fetch_rss):
        # Mock RSS feed entries
        mock_fetch_rss.return_value = [
            {"title": "Bitcoin surges past $60k", "published": "2026-07-31T00:00:00Z"},
            {"title": "BTC drops 5%", "published": "2026-07-31T00:00:00Z"},
        ]
        articles = self.service.analyze("BTC")
        assert len(articles) == 2
        assert articles[0]["headline"] == "Bitcoin surges past $60k"
        assert articles[0]["sentiment"] == "positive"  # from keyword fallback
        assert articles[1]["headline"] == "BTC drops 5%"
        assert articles[1]["sentiment"] == "negative"  # from keyword fallback

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
        self.mock_funding = MagicMock()
        self.mock_funding.fetch_funding_history.return_value = MagicMock(empty=True)
        self.mock_oi = MagicMock()
        self.mock_oi.fetch_with_trend.return_value = {"value": 0}
        self.service = WhaleService(funding_collector=self.mock_funding, oi_collector=self.mock_oi)

    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_high_volume_detected(self, mock_binance_request):
        mock_binance_request.return_value = None
        signals = self.service.detect("BTC", volume_score=0.95, volatility_score=0.5)
        types = [s["type"] for s in signals]
        assert "HIGH_VOLUME" in types

    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_whale_move_detected(self, mock_binance_request):
        mock_binance_request.return_value = None
        signals = self.service.detect("BTC", volume_score=0.9, volatility_score=0.9)
        types = [s["type"] for s in signals]
        assert "WHALE_MOVE" in types

    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_no_signals_low_volume(self, mock_binance_request):
        mock_binance_request.return_value = None
        signals = self.service.detect("BTC", volume_score=0.3, volatility_score=0.3)
        assert len(signals) == 0

    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_real_whale_trade_detected(self, mock_binance_request):
        # Mock trade history with a genuine whale trade and many tiny trades
        mock_binance_request.side_effect = lambda path, params: (
            [
                {"qty": "1.0", "price": "50000.0"},  # 50,000 USDT (large trade)
                {"qty": "0.0001", "price": "50000.0"},  # 5 USDT
                {"qty": "0.0002", "price": "50000.0"},  # 10 USDT
                {"qty": "0.0001", "price": "50000.0"},  # 5 USDT
                {"qty": "0.0001", "price": "50000.0"},  # 5 USDT
                {"qty": "0.0001", "price": "50000.0"},  # 5 USDT
                {"qty": "0.0001", "price": "50000.0"},  # 5 USDT
                {"qty": "0.0001", "price": "50000.0"},  # 5 USDT
                {"qty": "0.0001", "price": "50000.0"},  # 5 USDT
                {"qty": "0.0001", "price": "50000.0"},  # 5 USDT
            ]
            if path == "/api/v3/trades"
            else None
        )
        signals = self.service.detect("BTC")
        types = [s["type"] for s in signals]
        assert "WHALE_TRADE" in types
        assert any("unusually large" in s["description"] for s in signals)

    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_real_whale_wall_detected(self, mock_binance_request):
        # Mock depth data with bids having much higher volume than asks
        mock_binance_request.side_effect = lambda path, params: (
            {
                "bids": [["50000", "2.0"], ["49990", "3.0"]], # 250,000 USDT total bids
                "asks": [["50010", "0.2"], ["50020", "0.3"]], # 25,000 USDT total asks
            }
            if path == "/api/v3/depth"
            else None
        )
        signals = self.service.detect("BTC")
        types = [s["type"] for s in signals]
        assert "WHALE_WALL" in types
        assert any("Strong whale Support wall" in s["description"] for s in signals)


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

    @patch("market.intelligence.news.NewsService._fetch_rss_items")
    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_enrich_with_full_asset(self, mock_binance_request, mock_fetch_rss):
        import pandas as pd
        mock_fetch_rss.return_value = []
        mock_binance_request.return_value = None

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

    @patch("market.intelligence.news.NewsService._fetch_rss_items")
    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_enrich_with_mock_collectors(self, mock_binance_request, mock_fetch_rss):
        import pandas as pd
        mock_fetch_rss.return_value = []
        mock_binance_request.return_value = None

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
