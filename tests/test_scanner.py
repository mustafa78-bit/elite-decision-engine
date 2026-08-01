"""Tests for the Elite Scanner Core."""

from unittest.mock import MagicMock
import pandas as pd

from market.models import Asset, AssetMetadata
from scanner.core import OpportunityScanner
from scanner.models import Opportunity, ScanResult
from scanner.ranking import OpportunityRanker
from scanner.strategies import (
    BreakoutStrategy,
    LiquidityStrategy,
    MomentumStrategy,
    ReversalStrategy,
    TrendStrategy,
)


def _make_asset(
    symbol: str = "BTCUSDT",
    price: float = 50000.0,
    indicators: dict | None = None,
    features: dict | None = None,
    ohlcv: pd.DataFrame | None = None,
) -> Asset:
    if ohlcv is None:
        ohlcv = pd.DataFrame({"close": [49000.0, 49500.0, 50000.0],
                              "volume": [100.0, 110.0, 120.0]})
    return Asset(
        symbol=symbol,
        metadata=AssetMetadata(symbol=symbol),
        price=price,
        ohlcv=ohlcv,
        indicators=indicators or {},
        features=features or {},
    )


class TestTrendStrategy:

    def setup_method(self):
        self.strategy = TrendStrategy()

    def test_bullish_trend(self):
        asset = _make_asset(indicators={"ema20": 110, "ema50": 105, "ema200": 100},
                            features={"trend": "BULLISH"})
        score, signals = self.strategy.evaluate(asset)
        assert score > 0.5
        assert "BULLISH_TREND_ALIGNED" in signals

    def test_bearish_trend(self):
        asset = _make_asset(indicators={"ema20": 90, "ema50": 95, "ema200": 100},
                            features={"trend": "BEARISH"})
        score, signals = self.strategy.evaluate(asset)
        assert score > 0.5
        assert "BEARISH_TREND_ALIGNED" in signals

    def test_no_trend(self):
        asset = _make_asset(indicators={"ema20": 100, "ema50": 100, "ema200": 100})
        score, signals = self.strategy.evaluate(asset)
        assert score == 0.0


class TestMomentumStrategy:

    def setup_method(self):
        self.strategy = MomentumStrategy()

    def test_strong_rsi(self):
        asset = _make_asset(indicators={"rsi": 70}, features={"momentum": "STRONG"})
        score, signals = self.strategy.evaluate(asset)
        assert score > 0.5
        assert "RSI_BULLISH" in signals

    def test_weak_rsi(self):
        asset = _make_asset(indicators={"rsi": 35}, features={"momentum": "WEAK"})
        score, signals = self.strategy.evaluate(asset)
        assert score > 0
        assert "RSI_BEARISH" in signals

    def test_neutral_rsi(self):
        asset = _make_asset(indicators={"rsi": 50})
        score, signals = self.strategy.evaluate(asset)
        assert score == 0.0


class TestBreakoutStrategy:

    def setup_method(self):
        self.strategy = BreakoutStrategy()

    def test_breakout_high(self):
        closes = [100.0] * 20 + [110.0, 111.0, 112.0, 113.0, 115.0]
        volumes = [50.0] * 20 + [100.0, 110.0, 120.0, 130.0, 150.0]
        df = pd.DataFrame({"close": closes, "volume": volumes})
        asset = _make_asset(price=115.0, indicators={"ema20": 105.0}, ohlcv=df)
        score, signals = self.strategy.evaluate(asset)
        assert score > 0.5

    def test_no_breakout(self):
        closes = [100.0] * 25
        volumes = [50.0] * 25
        df = pd.DataFrame({"close": closes, "volume": volumes})
        asset = _make_asset(price=100.0, indicators={"ema20": 100.0}, ohlcv=df)
        score, signals = self.strategy.evaluate(asset)
        assert score < 0.3


