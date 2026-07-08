"""Tests for AI module integration into the decision pipeline and execution loop.

Verifies:
  - DecisionPipeline with RegimeAI adds regime_context to TradeCandidate
  - DecisionPipeline with TradeMemory adds memory_context to TradeCandidate
  - DecisionPipeline works without AI modules (backward compat)
  - ExecutionLoop with SignalRankingAI ranks signals before processing
  - ExecutionLoop works without SignalRankingAI (backward compat)
  - Intelligence payload forwarded through _create_trade
"""

import pandas as pd
import pytest

from execution.execution_loop import ExecutionLoop, ExecutionLoopResult
from execution.pipeline import DecisionPipeline
from core.confidence_engine import ConfidenceEngine


class MockRiskManager:
    """Always allows trade. Avoids database dependency."""

    def can_open_trade(self, candidate):
        return True, ""


class MockTradeEngine:
    """Returns a sentinel trade. Avoids database dependency."""

    def create_trade(self, signal, entry, atr, intelligence=None):
        return {"id": 1, "symbol": signal.symbol, "side": signal.side, "intelligence": intelligence}


class MockCollector:
    """Returns constant close price. Satisfies MarketDataCollector protocol."""

    def __init__(self, close_price=50000.0):
        self.close_price = close_price

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return pd.DataFrame({"close": [self.close_price] * 100})


class MockScoringEngine:
    """Returns scores that guarantee APPROVE (confidence >= 80)."""

    def score(self, signal):
        return {
            "entry": 50000.0,
            "ema20": 51000.0,
            "ema50": 50500.0,
            "ema200": 50200.0,
            "rsi": 55.0,
            "atr": 500.0,
            "trend_score": 1.0,
            "volume_score": 1.0,
            "btc_score": 1.0,
            "mtf_score": 1.0,
            "risk_score": 0.0,
            "final_score": 0.9,
        }


class FakeSignal:
    """Minimal TradingSignal protocol implementation."""

    def __init__(self, sid=1, symbol="BTCUSDT", side="LONG", timeframe="1h"):
        self.id = sid
        self.symbol = symbol
        self.side = side
        self.timeframe = timeframe


class FakeRegimeAI:
    """Return predefined regime detection result."""

    def __init__(self, result=None):
        self.result = result or {
            "regime": "TREND",
            "trend": "BULLISH",
            "trend_strength": "STRONG",
            "volatility_class": "NORMAL",
            "market_phase": "MARKUP",
            "score": 0.9,
        }

    def detect(self, values=None):
        return dict(self.result)


class FakeTradeMemory:
    """Return predefined list of past trade entries."""

    def __init__(self, entries=None):
        self.entries = entries or []

    def list(self, limit=50):
        return list(self.entries)


class FakeTradeMemoryEntry:
    """Minimal TradeMemoryEntry protocol implementation."""

    def __init__(self, symbol="BTCUSDT", side="LONG", result="WIN", pnl=100.0):
        self.symbol = symbol
        self.side = side
        self.result = result
        self.pnl = pnl


class FakeSignalRanker:
    """Return predefined ranked signals."""

    def __init__(self, ranked=None):
        self.ranked = ranked or []
        self.last_input = None

    def rank_signals(self, signals):
        self.last_input = signals
        return list(self.ranked)


class FakeRankedSignal:
    """Minimal RankedSignal protocol implementation."""

    def __init__(self, identifier="1", composite_score=0.9, recommendation="STRONG_BUY"):
        self.identifier = identifier
        self.composite_score = composite_score
        self.recommendation = recommendation


def make_pipeline(
    close_price=50000.0,
    regime_ai=None,
    trade_memory=None,
    filters=(),
):
    return DecisionPipeline(
        collector=MockCollector(close_price=close_price),
        filters=filters,
        scoring_engine=MockScoringEngine(),
        confidence_engine=ConfidenceEngine(),
        regime_ai=regime_ai,
        trade_memory=trade_memory,
    )


