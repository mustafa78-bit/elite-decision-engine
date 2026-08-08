"""Tests for the Scanner -> Signal -> DecisionEngine automation bridge.

Covers:
  - config.AUTO_TRADING_ENABLED / SCAN_INTERVAL_SECONDS defaults
  - scanner price/trend_score threading through OpportunityRanker
  - services.signal_generator.generate_signals dedup behavior
  - the two new background tasks in api/main.py's lifespan being gated
    behind AUTO_TRADING_ENABLED
  - ExecutionLoop/DecisionEngine constructed with a real PaperDomainExecutor
    trade_journal (full PaperOrder/PaperTrade coverage already lives in
    tests/test_integration.py::TestPaperTradeJournalIntegration)
"""

import asyncio
import inspect
from unittest.mock import MagicMock

import config
from core.engine import DecisionEngine
from database import Signal
from execution.execution_loop import ExecutionLoop
from execution.paper import PaperExecutor as PaperDomainExecutor
from scanner.models import Opportunity, ScanResult
from scanner.ranking import OpportunityRanker
from services.signal_generator import generate_signals


def _make_opportunity(
    symbol="BTCUSDT",
    side="LONG",
    price=50000.0,
    score=0.8,
    confidence=90.0,
    trend_score=0.5,
):
    return Opportunity(
        symbol=symbol,
        side=side,
        strategy="trend",
        score=score,
        confidence=confidence,
        price=price,
        trend_score=trend_score,
    )


class TestAutoTradingConfig:
    def test_defaults(self):
        assert isinstance(config.AUTO_TRADING_ENABLED, bool)
        assert isinstance(config.SCAN_INTERVAL_SECONDS, int)
        assert config.SCAN_INTERVAL_SECONDS > 0

    def test_auto_trading_disabled_by_default_in_test_env(self):
        # tests/conftest.py never sets AUTO_TRADING_ENABLED, so the default
        # (env unset -> "false") must hold in the test environment.
        assert config.AUTO_TRADING_ENABLED is False


class TestScannerPriceAndTrendScoreThreading:
    def test_rank_sets_price_and_trend_score_on_opportunity(self):
        ranker = OpportunityRanker()
        results = [
            ScanResult(
                symbol="BTCUSDT",
                price=63000.0,
                trend_score=0.9,
                momentum_score=0.2,
                breakout_score=0.0,
                reversal_score=0.0,
                liquidity_score=0.0,
            ),
        ]
        opportunities = ranker.rank(results)
        assert len(opportunities) == 1
        assert opportunities[0].price == 63000.0
        assert opportunities[0].trend_score == 0.9


class TestSignalGenerator:
    def test_creates_signal_for_new_opportunity(self, db_session):
        opp = _make_opportunity()
        created = generate_signals([opp], session=db_session)
        assert created == 1

        signal = (
            db_session.query(Signal)
            .filter(Signal.symbol == "BTCUSDT", Signal.side == "LONG")
            .first()
        )
        assert signal is not None
        assert signal.status == "OPEN"
        assert signal.price == 50000.0
        assert signal.score == 0.8
        assert signal.confidence == 90.0
        assert signal.trend_score == 0.5

    def test_skips_duplicate_when_open_signal_exists(self, db_session):
        existing = Signal(symbol="ETHUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(existing)
        db_session.flush()

        opp = _make_opportunity(symbol="ETHUSDT", side="LONG")
        created = generate_signals([opp], session=db_session)
        assert created == 0

        count = (
            db_session.query(Signal)
            .filter(Signal.symbol == "ETHUSDT", Signal.side == "LONG")
            .count()
        )
        assert count == 1

    def test_creates_new_signal_once_prior_signal_is_resolved(self, db_session):
        resolved = Signal(symbol="SOLUSDT", side="SHORT", timeframe="1h", status="EXECUTED")
        db_session.add(resolved)
        db_session.flush()

        opp = _make_opportunity(symbol="SOLUSDT", side="SHORT")
        created = generate_signals([opp], session=db_session)
        assert created == 1

    def test_different_side_is_not_deduped(self, db_session):
        existing = Signal(symbol="ADAUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(existing)
        db_session.flush()

        opp = _make_opportunity(symbol="ADAUSDT", side="SHORT")
        created = generate_signals([opp], session=db_session)
        assert created == 1


class TestAutoTradingLoopWiring:
    def test_decision_engine_can_be_constructed_with_real_trade_journal(self):
        journal = PaperDomainExecutor()
        loop = ExecutionLoop(trade_journal=journal)
        engine = DecisionEngine(execution_loop=loop)
        assert engine.execution_loop.trade_journal is journal


class TestAutoTradingBackgroundTasksGating:
    def test_new_tasks_are_created_inside_auto_trading_guard(self):
        from api.main import lifespan

        source = inspect.getsource(lifespan)
        guard_idx = source.index("if AUTO_TRADING_ENABLED:")
        scan_idx = source.index("_scan_and_generate_signals()")
        engine_idx = source.index("decision_engine.run()")
        periodic_idx = source.index("_periodic_broadcast()")

        assert guard_idx < scan_idx < periodic_idx
        assert guard_idx < engine_idx < periodic_idx

    async def test_scan_and_generate_signals_calls_scanner_and_generator(self, monkeypatch):
        import api.main as main_module

        monkeypatch.setattr(main_module, "SCAN_INTERVAL_SECONDS", 0)

        fake_opportunities = ["opp1", "opp2"]
        mock_scanner_instance = MagicMock()
        mock_scanner_instance.scan.return_value = fake_opportunities
        monkeypatch.setattr(main_module, "OpportunityScanner", lambda: mock_scanner_instance)

        generate_calls = []

        def fake_generate_signals(opportunities):
            generate_calls.append(opportunities)
            return len(opportunities)

        monkeypatch.setattr(main_module, "generate_signals", fake_generate_signals)

        task = asyncio.create_task(main_module._scan_and_generate_signals())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert generate_calls, "generate_signals should have been called at least once"
        assert generate_calls[0] == fake_opportunities
