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
        assert score < -0.5
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
        assert score < 0
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

    def test_ema_crossover_detected(self):
        # Prior 15 bars below the EMA, recent 5 bars crossing up through it and
        # finishing above -- a genuine crossover within the lookback window.
        closes = [95.0] * 15 + [98.0, 99.0, 100.5, 101.0, 102.0]
        volumes = [50.0] * 20
        df = pd.DataFrame({"close": closes, "volume": volumes})
        asset = _make_asset(price=102.0, indicators={"ema20": 100.0}, ohlcv=df)
        score, signals = self.strategy.evaluate(asset)
        assert "EMA_CROSSOVER" in signals

    def test_ema_crossover_not_spuriously_triggered(self):
        # Price consistently above the EMA for the entire lookback -- no prior
        # dip, so this must NOT be reported as a crossover.
        closes = [102.0] * 15 + [105.0] * 5
        volumes = [50.0] * 20
        df = pd.DataFrame({"close": closes, "volume": volumes})
        asset = _make_asset(price=105.0, indicators={"ema20": 100.0}, ohlcv=df)
        score, signals = self.strategy.evaluate(asset)
        assert "EMA_CROSSOVER" not in signals

    def test_ema_crossunder_detected(self):
        # Regression: the mirror-image bearish case (SHORT-favorable) had no
        # crossunder branch at all -- prior 15 bars above the EMA, recent 5
        # bars crossing down through it and finishing below.
        closes = [105.0] * 15 + [102.0, 101.0, 99.5, 99.0, 98.0]
        volumes = [50.0] * 20
        df = pd.DataFrame({"close": closes, "volume": volumes})
        asset = _make_asset(price=98.0, indicators={"ema20": 100.0}, ohlcv=df)
        score, signals = self.strategy.evaluate(asset)
        assert "EMA_CROSSUNDER" in signals
        assert score < 0


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
        assert score < -0.5
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

    def test_rank_short_opportunity(self):
        results = [
            ScanResult(symbol="BTC", trend_score=-0.8, momentum_score=-0.4,
                       breakout_score=0.0, reversal_score=0.0, liquidity_score=0.5),
        ]
        ops = self.ranker.rank(results)
        assert len(ops) == 1
        assert ops[0].side == "SHORT"
        # directional is -0.8 * 0.25 + -0.4 * 0.25 = -0.3
        # subtracting liquidity: -0.3 - 0.5 * 0.15 = -0.375. Rounded to -0.375
        # score should be abs = 0.375
        assert ops[0].score == 0.375
        assert ops[0].strategy == "trend"


class TestOpportunityScanner:

    def test_default_symbols_is_fixed_universe_plus_active_temporary_watches(self):
        # Regression: the default universe used to be a live top-100-by-volume
        # fetch (market_data.universe.get_top_volume_symbols) -- that's now
        # replaced with FIXED_COIN_UNIVERSE (config.py) plus whatever
        # temporary watches are currently active, deduplicated.
        from config import FIXED_COIN_UNIVERSE

        mock_temp_watch = MagicMock()
        mock_temp_watch.active_symbols.return_value = ["PEPEUSDT", "BTCUSDT"]  # BTCUSDT dupes a fixed entry
        scanner = OpportunityScanner(temporary_watch_service=mock_temp_watch)
        assert scanner.symbols == [*FIXED_COIN_UNIVERSE, "PEPEUSDT"]

    def test_default_symbols_excludes_expired_temporary_watches(self):
        # active_symbols() is the real TemporaryWatchService's job to filter
        # by expiry -- the scanner just trusts whatever it returns. A real
        # (non-mocked) TemporaryWatchService with no active rows should
        # yield exactly the fixed universe, nothing extra.
        from config import FIXED_COIN_UNIVERSE
        from services.temporary_watch_service import TemporaryWatchService

        mock_session_factory = MagicMock()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        mock_session_factory.return_value = mock_session
        temp_watch = TemporaryWatchService(session_factory=mock_session_factory)

        scanner = OpportunityScanner(temporary_watch_service=temp_watch)
        assert scanner.symbols == FIXED_COIN_UNIVERSE

    def test_explicit_symbols_bypasses_fixed_universe(self):
        mock_temp_watch = MagicMock()
        scanner = OpportunityScanner(symbols=["DOGEUSDT"], temporary_watch_service=mock_temp_watch)
        assert scanner.symbols == ["DOGEUSDT"]
        mock_temp_watch.active_symbols.assert_not_called()

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