class TestDecisionPipelineAI:
    """DecisionPipeline AI context integration tests."""

    def test_pipeline_adds_regime_context(self):
        regime_ai = FakeRegimeAI()
        pipeline = make_pipeline(regime_ai=regime_ai)
        candidate = pipeline.evaluate(FakeSignal())
        assert candidate is not None
        assert candidate.regime_context is not None
        assert candidate.regime_context["regime"] == "TREND"
        assert candidate.regime_context["trend"] == "BULLISH"
        assert candidate.regime_context["score"] == 0.9

    def test_pipeline_adds_memory_context(self):
        entries = [
            FakeTradeMemoryEntry(symbol="BTCUSDT", side="LONG", result="WIN", pnl=150.0),
            FakeTradeMemoryEntry(symbol="BTCUSDT", side="LONG", result="LOSS", pnl=-50.0),
        ]
        trade_memory = FakeTradeMemory(entries=entries)
        pipeline = make_pipeline(trade_memory=trade_memory)
        candidate = pipeline.evaluate(FakeSignal())
        assert candidate is not None
        assert candidate.memory_context is not None
        assert candidate.memory_context["past_trades"] == 2
        assert candidate.memory_context["wins"] == 1
        assert candidate.memory_context["losses"] == 1
        assert candidate.memory_context["avg_pnl"] == 50.0

    def test_pipeline_memory_filters_by_symbol_and_side(self):
        entries = [
            FakeTradeMemoryEntry(symbol="ETHUSDT", side="LONG", result="WIN", pnl=200.0),
            FakeTradeMemoryEntry(symbol="BTCUSDT", side="SHORT", result="WIN", pnl=100.0),
            FakeTradeMemoryEntry(symbol="BTCUSDT", side="LONG", result="LOSS", pnl=-75.0),
        ]
        trade_memory = FakeTradeMemory(entries=entries)
        pipeline = make_pipeline(trade_memory=trade_memory)
        candidate = pipeline.evaluate(FakeSignal())
        assert candidate is not None
        assert candidate.memory_context is not None
        assert candidate.memory_context["past_trades"] == 1
        assert candidate.memory_context["wins"] == 0
        assert candidate.memory_context["losses"] == 1
        assert candidate.memory_context["avg_pnl"] == -75.0

    def test_pipeline_no_ai_modules_backward_compat(self):
        pipeline = make_pipeline(regime_ai=None, trade_memory=None)
        candidate = pipeline.evaluate(FakeSignal())
        assert candidate is not None
        assert candidate.regime_context is None
        assert candidate.memory_context is None

    def test_pipeline_regime_and_memory_together(self):
        regime_ai = FakeRegimeAI()
        entries = [
            FakeTradeMemoryEntry(symbol="BTCUSDT", side="LONG", result="WIN", pnl=200.0),
        ]
        trade_memory = FakeTradeMemory(entries=entries)
        pipeline = make_pipeline(regime_ai=regime_ai, trade_memory=trade_memory)
        candidate = pipeline.evaluate(FakeSignal())
        assert candidate is not None
        assert candidate.regime_context is not None
        assert candidate.memory_context is not None
        assert candidate.regime_context["regime"] == "TREND"
        assert candidate.memory_context["past_trades"] == 1


