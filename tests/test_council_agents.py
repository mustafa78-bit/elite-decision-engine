from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from council.base import DIRECTION_BEARISH, DIRECTION_BULLISH, DIRECTION_NEUTRAL, DIRECTION_PASS
from council.macro_agent import MacroAgent
from council.news_agent import NewsAgent
from council.risk_agent import RiskAgent
from council.technical_agent import TechnicalAgent
from council.trend_agent import TrendAgent
from council.whale_agent import WhaleAgent


@pytest.fixture
def mock_signal():
    signal = MagicMock()
    signal.id = 1
    signal.symbol = "BTCUSDT"
    signal.side = "LONG"
    signal.timeframe = "1h"
    return signal


class TestTechnicalAgent:
    def test_default_creation(self):
        agent = TechnicalAgent()
        assert agent.name == "Technical"
        assert agent.weight == 1.0

    def test_evaluate_with_scores(self, mock_signal):
        agent = TechnicalAgent()
        scores = {
            "trend_score": 0.8,
            "volume_score": 0.7,
            "btc_score": 0.6,
            "mtf_score": 0.5,
            "final_score": 0.8,
            "rsi": 45,
            "ema20": 50000,
            "ema50": 48000,
            "ema200": 45000,
            "contributions": {"trend": 0.24, "volume": 0.14, "btc": 0.12, "mtf": 0.10, "risk": 0.05},
        }
        report = agent.evaluate(signal=mock_signal, scores=scores)
        assert report.agent_name == "Technical"
        assert report.symbol == "BTCUSDT"
        assert report.direction == DIRECTION_BULLISH
        assert report.confidence > 0
        assert report.score > 0
        assert len(report.reasoning) > 0
        assert "ema20" in report.data_points

    def test_evaluate_no_scores(self):
        agent = TechnicalAgent()
        report = agent.evaluate(signal=None, scores=None)
        assert report.direction == DIRECTION_NEUTRAL
        assert report.score == 0.0

    def test_evaluate_no_signal(self):
        agent = TechnicalAgent()
        report = agent.evaluate(signal=None)
        assert report.symbol == "?"
        assert report.direction in (DIRECTION_NEUTRAL, DIRECTION_PASS)

    def test_confidence_reaches_1_0_on_maximal_scores(self, mock_signal):
        # trend/volume/btc/mtf weights (0.30/0.20/0.20/0.20 from
        # config.SCORE_WEIGHTS, excluding the "risk" term RiskAgent covers
        # separately) only summed to 0.9 before renormalization -- a perfect
        # reading on all four could never actually reach confidence 1.0.
        agent = TechnicalAgent()
        scores = {
            "trend_score": 1.0, "volume_score": 1.0, "btc_score": 1.0, "mtf_score": 1.0,
            "final_score": 1.0, "rsi": 50, "ema20": 3, "ema50": 2, "ema200": 1,
        }
        report = agent.evaluate(signal=mock_signal, scores=scores)
        assert report.confidence == 1.0

    def test_evaluate_short_with_scores(self):
        # Test TechnicalAgent with SHORT side
        agent = TechnicalAgent()
        mock_short_signal = MagicMock()
        mock_short_signal.symbol = "BTCUSDT"
        mock_short_signal.side = "SHORT"

        # Bullish EMA structure (20 > 50 > 200) -> literal BULLISH -> normalized BEARISH (bad for SHORT)
        scores = {
            "trend_score": 0.8,
            "volume_score": 0.7,
            "btc_score": 0.6,
            "mtf_score": 0.5,
            "final_score": 0.8,
            "rsi": 45,
            "ema20": 50000,
            "ema50": 48000,
            "ema200": 45000,
        }
        report = agent.evaluate(signal=mock_short_signal, scores=scores)
        assert report.direction == DIRECTION_BEARISH


