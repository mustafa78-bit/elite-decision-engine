"""Tests for core.engine.DecisionEngine._process_open_signals().

Covers a real production bug: run_once() always monitors open paper trades
(TP/SL/staleness) as its last step, but the only caller previously skipped
run_once() entirely whenever there were zero open signals -- meaning every
currently-open trade stopped being monitored the moment the signal queue
drained, until some unrelated new signal happened to arrive.
"""

from __future__ import annotations

import core.engine as engine_module
from core.engine import DecisionEngine


class _RecordingExecutionLoop:
    def __init__(self) -> None:
        self.run_once_calls: list[list] = []

    def run_once(self, signals):
        signal_list = list(signals)
        self.run_once_calls.append(signal_list)
        return signal_list


def _make_engine(loop: _RecordingExecutionLoop, open_signals: list) -> DecisionEngine:
    engine = DecisionEngine(execution_loop=loop)
    engine.get_open_signals = lambda: open_signals
    return engine


class TestProcessOpenSignalsMonitorsTradesEvenWhenQueueIsEmpty:
    def test_run_once_still_fires_with_zero_open_signals(self):
        loop = _RecordingExecutionLoop()
        engine = _make_engine(loop, [])

        engine._process_open_signals()

        assert len(loop.run_once_calls) == 1
        assert loop.run_once_calls[0] == []

    def test_run_once_fires_per_signal_when_signals_exist(self, monkeypatch):
        monkeypatch.setattr(engine_module, "update_signal_status", lambda *a, **k: None)
        loop = _RecordingExecutionLoop()

        class _Signal:
            id = 1
            symbol = "BTCUSDT"
            side = "LONG"
            timeframe = "1h"

        engine = _make_engine(loop, [_Signal()])

        engine._process_open_signals()

        # One run_once call per real signal (existing behavior) -- no
        # separate zero-signal monitor-only call gets added on top when
        # signals were actually present.
        assert len(loop.run_once_calls) == 1
        assert len(loop.run_once_calls[0]) == 1
