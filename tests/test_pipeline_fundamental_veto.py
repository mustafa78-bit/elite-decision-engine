"""Integration tests: DecisionPipeline actually calls and respects
council/fundamental_gate.py's check_fundamental_veto(). See conftest.py's
mock_fundamental_veto fixture -- this file is explicitly excluded from that
global "never veto" mock so these tests exercise the real wiring."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pandas as pd

from core.confidence_engine import ConfidenceEngine
from council.fundamental_gate import FundamentalVetoResult
from execution.pipeline import DecisionPipeline


@dataclass(frozen=True)
class _Signal:
    id: int = 1
    symbol: str = "BTCUSDT"
    side: str = "LONG"
    timeframe: str = "1h"


class _MockCollector:
    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return pd.DataFrame({"close": [50000.0] * 100})


class _ApprovingScoringEngine:
    """Guarantees APPROVE (confidence >= 80) -- isolates this test from
    ScoringEngine's own logic, only the veto gate's effect is under test."""

    def score(self, signal):
        return {
            "entry": 50000.0, "ema20": 51000.0, "ema50": 50500.0, "ema200": 50200.0,
            "rsi": 55.0, "atr": 500.0,
            "trend_score": 1.0, "volume_score": 1.0, "btc_score": 1.0,
            "mtf_score": 1.0, "risk_score": 0.0, "final_score": 0.9,
        }


def _build_pipeline(fundamental_veto_enabled: bool = True) -> DecisionPipeline:
    return DecisionPipeline(
        collector=_MockCollector(),
        filters=(),
        scoring_engine=_ApprovingScoringEngine(),
        confidence_engine=ConfidenceEngine(),
        fundamental_veto_enabled=fundamental_veto_enabled,
    )


class TestPipelineFundamentalVeto:

    def test_approved_signal_passes_when_no_veto(self):
        pipeline = _build_pipeline()
        with patch(
            "council.fundamental_gate.check_fundamental_veto",
            return_value=FundamentalVetoResult(False, None),
        ):
            candidate = pipeline.evaluate(_Signal())
        assert candidate is not None
        assert candidate.decision in ("APPROVE", "STRONG_APPROVE")

    def test_approved_signal_rejected_when_vetoed(self):
        pipeline = _build_pipeline()
        with patch(
            "council.fundamental_gate.check_fundamental_veto",
            return_value=FundamentalVetoResult(True, "2/3 fundamental agents contradict this LONG on BTCUSDT"),
        ) as mock_veto:
            candidate = pipeline.evaluate(_Signal())
        assert candidate is None
        mock_veto.assert_called_once_with("BTCUSDT", "LONG", "1h")

    def test_veto_check_skipped_when_disabled(self):
        # fundamental_veto_enabled=False -- the gate must not even be called,
        # regardless of what it would have returned.
        pipeline = _build_pipeline(fundamental_veto_enabled=False)
        with patch("council.fundamental_gate.check_fundamental_veto") as mock_veto:
            candidate = pipeline.evaluate(_Signal())
        assert candidate is not None
        mock_veto.assert_not_called()

    def test_veto_never_overrides_a_rejection(self):
        # The gate can only block an approval, never rescue a rejection --
        # confirm a genuinely low-confidence signal stays rejected regardless
        # of what the veto check would say.
        class _RejectingScoringEngine:
            def score(self, signal):
                return {
                    "entry": 50000.0, "ema20": 51000.0, "ema50": 50500.0, "ema200": 50200.0,
                    "rsi": 55.0, "atr": 500.0,
                    "trend_score": 0.5, "volume_score": 0.5, "btc_score": 0.5,
                    "mtf_score": 0.5, "risk_score": 0.5, "final_score": 0.55,
                }

        pipeline = DecisionPipeline(
            collector=_MockCollector(),
            filters=(),
            scoring_engine=_RejectingScoringEngine(),
            confidence_engine=ConfidenceEngine(),
            fundamental_veto_enabled=True,
        )
        with patch("council.fundamental_gate.check_fundamental_veto") as mock_veto:
            candidate = pipeline.evaluate(_Signal())
        assert candidate is None
        mock_veto.assert_not_called()
