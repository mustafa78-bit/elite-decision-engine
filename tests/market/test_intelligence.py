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
        result = self.service.compute(rsi=80, btc_trend="BULLISH", funding_rate=55.0)
        assert result["value"] >= 70
        assert "EXTREME_GREED" in result["label"]

    def test_funding_rate_thresholds(self):
        # Mild/normal annualized rate should not trigger any funding signal
        result_mild = self.service.compute(funding_rate=3.0)
        assert "HIGH_FUNDING_GREED" not in result_mild["signals"]
        assert "NEGATIVE_FUNDING_FEAR" not in result_mild["signals"]

        # Elevated positive rate (20-50 range)
        result_high_greed = self.service.compute(funding_rate=25.0)
        assert result_high_greed["value"] == 60
        assert "HIGH_FUNDING_GREED" in result_high_greed["signals"]

        # Extreme positive rate (>50)
        result_extreme_greed = self.service.compute(funding_rate=55.0)
        assert result_extreme_greed["value"] == 70
        assert "HIGH_FUNDING_GREED" in result_extreme_greed["signals"]

        # Elevated negative rate
        result_high_fear = self.service.compute(funding_rate=-25.0)
        assert result_high_fear["value"] == 40
        assert "NEGATIVE_FUNDING_FEAR" in result_high_fear["signals"]

        # Extreme negative rate
        result_extreme_fear = self.service.compute(funding_rate=-55.0)
        assert result_extreme_fear["value"] == 30
        assert "NEGATIVE_FUNDING_FEAR" in result_extreme_fear["signals"]

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
        # No isBuyerMaker in the fixture -- direction must not be fabricated.
        whale_trade = next(s for s in signals if s["type"] == "WHALE_TRADE")
        assert whale_trade["direction"] is None

    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_real_whale_trade_extracts_sell_side_direction(self, mock_binance_request):
        # isBuyerMaker=True means taker-sell (aggressive selling).
        tiny = [{"qty": "0.0001", "price": "50000.0", "isBuyerMaker": False} for _ in range(9)]
        mock_binance_request.side_effect = lambda path, params: (
            [{"qty": "1.0", "price": "50000.0", "isBuyerMaker": True}] + tiny  # 50,000 USDT sell
            if path == "/api/v3/trades"
            else None
        )
        signals = self.service.detect("BTC")
        whale_trade = next(s for s in signals if s["type"] == "WHALE_TRADE")
        assert whale_trade["direction"] == "sell"
        assert "sell-side" in whale_trade["description"]

    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_real_whale_trade_extracts_buy_side_direction(self, mock_binance_request):
        # isBuyerMaker=False means taker-buy (aggressive buying).
        tiny = [{"qty": "0.0001", "price": "50000.0", "isBuyerMaker": True} for _ in range(9)]
        mock_binance_request.side_effect = lambda path, params: (
            [{"qty": "1.0", "price": "50000.0", "isBuyerMaker": False}] + tiny  # 50,000 USDT buy
            if path == "/api/v3/trades"
            else None
        )
        signals = self.service.detect("BTC")
        whale_trade = next(s for s in signals if s["type"] == "WHALE_TRADE")
        assert whale_trade["direction"] == "buy"
        assert "buy-side" in whale_trade["description"]

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

    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_whale_wall_exposes_wall_type_field(self, mock_binance_request):
        # Ask-heavy book -> Resistance wall; wall_type must be a real field on
        # the signal dict (not just baked into the description string), so
        # consumers like WhaleAgent can branch on it directly.
        mock_binance_request.side_effect = lambda path, params: (
            {
                "bids": [["50000", "0.2"], ["49990", "0.3"]],  # 25,000 USDT total bids
                "asks": [["50010", "2.0"], ["50020", "3.0"]],  # 250,000 USDT total asks
            }
            if path == "/api/v3/depth"
            else None
        )
        signals = self.service.detect("BTC")
        wall_signals = [s for s in signals if s["type"] == "WHALE_WALL"]
        assert len(wall_signals) == 1
        assert wall_signals[0]["wall_type"] == "Resistance"

    @patch("market.intelligence.whale.WhaleService._binance_request")
    def test_extreme_funding_exposes_direction_field(self, mock_binance_request):
        mock_binance_request.return_value = None
        from market_data.funding.models import FundingRate, FundingResult

        self.mock_funding.fetch_funding_history.return_value = FundingResult(
            rates=(FundingRate(symbol="BTC", rate=-0.002, timestamp=0, next_funding_time=0),),
        )
        signals = self.service.detect("BTC")
        funding_signals = [s for s in signals if s["type"] == "EXTREME_FUNDING"]
        assert len(funding_signals) == 1
        assert funding_signals[0]["direction"] == "discount"


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

    def test_estimate_24h_change_uses_24_candles_for_1h_timeframe(self):
        import pandas as pd

        closes = [100.0] * 23 + [110.0]  # 24 candles, 1h apart -> real 24h ago = 100.0
        df = pd.DataFrame({"close": closes})
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            timeframe="1h", ohlcv=df,
        )
        change = IntelligenceService._estimate_24h_change(asset)
        assert change == 10.0

    def test_estimate_24h_change_uses_6_candles_for_4h_timeframe(self):
        import pandas as pd

        # 4h candles: a real 24h window is only 6 candles, not 24.
        closes = [100.0, 100.0, 100.0, 100.0, 100.0, 120.0, 500.0, 500.0]
        df = pd.DataFrame({"close": closes})
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            timeframe="4h", ohlcv=df,
        )
        change = IntelligenceService._estimate_24h_change(asset)
        # price_now = 500.0 (last), price_24h_ago = close[-6] = 100.0
        assert change == 400.0

    def test_estimate_24h_change_returns_none_when_fewer_candles_than_window(self):
        import pandas as pd

        # 4h timeframe needs 6 candles for a real 24h window; only 3 available.
        df = pd.DataFrame({"close": [100.0, 105.0, 110.0]})
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            timeframe="4h", ohlcv=df,
        )
        assert IntelligenceService._estimate_24h_change(asset) is None

    def test_estimate_24h_change_defaults_to_1h_when_timeframe_unknown(self):
        import pandas as pd

        closes = [100.0] * 23 + [150.0]
        df = pd.DataFrame({"close": closes})
        asset = Asset(
            symbol="BTC", metadata=AssetMetadata(symbol="BTC"),
            timeframe="2h",  # not in the lookup table -> falls back to 1h (24 candles)
            ohlcv=df,
        )
        change = IntelligenceService._estimate_24h_change(asset)
        assert change == 50.0
