"""Tests for database.reap_orphaned_processing_signals().

A Signal can only be left in PROCESSING if a prior process crashed mid-
DecisionEngine.process_signal() -- see the function's own docstring and
core/engine.py. This reaper resets any such orphaned rows back to OPEN so
they get picked up again, and is called once at api/main.py lifespan()
startup (see TestReaperWiredIntoLifespan below).
"""

import inspect

from database import Signal, reap_orphaned_processing_signals


class TestReapOrphanedProcessingSignals:
    def test_processing_signal_is_reset_to_open(self, db_session):
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="PROCESSING")
        db_session.add(signal)
        db_session.commit()

        count = reap_orphaned_processing_signals()

        assert count == 1
        db_session.refresh(signal)
        assert signal.status == "OPEN"

    def test_returns_correct_count_for_multiple_orphaned_signals(self, db_session):
        for _ in range(3):
            db_session.add(Signal(symbol="ETHUSDT", side="SHORT", timeframe="1h", status="PROCESSING"))
        db_session.commit()

        count = reap_orphaned_processing_signals()

        assert count == 3

    def test_other_statuses_are_left_untouched(self, db_session):
        open_signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        rejected_signal = Signal(symbol="ETHUSDT", side="SHORT", timeframe="1h", status="REJECTED")
        executed_signal = Signal(symbol="SOLUSDT", side="LONG", timeframe="1h", status="EXECUTED")
        db_session.add_all([open_signal, rejected_signal, executed_signal])
        db_session.commit()

        count = reap_orphaned_processing_signals()

        assert count == 0
        db_session.refresh(open_signal)
        db_session.refresh(rejected_signal)
        db_session.refresh(executed_signal)
        assert open_signal.status == "OPEN"
        assert rejected_signal.status == "REJECTED"
        assert executed_signal.status == "EXECUTED"

    def test_no_orphaned_signals_returns_zero(self, db_session):
        assert reap_orphaned_processing_signals() == 0


class TestReaperWiredIntoLifespan:
    def test_reaper_runs_before_auto_trading_tasks_are_created(self):
        from api.main import lifespan

        source = inspect.getsource(lifespan)
        migrations_idx = source.index("database.run_migrations()")
        reap_idx = source.index("database.reap_orphaned_processing_signals()")
        guard_idx = source.index("if AUTO_TRADING_ENABLED:")

        assert migrations_idx < reap_idx < guard_idx

    def test_threadpool_capacity_is_raised_before_migrations_run(self):
        # anyio's default sync-route threadpool limiter (40 tokens, shared
        # by ~187/193 sync routes) is raised as the very first thing
        # lifespan() does -- see that line's own comment for the live
        # 2026-08-20 finding (GET /risk took 4-5 minutes under load) that
        # motivated this. Must run before anything else queues work onto
        # it, so before even the DB migrations call.
        from api.main import lifespan

        source = inspect.getsource(lifespan)
        limiter_idx = source.index("current_default_thread_limiter()")
        migrations_idx = source.index("database.run_migrations()")

        assert limiter_idx < migrations_idx