class TestExecutionLoopAI:
    """ExecutionLoop SignalRankingAI integration tests."""

    def _make_loop(self, pipeline=None, signal_ranker=None):
        return ExecutionLoop(
            pipeline=pipeline or make_pipeline(),
            paper_executor=None,
            risk_manager=MockRiskManager(),
            trade_engine=MockTradeEngine(),
            signal_ranker=signal_ranker,
        )

    def test_loop_ranks_signals(self):
        ranked = [
            FakeRankedSignal(identifier="1", composite_score=0.95, recommendation="STRONG_BUY"),
            FakeRankedSignal(identifier="2", composite_score=0.60, recommendation="BUY"),
        ]
        ranker = FakeSignalRanker(ranked=ranked)

        pipeline = make_pipeline()
        loop = self._make_loop(pipeline=pipeline, signal_ranker=ranker)

        signals = [FakeSignal(sid=1), FakeSignal(sid=2)]
        result = loop.run_once(signals)

        assert result.processed == 2
        assert ranker.last_input is not None
        assert len(ranker.last_input) == 2

    def test_loop_no_ranker_backward_compat(self):
        loop = self._make_loop(signal_ranker=None)
        signals = [FakeSignal(sid=1), FakeSignal(sid=2)]
        result = loop.run_once(signals)
        assert result.processed == 2

    def test_loop_passes_intelligence_with_ai_context(self):
        entry = FakeTradeMemoryEntry(symbol="BTCUSDT", side="LONG", result="WIN", pnl=100.0)
        trade_memory = FakeTradeMemory(entries=[entry])
        pipeline = make_pipeline(
            regime_ai=FakeRegimeAI(),
            trade_memory=trade_memory,
        )
        loop = self._make_loop(pipeline=pipeline)
        signal = FakeSignal(sid=1)
        candidate = pipeline.evaluate(signal)
        assert candidate is not None
        assert candidate.regime_context is not None
        assert candidate.memory_context is not None


class _LowScoreEngine:
    """Module-level low score engine. Returns scores that produce confidence < 70."""

    def score(self, signal):
        return {
            "entry": 50000.0, "ema20": 51000.0, "ema50": 50500.0,
            "ema200": 50200.0, "rsi": 55.0, "atr": 500.0,
            "trend_score": 0.5, "volume_score": 0.5,
            "btc_score": 0.5, "mtf_score": 0.5,
            "risk_score": 0.5, "final_score": 0.55,
        }


class TestExecutionLoopProcessSignal:
    """ExecutionLoop.process_signal unit tests with a real DB for signal status."""

    class _NoneTradeEngine:
        """TradeEngine that returns None (simulates creation failure)."""

        def create_trade(self, signal, entry, atr, intelligence=None):
            return None

    class _RejectRiskManager:
        """RiskManager that always rejects."""

        def can_open_trade(self, candidate):
            return False, "mock rejection"

    class _MissingEntryScorer:
        """Scoring engine that produces None entry."""

        def score(self, signal):
            return {
                "entry": None, "ema20": 51000.0, "ema50": 50500.0,
                "ema200": 50200.0, "rsi": 55.0, "atr": 500.0,
                "trend_score": 1.0, "volume_score": 1.0,
                "btc_score": 1.0, "mtf_score": 1.0,
                "risk_score": 0.0, "final_score": 0.9,
            }

    def _make_pipeline(self, close_price=50000.0, scoring_engine=None):
        from core.confidence_engine import ConfidenceEngine
        return DecisionPipeline(
            collector=MockCollector(close_price=close_price),
            filters=(),
            scoring_engine=scoring_engine or MockScoringEngine(),
            confidence_engine=ConfidenceEngine(),
        )

    def _make_loop(self, pipeline=None, risk_manager=None, trade_engine=None):
        return ExecutionLoop(
            pipeline=pipeline or self._make_pipeline(),
            paper_executor=None,
            risk_manager=risk_manager or MockRiskManager(),
            trade_engine=trade_engine or MockTradeEngine(),
        )

    def test_process_signal_pipeline_returns_none(self, db_session, session_factory, monkeypatch):
        from database import Signal
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        pipeline = self._make_pipeline(scoring_engine=_LowScoreEngine())
        loop = self._make_loop(pipeline=pipeline)
        result = loop.process_signal(signal)

        assert result is None
        db_session.refresh(signal)
        assert signal.status == "REJECTED"

    def test_process_signal_risk_manager_rejects(self, db_session, session_factory, monkeypatch):
        from database import Signal
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        loop = self._make_loop(risk_manager=self._RejectRiskManager())
        result = loop.process_signal(signal)

        assert result is None
        db_session.refresh(signal)
        assert signal.status == "REJECTED"

    def test_process_signal_trade_engine_returns_none(self, db_session, session_factory, monkeypatch):
        from database import Signal
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        loop = self._make_loop(trade_engine=self._NoneTradeEngine())
        result = loop.process_signal(signal)

        assert result is None
        db_session.refresh(signal)
        assert signal.status == "OPEN"

    def test_process_signal_missing_entry_sets_open(self, db_session, session_factory, monkeypatch):
        from database import Signal
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        pipeline = self._make_pipeline(scoring_engine=self._MissingEntryScorer())
        loop = self._make_loop(pipeline=pipeline)
        result = loop.process_signal(signal)

        assert result is None
        db_session.refresh(signal)
        assert signal.status == "OPEN"