class TestReversalStrategy:

    def setup_method(self):
        self.strategy = ReversalStrategy()

    def test_oversold_reversal(self):
        closes = [100.0] * 15
        df = pd.DataFrame({"close": closes})
        asset = _make_asset(indicators={"rsi": 24}, features={"momentum": "OVERSOLD"}, ohlcv=df)
        score, signals = self.strategy.evaluate(asset)
        assert score > 0.5
        assert "OVERSOLD_REVERSAL" in signals

    def test_overbought_reversal(self):
        closes = [100.0] * 15
        df = pd.DataFrame({"close": closes})
        asset = _make_asset(indicators={"rsi": 78}, features={"momentum": "OVERBOUGHT"}, ohlcv=df)
        score, signals = self.strategy.evaluate(asset)
        assert score > 0.5
        assert "OVERBOUGHT_REVERSAL" in signals

    def test_no_reversal(self):
        closes = [100.0] * 15
        df = pd.DataFrame({"close": closes})
        asset = _make_asset(indicators={"rsi": 50}, features={"momentum": "NEUTRAL"}, ohlcv=df)
        score, signals = self.strategy.evaluate(asset)
        assert score == 0.0


class TestLiquidityStrategy:

    def setup_method(self):
        self.strategy = LiquidityStrategy()

    def test_high_liquidity(self):
        asset = _make_asset(features={"liquidity": "HIGH"}, indicators={"volume_score": 0.9})
        score, signals = self.strategy.evaluate(asset)
        assert score > 0.8

    def test_low_liquidity(self):
        asset = _make_asset(features={"liquidity": "LOW"}, indicators={"volume_score": 0.2})
        score, signals = self.strategy.evaluate(asset)
        assert score < 0.3


class TestOpportunityRanker:

    def setup_method(self):
        self.ranker = OpportunityRanker()

    def test_empty_results(self):
        assert self.ranker.rank([]) == []

    def test_rank_sorts_by_score(self):
        results = [
            ScanResult(symbol="BTC", trend_score=0.9, momentum_score=0.0,
                       breakout_score=0.0, reversal_score=0.0, liquidity_score=0.0),
            ScanResult(symbol="ETH", trend_score=0.1, momentum_score=0.0,
                       breakout_score=0.0, reversal_score=0.0, liquidity_score=0.0),
        ]
        ops = self.ranker.rank(results)
        assert len(ops) == 2
        assert ops[0].symbol == "BTC"

    def test_zero_score_skipped(self):
        results = [
            ScanResult(symbol="BTC", trend_score=0.0, momentum_score=0.0,
                       breakout_score=0.0, reversal_score=0.0, liquidity_score=0.0),
        ]
        ops = self.ranker.rank(results)
        assert len(ops) == 0

    def test_top_n(self):
        results = [
            ScanResult(symbol=f"SYM{i}", trend_score=i * 0.1, momentum_score=0.0,
                       breakout_score=0.0, reversal_score=0.0, liquidity_score=0.0)
            for i in range(10)
        ]
        top = self.ranker.top(results, n=3)
        assert len(top) == 3


class TestOpportunityScanner:

    def test_scan_with_mock_service(self):
        mock_service = MagicMock()
        asset = _make_asset(indicators={"ema20": 110, "ema50": 105, "ema200": 100, "rsi": 60},
                            features={"trend": "BULLISH", "momentum": "STRONG",
                                      "liquidity": "HIGH", "risk": "LOW",
                                      "volatility_class": "NORMAL"})
        mock_service.get_asset.return_value = asset
        scanner = OpportunityScanner(market_service=mock_service, symbols=["BTCUSDT"])
        ops = scanner.scan()
        assert len(ops) > 0
        assert ops[0].score > 0

    def test_empty_asset_skipped(self):
        mock_service = MagicMock()
        empty_asset = Asset(symbol="BTC", metadata=AssetMetadata(symbol="BTC"))
        mock_service.get_asset.return_value = empty_asset
        scanner = OpportunityScanner(market_service=mock_service, symbols=["BTCUSDT"])
        ops = scanner.scan()
        assert len(ops) == 0

    def test_top_opportunities(self):
        mock_service = MagicMock()
        asset = _make_asset(indicators={"ema20": 105, "ema50": 102, "ema200": 100, "rsi": 55},
                            features={"trend": "BULLISH", "momentum": "STRONG",
                                      "liquidity": "HIGH", "risk": "LOW",
                                      "volatility_class": "NORMAL"})
        mock_service.get_asset.return_value = asset
        scanner = OpportunityScanner(market_service=mock_service, symbols=["BTCUSDT", "ETHUSDT"])
        top = scanner.top_opportunities(n=1)
        assert len(top) <= 1
