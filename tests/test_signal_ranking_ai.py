"""Tests for signal ranking AI."""

from scoring.signal_ranking_ai import RankedSignal, SignalRankingAI


class TestSignalRankingAI:
    def test_rank_signals(self):
        ai = SignalRankingAI()
        signals = [
            {"id": 1, "symbol": "BTC", "side": "LONG", "score": 90, "confidence": 85},
            {"id": 2, "symbol": "ETH", "side": "SHORT", "score": 60, "confidence": 55},
            {"id": 3, "symbol": "SOL", "side": "LONG", "score": 75, "confidence": 70},
        ]
        ranked = ai.rank_signals(signals)
        assert len(ranked) == 3
        assert ranked[0].rank == 1
        assert ranked[2].rank == 3
        assert ranked[0].composite_score >= ranked[1].composite_score

    def test_ranked_signal_dataclass(self):
        rs = RankedSignal(rank=1, signal_id=1, symbol="BTC", side="LONG", raw_score=90, confidence=85, historical_win_rate=0.6, trend_alignment=0.8, volatility_condition=0.7, regime_alignment=0.9, composite_score=0.85, recommendation="STRONG_BUY")
        assert rs.symbol == "BTC"
        assert rs.recommendation == "STRONG_BUY"

    def test_top_signal_strong_buy(self):
        ai = SignalRankingAI()
        signals = [{"id": 1, "symbol": "BTC", "side": "LONG", "score": 95, "confidence": 90, "historical_win_rate": 0.8, "trend_alignment": 0.9, "volatility_condition": 0.9, "regime_alignment": 0.9}]
        ranked = ai.rank_signals(signals)
        assert ranked[0].recommendation in ("STRONG_BUY", "BUY")

    def test_low_signal_pass(self):
        ai = SignalRankingAI()
        signals = [{"id": 1, "symbol": "BTC", "side": "LONG", "score": 10, "confidence": 5}]
        ranked = ai.rank_signals(signals)
        assert ranked[0].recommendation == "PASS"

    def test_trend_alignment_long_bullish(self):
        ai = SignalRankingAI()
        assert ai.get_trend_alignment("LONG", "BULLISH") == 1.0

    def test_trend_alignment_short_bullish(self):
        ai = SignalRankingAI()
        assert ai.get_trend_alignment("SHORT", "BULLISH") == 0.1

    def test_volatility_condition_normal(self):
        ai = SignalRankingAI()
        assert ai.get_volatility_condition("NORMAL") == 1.0

    def test_volatility_condition_extreme(self):
        ai = SignalRankingAI()
        assert ai.get_volatility_condition("EXTREME") == 0.1

    def test_regime_alignment_long_trend(self):
        ai = SignalRankingAI()
        assert ai.get_regime_alignment("LONG", "TREND") == 1.0

    def test_regime_alignment_short_trend(self):
        ai = SignalRankingAI()
        assert ai.get_regime_alignment("SHORT", "TREND") == 0.1

    def test_regime_alignment_long_dead(self):
        ai = SignalRankingAI()
        assert ai.get_regime_alignment("LONG", "DEAD") == 0.0
