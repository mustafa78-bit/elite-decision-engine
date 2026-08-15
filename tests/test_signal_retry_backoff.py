"""Tests for the signal retry/backoff mechanism.

DecisionEngine.process_signal() (core/engine.py) marks a signal PROCESSING
then runs it through execution_loop.run_once(). An *exception* during that
call -- a transient failure like a network blip or a momentary DB error --
now gets a backoff-delayed retry via database.schedule_signal_retry()
instead of an immediate permanent REJECTED, up to config.MAX_SIGNAL_RETRIES.

This is deliberately distinct from the two *deliberate* REJECTED verdicts
inside execution/execution_loop.py (low pipeline confidence, risk-manager
rejection) -- those complete run_once() normally (no exception), so
process_signal() never even reaches the retry-scheduling code for them.
"""

from datetime import UTC, datetime, timedelta

from config import MAX_SIGNAL_RETRIES, SIGNAL_RETRY_BACKOFF_SECONDS
from core.engine import DecisionEngine
from database import Signal, schedule_signal_retry


class _RecordingExecutionLoop:
    def __init__(self, side_effect=None) -> None:
        self.run_once_calls: list[list] = []
        self._side_effect = side_effect

    def run_once(self, signals):
        signal_list = list(signals)
        self.run_once_calls.append(signal_list)
        if self._side_effect is not None:
            self._side_effect(signal_list)
        return signal_list


def _aware(dt):
    """SQLite doesn't persist tzinfo for DateTime(timezone=True) -- values
    read back from it are naive even though written as UTC-aware. Normalize
    before comparing against a fresh datetime.now(UTC)."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _make_signal(db_session, status="OPEN", retry_count=0, next_retry_at=None):
    signal = Signal(
        symbol="BTCUSDT", side="LONG", timeframe="1h",
        status=status, retry_count=retry_count, next_retry_at=next_retry_at,
    )
    db_session.add(signal)
    db_session.commit()
    return signal


class TestScheduleSignalRetry:
    def test_first_failure_schedules_retry_and_sets_open(self, db_session):
        signal = _make_signal(db_session)

        result = schedule_signal_retry(signal.id)

        assert result is True
        db_session.refresh(signal)
        assert signal.status == "OPEN"
        assert signal.retry_count == 1
        assert signal.next_retry_at is not None
        assert _aware(signal.next_retry_at) > datetime.now(UTC)

    def test_backoff_delay_increases_with_retry_count(self, db_session):
        signal = _make_signal(db_session, retry_count=1)

        schedule_signal_retry(signal.id)

        db_session.refresh(signal)
        assert signal.retry_count == 2
        expected_delay = SIGNAL_RETRY_BACKOFF_SECONDS[1]
        delta = (_aware(signal.next_retry_at) - datetime.now(UTC)).total_seconds()
        assert expected_delay - 5 <= delta <= expected_delay + 5

    def test_retries_exhausted_returns_false_and_leaves_signal_untouched(self, db_session):
        signal = _make_signal(db_session, retry_count=MAX_SIGNAL_RETRIES)

        result = schedule_signal_retry(signal.id)

        assert result is False
        db_session.refresh(signal)
        assert signal.retry_count == MAX_SIGNAL_RETRIES
        assert signal.next_retry_at is None


class TestProcessSignalRetryVsReject:
    def test_exception_with_retries_remaining_goes_back_to_open(self, db_session):
        signal = _make_signal(db_session)

        def _raise(_signals):
            raise RuntimeError("simulated transient failure")

        loop = _RecordingExecutionLoop(side_effect=_raise)
        engine = DecisionEngine(execution_loop=loop)

        engine.process_signal(signal)

        db_session.refresh(signal)
        assert signal.status == "OPEN"
        assert signal.retry_count == 1
        assert signal.next_retry_at is not None

    def test_exception_after_retries_exhausted_rejects(self, db_session):
        signal = _make_signal(db_session, retry_count=MAX_SIGNAL_RETRIES)

        def _raise(_signals):
            raise RuntimeError("simulated transient failure")

        loop = _RecordingExecutionLoop(side_effect=_raise)
        engine = DecisionEngine(execution_loop=loop)

        engine.process_signal(signal)

        db_session.refresh(signal)
        assert signal.status == "REJECTED"
        assert signal.retry_count == MAX_SIGNAL_RETRIES

    def test_deliberate_rejection_without_exception_never_touches_retry(self, db_session):
        signal = _make_signal(db_session)

        def _deliberate_reject(signal_list):
            # Simulates execution_loop.py's own process_signal() rejecting
            # via the pipeline/risk-manager path: it writes REJECTED
            # directly and returns normally, no exception raised.
            signal_list[0].status = "REJECTED"
            db_session.commit()

        loop = _RecordingExecutionLoop(side_effect=_deliberate_reject)
        engine = DecisionEngine(execution_loop=loop)

        engine.process_signal(signal)

        db_session.refresh(signal)
        assert signal.status == "REJECTED"
        assert signal.retry_count == 0
        assert signal.next_retry_at is None


class TestGetOpenSignalsRespectsBackoff:
    def test_excludes_signal_with_future_next_retry_at(self, db_session):
        future = datetime.now(UTC) + timedelta(seconds=300)
        _make_signal(db_session, retry_count=1, next_retry_at=future)

        engine = DecisionEngine(execution_loop=_RecordingExecutionLoop())
        open_signals = engine.get_open_signals()

        assert open_signals == []

    def test_includes_signal_with_past_next_retry_at(self, db_session):
        past = datetime.now(UTC) - timedelta(seconds=5)
        signal = _make_signal(db_session, retry_count=1, next_retry_at=past)

        engine = DecisionEngine(execution_loop=_RecordingExecutionLoop())
        open_signals = engine.get_open_signals()

        assert [s.id for s in open_signals] == [signal.id]

    def test_includes_signal_with_no_next_retry_at(self, db_session):
        signal = _make_signal(db_session)

        engine = DecisionEngine(execution_loop=_RecordingExecutionLoop())
        open_signals = engine.get_open_signals()

        assert [s.id for s in open_signals] == [signal.id]
