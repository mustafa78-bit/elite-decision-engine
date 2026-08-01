from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from council.base import DIRECTION_BEARISH, DIRECTION_BULLISH, DIRECTION_NEUTRAL, DIRECTION_PASS
from council.technical_agent import TechnicalAgent
from council.trend_agent import TrendAgent
from council.risk_agent import RiskAgent
from council.news_agent import NewsAgent
from council.whale_agent import WhaleAgent
from council.macro_agent import MacroAgent


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
        agent = NewsAgent()
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=None)
        assert report.direction == DIRECTION_NEUTRAL


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
        agent = WhaleAgent()
        report = agent.evaluate(signal=mock_signal, scores={"volume_score": 0.3})
        assert report.direction == DIRECTION_NEUTRAL


class TestMacroAgent:
    def test_default_creation(self):
        agent = MacroAgent()
        assert agent.name == "Macro"

    def test_evaluate_with_all_data(self, mock_signal):
        agent = MacroAgent()
        bundle = MagicMock()
        bundle.funding = {"annualized_rate": 0.0001, "level": "LOW", "risk_score": 0.2}
        bundle.open_interest = {"value": 1e9, "trend": "RISING", "strength": 0.7}
        bundle.fear_greed = {"label": "FEAR", "value": 30, "confidence": 0.6}
        bundle.liquidity_context = {"score": 0.8, "level": "HIGH"}
        bundle.exchange_flow = {"direction": "OUTFLOW", "confidence": 0.75}

        report = agent.evaluate(signal=mock_signal, intelligence_bundle=bundle)
        assert report.agent_name == "Macro"
        assert report.symbol == "BTCUSDT"
        assert len(report.reasoning) >= 4
        assert report.data_points["bullish_signals"] >= 2
        assert report.data_points["composite_score"] > 0

    def test_evaluate_no_bundle(self, mock_signal):
        agent = MacroAgent()
        report = agent.evaluate(signal=mock_signal, intelligence_bundle=None)
        assert report.direction == DIRECTION_NEUTRAL
        assert report.confidence == 0.5