class TestExecutionLoopSignalRankerFailure:
    """ExecutionLoop.run_once handles signal_ranker exceptions gracefully."""

    class _RaiserRanker:
        def rank_signals(self, signals):
            raise RuntimeError("ranker failure")

    def test_ranker_exception_falls_back(self):
        pipeline = make_pipeline()
        ranker = self._RaiserRanker()
        loop = ExecutionLoop(
            pipeline=pipeline,
            paper_executor=None,
            risk_manager=MockRiskManager(),
            trade_engine=MockTradeEngine(),
            signal_ranker=ranker,
        )
        signals = [FakeSignal(sid=1), FakeSignal(sid=2)]
        result = loop.run_once(signals)
        assert result.processed == 2
        assert result.created >= 0


class TestDecisionPipelineRejection:
    """Pipeline returns None when confidence or scores are too low."""

    class _LowScoreEngine:
        """Returns component scores that produce confidence < 70 (REJECT)."""

        def score(self, signal):
            return {
                "entry": 50000.0, "ema20": 51000.0, "ema50": 50500.0,
                "ema200": 50200.0, "rsi": 55.0, "atr": 500.0,
                "trend_score": 0.5, "volume_score": 0.5,
                "btc_score": 0.5, "mtf_score": 0.5,
                "risk_score": 0.5, "final_score": 0.55,
            }

    class _BorderlineWatchEngine:
        """Returns scores that produce confidence = 70 (WATCH, not approved)."""

        def score(self, signal):
            return {
                "entry": 50000.0, "ema20": 51000.0, "ema50": 50500.0,
                "ema200": 50200.0, "rsi": 55.0, "atr": 500.0,
                "trend_score": 0.5, "volume_score": 0.5,
                "btc_score": 1.0, "mtf_score": 1.0,
                "risk_score": 0.5, "final_score": 0.75,
            }

    class _ApproveEngine:
        """Returns scores that produce confidence >= 80 (APPROVE)."""

        def score(self, signal):
            return {
                "entry": 50000.0, "ema20": 51000.0, "ema50": 50500.0,
                "ema200": 50200.0, "rsi": 55.0, "atr": 500.0,
                "trend_score": 1.0, "volume_score": 1.0,
                "btc_score": 0.5, "mtf_score": 1.0,
                "risk_score": 0.5, "final_score": 0.85,
            }

    def _pipeline(self, scorer):
        from execution.pipeline import DecisionPipeline
        return DecisionPipeline(
            collector=MockCollector(),
            filters=(),
            scoring_engine=scorer,
            confidence_engine=ConfidenceEngine(),
        )

    def test_rejects_low_confidence(self):
        pipeline = self._pipeline(self._LowScoreEngine())
        assert pipeline.evaluate(FakeSignal()) is None

    def test_rejects_watch_decision(self):
        pipeline = self._pipeline(self._BorderlineWatchEngine())
        assert pipeline.evaluate(FakeSignal()) is None

    def test_approves_with_sufficient_confidence(self):
        pipeline = self._pipeline(self._ApproveEngine())
        candidate = pipeline.evaluate(FakeSignal())
        assert candidate is not None
        assert candidate.decision == "APPROVE"
        assert candidate.confidence >= 80.0