class TestTrendAgent:
    def test_default_creation(self):
        agent = TrendAgent()
        assert agent.name == "Trend"

    def test_evaluate_with_regime_context(self, mock_signal):
        agent = TrendAgent()
        regime_context = {
            "regime": "TREND",
            "trend": "BULLISH",
            "trend_strength": "STRONG",
            "volatility_class": "NORMAL",
            "market_phase": "MARKUP",
            "score": 0.85,
        }
        report = agent.evaluate(signal=mock_signal, scores={}, regime_context=regime_context)
        assert report.direction == DIRECTION_BULLISH
        assert report.confidence > 0.5
        assert report.score == 0.85
        assert "Regime: TREND" in report.reasoning
        assert "Market phase: MARKUP" in report.reasoning

    def test_evaluate_with_downtrend(self, mock_signal):
        agent = TrendAgent()
        scores = {
            "ema20": 40000, "ema50": 45000, "ema200": 50000,
            "atr": 500, "entry": 42000, "rsi": 35,
        }
        report = agent.evaluate(signal=mock_signal, scores=scores)
        assert report.direction == DIRECTION_BEARISH

    def test_evaluate_dead_regime(self, mock_signal):
        agent = TrendAgent()
        scores = {"ema20": 0, "ema50": 0, "ema200": 0, "atr": 0, "entry": 0, "rsi": 50}
        report = agent.evaluate(signal=mock_signal, scores=scores)
        assert report.direction == DIRECTION_PASS
        assert report.confidence < 0.3
        # regime_score (RegimeAI's own score) floors at 0.4 for DEAD regimes
        # and can never trigger a "< 0.3" guard -- this reasoning line must
        # key off direction == DIRECTION_PASS directly, not that threshold.
        assert "Market too quiet — no trend signal" in report.reasoning

    def test_evaluate_short_with_downtrend(self):
        agent = TrendAgent()
        mock_short_signal = MagicMock()
        mock_short_signal.symbol = "BTCUSDT"
        mock_short_signal.side = "SHORT"

        # Downtrend is literal BEARISH -> normalized BULLISH (favourable for SHORT)
        scores = {
            "ema20": 40000, "ema50": 45000, "ema200": 50000,
            "atr": 500, "entry": 42000, "rsi": 35,
        }
        report = agent.evaluate(signal=mock_short_signal, scores=scores)
        assert report.direction == DIRECTION_BULLISH

    def test_confidence_symmetric_between_trend_long_and_downtrend_short(self, mock_signal):
        # TREND regime + LONG and DOWNTREND regime + SHORT are mirror-image,
        # equally-strong "fully aligned trend" setups once direction has
        # already been side-normalized (both come out DIRECTION_BULLISH,
        # i.e. "supports the trade"). Confidence must be the same for both,
        # not keyed off which literal regime string happened to produce it.
        agent = TrendAgent()

        long_signal = MagicMock()
        long_signal.symbol = "BTCUSDT"
        long_signal.side = "LONG"
        trend_context = {
            "regime": "TREND", "trend": "BULLISH", "trend_strength": "STRONG",
            "volatility_class": "NORMAL", "market_phase": "MARKUP", "score": 0.85,
        }
        long_report = agent.evaluate(signal=long_signal, scores={}, regime_context=trend_context)

        short_signal = MagicMock()
        short_signal.symbol = "BTCUSDT"
        short_signal.side = "SHORT"
        downtrend_context = {
            "regime": "DOWNTREND", "trend": "BEARISH", "trend_strength": "STRONG",
            "volatility_class": "NORMAL", "market_phase": "MARKDOWN", "score": 0.85,
        }
        short_report = agent.evaluate(signal=short_signal, scores={}, regime_context=downtrend_context)

        assert long_report.direction == DIRECTION_BULLISH
        assert short_report.direction == DIRECTION_BULLISH
        assert long_report.confidence == short_report.confidence


