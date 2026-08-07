"""Tests for simulator/report_generator.py's ReportGenerator."""

from __future__ import annotations

from simulator.models import SimulatedTrade, SimulatorState
from simulator.report_generator import ReportGenerator


def _make_trade(trade_id, pnl, entry_decision=None, close_reason=None):
    return SimulatedTrade(
        id=trade_id,
        symbol="BTCUSDT",
        side="LONG",
        entry_price=50000.0,
        entry_time=0,
        quantity=1.0,
        leverage=1.0,
        stop_loss=49000.0,
        take_profit=51000.0,
        status="CLOSED",
        exit_price=50000.0 + pnl,
        exit_time=1000,
        pnl=pnl,
        pnl_percent=pnl / 50000.0 * 100,
        entry_decision=entry_decision,
        close_reason=close_reason,
    )


class TestProfitFactor:
    def test_profit_factor_uses_sum_not_average(self):
        # 9 wins of +100 (gross_profit=900), 1 loss of -900 (gross_loss=900)
        # -- a breakeven strategy, real profit_factor should be 1.0.
        # The old avg-based bug (avg_win=100, avg_loss=900) would report ~0.11.
        trades = [_make_trade(f"w{i}", 100.0) for i in range(9)]
        trades.append(_make_trade("l0", -900.0))
        state = SimulatorState(session_id="s1", trades=trades)

        report = ReportGenerator().generate(state)
        assert report.profit_factor == 1.0

    def test_profit_factor_inverse_case_still_breakeven(self):
        # 1 win of +900, 9 losses of -100 each -- also breakeven, profit_factor
        # should still be 1.0, not 9.0 (the old bug would flip depending on
        # which side had more trades).
        trades = [_make_trade("w0", 900.0)]
        trades.extend(_make_trade(f"l{i}", -100.0) for i in range(9))
        state = SimulatorState(session_id="s2", trades=trades)

        report = ReportGenerator().generate(state)
        assert report.profit_factor == 1.0


class TestEntryQualityScore:
    def test_entry_quality_uses_0_100_scale_threshold(self):
        # entry_decision["confidence"] is stored on a 0-100 scale. A trade
        # with confidence=72 (real high-confidence entry) should count as a
        # good entry; confidence=50 should not.
        trades = [
            _make_trade("t1", 100.0, entry_decision={"confidence": 72.0}),
            _make_trade("t2", -50.0, entry_decision={"confidence": 50.0}),
        ]
        state = SimulatorState(session_id="s3", trades=trades)

        report = ReportGenerator().generate(state)
        # Only 1 of 2 trades had confidence > 60 -> 50.0
        assert report.training_score.entry_quality == 50.0

    def test_entry_quality_all_low_confidence(self):
        trades = [
            _make_trade("t1", 100.0, entry_decision={"confidence": 55.0}),
            _make_trade("t2", -50.0, entry_decision={"confidence": 40.0}),
        ]
        state = SimulatorState(session_id="s4", trades=trades)

        report = ReportGenerator().generate(state)
        assert report.training_score.entry_quality == 0.0


class TestCloseReasonVocabulary:
    """simulator_engine.py only ever sets close_reason to STOP_LOSS,
    TAKE_PROFIT, or MANUAL_CLOSE -- report_generator.py previously also
    checked for TP_HIT/SL_HIT/TRAILING_STOP/REVERSAL, none of which any
    producer ever emits, making those branches permanently dead."""

    def test_exit_quality_counts_real_take_profit_reason(self):
        trades = [_make_trade("t1", 100.0, close_reason="TAKE_PROFIT")]
        state = SimulatorState(session_id="s5", trades=trades)
        report = ReportGenerator().generate(state)
        assert report.training_score.exit_quality == 100.0

    def test_psychology_ignores_dead_reversal_reason(self):
        # Even if something set close_reason="REVERSAL" (no real producer
        # does), it must not affect the psychology score -- that penalty
        # was pure dead code and has been removed.
        trades = [_make_trade("t1", -10.0, close_reason="REVERSAL") for _ in range(3)]
        state = SimulatorState(session_id="s6", trades=trades)
        report = ReportGenerator().generate(state)
        assert report.training_score.psychology == 100.0

    def test_find_mistakes_only_uses_real_stop_loss_reason(self):
        # A trade with close_reason="SL_HIT" (dead vocabulary) and a large
        # loss must NOT produce the "large loss" mistake message -- only the
        # real "STOP_LOSS" reason does.
        trades = [_make_trade("t1", -2000.0, close_reason="SL_HIT")]
        trades[0].pnl_percent = -4.0
        state = SimulatorState(session_id="s7", trades=trades)
        report = ReportGenerator().generate(state)
        assert not any("large loss" in m for m in report.mistakes)