class TestRiskAgent:
    def test_default_creation(self):
        agent = RiskAgent()
        assert agent.name == "Risk"

    def test_evaluate_low_risk(self, mock_signal):
        agent = RiskAgent()
        scores = {"atr": 200, "risk_score": 0.2, "volatility": 0.1}
        report = agent.evaluate(signal=mock_signal, scores=scores)
        assert report.direction in (DIRECTION_BULLISH, DIRECTION_NEUTRAL)
        assert report.confidence > 0.5

    def test_evaluate_high_risk(self, mock_signal):
        agent = RiskAgent()
        scores = {"atr": 3000, "risk_score": 0.9, "volatility": 0.8}
        report = agent.evaluate(signal=mock_signal, scores=scores)
        # risk_score=0.9 is the raw volatility component, but risk_engine will
        # penalize and produce a lower risk_score
        assert report.data_points is not None

    def test_evaluate_no_scores(self, mock_signal):
        agent = RiskAgent()
        report = agent.evaluate(signal=mock_signal, scores=None)
        assert report.direction == DIRECTION_NEUTRAL


class TestNewsAgent:
    def test_default_creation(self):
        agent = NewsAgent()
        assert agent.name == "News"

    def test_evaluate_with_intel_bundle(self, mock_signal):
        agent = NewsAgent()
        bundle = MagicMock()
        bundle.news = [
            {"source": "test", "headline": "BTC up 5%", "sentiment": "positive", "relevance": 0.8},
            {"source": "test", "headline": "Market rally", "sentiment": "positive", "relevance": 0.6},
        ]
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BULLISH
        assert report.confidence > 0
        assert report.data_points["article_count"] == 2

    def test_evaluate_no_articles(self, mock_signal):
        agent = NewsAgent()
        bundle = MagicMock()
        bundle.news = []
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_NEUTRAL
        assert report.confidence == 0.0

    def test_evaluate_no_bundle(self, mock_signal):
        mock_news_service = MagicMock()
        mock_news_service.analyze.return_value = []
        agent = NewsAgent(news_service=mock_news_service)
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=None)
        assert report.direction == DIRECTION_NEUTRAL

    def test_evaluate_short_positive_sentiment(self):
        agent = NewsAgent()
        mock_short_signal = MagicMock()
        mock_short_signal.symbol = "BTCUSDT"
        mock_short_signal.side = "SHORT"

        bundle = MagicMock()
        bundle.news = [
            {"source": "test", "headline": "BTC up 5%", "sentiment": "positive", "relevance": 0.8},
        ]
        # Positive sentiment is literal BULLISH -> normalized BEARISH (bad for SHORT)
        report = agent.evaluate(signal=mock_short_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BEARISH


class TestWhaleAgent:
    def test_default_creation(self):
        agent = WhaleAgent()
        assert agent.name == "Whale"

    def test_evaluate_with_signals(self, mock_signal):
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {"type": "WHALE_MOVE", "severity": "high", "confidence": 0.85, "description": "Whale accumulation"},
            {"type": "HIGH_VOLUME", "severity": "medium", "confidence": 0.72, "description": "High volume"},
        ]
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BULLISH
        assert report.confidence > 0.7
        assert report.data_points["signal_count"] == 2
        assert report.data_points["high_severity"] is True

    def test_evaluate_no_signals(self, mock_signal):
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = []
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_NEUTRAL
        assert report.score == 0.5

    def test_evaluate_no_bundle(self, mock_signal):
        mock_whale_service = MagicMock()
        mock_whale_service.detect.return_value = []
        agent = WhaleAgent(whale_service=mock_whale_service)
        report = agent.evaluate(signal=mock_signal, scores={"volume_score": 0.3})
        assert report.direction == DIRECTION_NEUTRAL

    def test_evaluate_short_with_signals(self):
        agent = WhaleAgent()
        mock_short_signal = MagicMock()
        mock_short_signal.symbol = "BTCUSDT"
        mock_short_signal.side = "SHORT"

        bundle = MagicMock()
        bundle.whales = [
            {"type": "WHALE_MOVE", "severity": "high", "confidence": 0.85, "description": "Whale accumulation"},
        ]
        # High severity whale move is literal BULLISH -> normalized BEARISH (bad for SHORT)
        report = agent.evaluate(signal=mock_short_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BEARISH

    def test_evaluate_bearish_wall_long_side(self, mock_signal):
        agent = WhaleAgent()
        bundle = MagicMock()
        # Mocking a heavy ask-side/Resistance wall
        bundle.whales = [
            {"type": "WHALE_WALL", "wall_type": "Resistance", "severity": "high", "confidence": 0.9, "description": "Resistance wall"}
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BEARISH
        assert report.confidence == 0.9
        assert any("Whale wall: Resistance" in r for r in report.reasoning)

    def test_evaluate_bullish_wall_long_side(self, mock_signal):
        agent = WhaleAgent()
        bundle = MagicMock()
        # Mocking a heavy bid-side/Support wall
        bundle.whales = [
            {"type": "WHALE_WALL", "wall_type": "Support", "severity": "high", "confidence": 0.9, "description": "Support wall"}
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BULLISH
        assert report.confidence == 0.9
        assert any("Whale wall: Support" in r for r in report.reasoning)

    def test_evaluate_bearish_wall_short_side(self, mock_signal):
        """A Resistance wall is literally bearish, but for a SHORT trade that
        validates the position -- must normalize to BULLISH, not BEARISH.
        This is the exact bug this sprint fixes: the consensus mechanism must
        flip by side like every other council agent, not report the literal
        market direction unconditionally."""
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {"type": "WHALE_WALL", "wall_type": "Resistance", "severity": "high", "confidence": 0.9, "description": "Resistance wall"}
        ]
        mock_signal.side = "SHORT"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BULLISH

    def test_evaluate_bullish_wall_short_side(self, mock_signal):
        """A Support wall is literally bullish, but opposes a SHORT trade --
        must normalize to BEARISH."""
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {"type": "WHALE_WALL", "wall_type": "Support", "severity": "high", "confidence": 0.9, "description": "Support wall"}
        ]
        mock_signal.side = "SHORT"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BEARISH

    def test_evaluate_bearish_funding_long_side(self, mock_signal):
        agent = WhaleAgent()
        bundle = MagicMock()
        # Mocking extreme funding discount
        bundle.whales = [
            {"type": "EXTREME_FUNDING", "direction": "discount", "severity": "high", "confidence": 0.85, "description": "Extreme funding discount"}
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BEARISH
        assert report.confidence == 0.85
        assert any("Extreme funding: discount" in r for r in report.reasoning)

    def test_evaluate_bullish_funding_long_side(self, mock_signal):
        agent = WhaleAgent()
        bundle = MagicMock()
        # Mocking extreme funding premium
        bundle.whales = [
            {"type": "EXTREME_FUNDING", "direction": "premium", "severity": "high", "confidence": 0.85, "description": "Extreme funding premium"}
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BULLISH
        assert report.confidence == 0.85
        assert any("Extreme funding: premium" in r for r in report.reasoning)

    def test_evaluate_malformed_wall_type_is_neutral_not_bearish(self, mock_signal):
        # Regression: an unrecognized/missing wall_type used to default to
        # bearish (any non-"Support" value) instead of neutral, same class
        # of bug already fixed for WHALE_TRADE's direction field.
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {
                "type": "WHALE_WALL", "wall_type": None, "severity": "high",
                "confidence": 0.9, "description": "Malformed wall",
            }
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_NEUTRAL

    def test_evaluate_malformed_funding_direction_is_neutral_not_bearish(self, mock_signal):
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {
                "type": "EXTREME_FUNDING", "direction": "unknown", "severity": "high",
                "confidence": 0.85, "description": "Malformed funding",
            }
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_NEUTRAL

    def test_evaluate_conflicting_signals_consensus(self, mock_signal):
        agent = WhaleAgent()
        bundle = MagicMock()
        # Resistance wall (bearish, high severity) and minor Support wall (bullish, medium severity)
        bundle.whales = [
            {"type": "WHALE_WALL", "wall_type": "Resistance", "severity": "high", "confidence": 0.9, "description": "Resistance wall"},
            {"type": "WHALE_WALL", "wall_type": "Support", "severity": "medium", "confidence": 0.4, "description": "Support wall"}
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        # Total influence = (-1 * 2.0 * 0.9) + (1 * 1.0 * 0.4) = -1.8 + 0.4 = -1.4
        # Since net influence is < -0.05, aggregate direction is BEARISH
        assert report.direction == DIRECTION_BEARISH

    def test_whale_move_does_not_bias_directional_consensus(self, mock_signal):
        """WHALE_MOVE (open-interest buildup) carries no inherent buy/sell
        direction -- it must not silently push total_influence bullish when
        it rides along with a genuinely directional signal. A medium-severity
        bearish Resistance wall alone is bearish; adding a high-severity
        WHALE_MOVE must not flip that to bullish."""
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {"type": "WHALE_WALL", "wall_type": "Resistance", "severity": "medium", "confidence": 0.5, "description": "Resistance wall"},
            {"type": "WHALE_MOVE", "severity": "high", "confidence": 0.85, "description": "Whale movement"},
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        # Total influence = (-1 * 1.0 * 0.5) + (0 * 2.0 * 0.85) = -0.5
        assert report.direction == DIRECTION_BEARISH

    def test_whale_trade_sell_side_produces_bearish(self, mock_signal):
        """A WHALE_TRADE-only signal set was previously structurally unable
        to ever produce DIRECTION_BEARISH -- a high-severity reading always
        became literal-bullish via a catch-all, regardless of what actually
        happened. Real direction is now extracted from Binance's
        isBuyerMaker (market/intelligence/whale.py); a sell-side large trade
        must produce a real bearish result."""
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {"type": "WHALE_TRADE", "direction": "sell", "severity": "high", "confidence": 0.9, "description": "Large sell-side trade"},
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BEARISH

    def test_whale_trade_buy_side_produces_bullish(self, mock_signal):
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {"type": "WHALE_TRADE", "direction": "buy", "severity": "high", "confidence": 0.9, "description": "Large buy-side trade"},
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BULLISH

    def test_whale_trade_without_direction_stays_neutral_not_bullish(self, mock_signal):
        """A WHALE_TRADE with no extractable direction (isBuyerMaker
        unavailable) must fall back to the non-directional path and stay
        NEUTRAL -- not the old unconditional-bullish catch-all."""
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {"type": "WHALE_TRADE", "direction": None, "severity": "high", "confidence": 0.9, "description": "Large trade, side unknown"},
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_NEUTRAL

    def test_high_volume_only_stays_neutral_not_bullish(self, mock_signal):
        """HIGH_VOLUME carries no direction of its own -- a high-severity,
        high-confidence reading must not default to bullish."""
        agent = WhaleAgent()
        bundle = MagicMock()
        bundle.whales = [
            {"type": "HIGH_VOLUME", "severity": "high", "confidence": 0.9, "description": "Unusually high volume"},
        ]
        mock_signal.side = "LONG"
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_NEUTRAL


class TestMacroAgent:
    def test_default_creation(self):
        agent = MacroAgent()
        assert agent.name == "Macro"

    def test_evaluate_with_all_data(self, mock_signal):
        agent = MacroAgent()
        bundle = MagicMock()
        bundle.funding = {"annualized_rate": 0.0001, "level": "neutral", "risk_score": 0.2}
        bundle.open_interest = {"value": 1e9, "trend": "strong_increase", "strength": 0.7}
        bundle.fear_greed = {"label": "FEAR", "value": 30, "confidence": 0.6}
        bundle.liquidity_context = {"score": 0.8, "level": "HIGH"}
        bundle.exchange_flow = {"direction": "NET_OUTFLOW", "confidence": 0.75}

        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.agent_name == "Macro"
        assert report.symbol == "BTCUSDT"
        assert len(report.reasoning) >= 4
        assert report.data_points["bullish_signals"] >= 2
        assert report.data_points["composite_score"] > 0

    def test_oi_trend_uses_real_detect_oi_trend_vocabulary(self, mock_signal):
        # Regression: OI_TREND_MAP previously keyed on "RISING"/"FALLING"/
        # "FLAT", which market_data/open_interest/models.py's
        # detect_oi_trend() never produces (real vocabulary is lowercase
        # strong_increase/increase/strong_decrease/decrease/neutral) -- the
        # map never matched anything, so OI trend never contributed to
        # bullish/bearish count regardless of real open interest movement.
        agent = MacroAgent()
        bundle = MagicMock()
        bundle.funding = {"annualized_rate": 0, "level": "neutral"}
        bundle.open_interest = {"value": 1e9, "trend": "strong_increase", "strength": 0.9}
        bundle.fear_greed = {"label": "NEUTRAL", "value": 50}
        bundle.liquidity_context = {"score": 0.5, "level": "NEUTRAL"}
        bundle.exchange_flow = {"direction": "NEUTRAL", "confidence": 0.5}

        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.data_points["bullish_signals"] >= 1

    def test_evaluate_no_bundle(self, mock_signal):
        agent = MacroAgent()
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=None)
        assert report.direction == DIRECTION_NEUTRAL
        assert report.confidence == 0.5

    def test_evaluate_short_with_macro_data(self):
        agent = MacroAgent()
        mock_short_signal = MagicMock()
        mock_short_signal.symbol = "BTCUSDT"
        mock_short_signal.side = "SHORT"

        bundle = MagicMock()
        bundle.funding = {"annualized_rate": 0.0001, "level": "neutral", "risk_score": 0.2}
        bundle.open_interest = {"value": 1e9, "trend": "strong_increase", "strength": 0.7}
        bundle.fear_greed = {"label": "FEAR", "value": 30, "confidence": 0.6}
        bundle.liquidity_context = {"score": 0.8, "level": "HIGH"}
        bundle.exchange_flow = {"direction": "NET_OUTFLOW", "confidence": 0.75}

        # Original LONG evaluates to BULLISH (literal bullish is >= 2 signals)
        # For SHORT, literal BULLISH -> normalized BEARISH
        report = agent.evaluate(signal=mock_short_signal, intelligence_bundle=bundle)
        assert report.direction == DIRECTION_BEARISH

    def _neutral_macro_bundle(self):
        """A bundle with every field neutral/absent except exchange_flow, to
        isolate exchange_flow's own contribution from funding/OI/fear-greed/
        liquidity."""
        bundle = MagicMock()
        bundle.funding = {"annualized_rate": 0, "level": "NEUTRAL"}
        bundle.open_interest = {"value": 0, "trend": "neutral"}
        bundle.fear_greed = {"label": "NEUTRAL", "value": 50}
        bundle.liquidity_context = {"score": 0.5, "level": "NEUTRAL"}
        return bundle

    def test_exchange_flow_net_outflow_is_bullish(self, mock_signal):
        agent = MacroAgent()
        bundle = self._neutral_macro_bundle()
        bundle.exchange_flow = {"direction": "NET_OUTFLOW", "confidence": 0.75}
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.data_points["bullish_signals"] == 1
        assert report.data_points["bearish_signals"] == 0
        assert "Exchange outflow — accumulation signal" in report.reasoning

    def test_exchange_flow_net_inflow_is_bearish(self, mock_signal):
        agent = MacroAgent()
        bundle = self._neutral_macro_bundle()
        bundle.exchange_flow = {"direction": "NET_INFLOW", "confidence": 0.75}
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.data_points["bullish_signals"] == 0
        assert report.data_points["bearish_signals"] == 1
        assert "Exchange inflow — potential selling pressure" in report.reasoning

    def test_evaluate_positive_funding_is_bearish(self, mock_signal):
        agent = MacroAgent()
        bundle = self._neutral_macro_bundle()
        bundle.exchange_flow = {}
        bundle.funding = {"annualized_rate": 25.0, "level": "high", "risk_score": 0.3}
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.data_points["bearish_signals"] == 1
        assert report.data_points["bullish_signals"] == 0
        assert "Elevated funding — crowded long" in report.reasoning

    def test_evaluate_negative_funding_is_bullish(self, mock_signal):
        agent = MacroAgent()
        bundle = self._neutral_macro_bundle()
        bundle.exchange_flow = {}
        bundle.funding = {"annualized_rate": -25.0, "level": "high_negative", "risk_score": 0.3}
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.data_points["bullish_signals"] == 1
        assert report.data_points["bearish_signals"] == 0
        assert "Negative funding — short squeeze risk / favorable" in report.reasoning
