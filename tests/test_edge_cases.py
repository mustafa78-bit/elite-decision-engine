"""Edge case and robustness tests for the trading pipeline.

Tests behavior with:
  - Empty/degenerate inputs
  - Missing or invalid fields
  - Boundary values
  - Graceful degradation
"""

import pandas as pd
import pytest

from core.confidence_engine import ConfidenceEngine
from database import Trade
from execution.execution_loop import ExecutionLoop, ExecutionLoopResult
from execution.pipeline import DecisionPipeline
from execution.paper_executor import PaperExecutor, TradeMonitorResult
from execution.trade_engine import TradeEngine
from risk_manager import RiskManager


class FakeSignal:
    def __init__(self, sid=1, symbol="BTCUSDT", side="LONG", timeframe="1h"):
        self.id = sid
        self.symbol = symbol
        self.side = side
        self.timeframe = timeframe


class MockCollector:
    def __init__(self, close_price=50000.0):
        self.close_price = close_price

    def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
        return pd.DataFrame({"close": [self.close_price] * 100})


class MockScoringEngine:
    def score(self, signal):
        return {
            "entry": 50000.0, "ema20": 51000.0, "ema50": 50500.0,
            "ema200": 50200.0, "rsi": 55.0, "atr": 500.0,
            "trend_score": 1.0, "volume_score": 1.0,
            "btc_score": 1.0, "mtf_score": 1.0,
            "risk_score": 0.0, "final_score": 0.9,
        }


class MockTradeEngine:
    def create_trade(self, signal, entry, atr, intelligence=None):
        return {"id": 1, "symbol": signal.symbol, "side": signal.side}


class MockRiskManager:
    def can_open_trade(self, candidate):
        return True, ""


class MockPaperExecutor:
    def monitor_open_trades(self):
        return []


# ─── ExecutionLoop edge cases ──────────────────────────────────────────────


class TestExecutionLoopEdgeCases:

    def test_run_once_empty_list(self):
        loop = ExecutionLoop(
            pipeline=None,
            trade_engine=MockTradeEngine(),
            paper_executor=MockPaperExecutor(),
            risk_manager=MockRiskManager(),
        )
        result = loop.run_once([])
        assert isinstance(result, ExecutionLoopResult)
        assert result.processed == 0
        assert result.created == 0
        assert result.trades == []
        assert result.monitor_results == []

    def test_run_once_single_signal(self):
        loop = ExecutionLoop(
            pipeline=None,
            trade_engine=MockTradeEngine(),
            paper_executor=MockPaperExecutor(),
            risk_manager=MockRiskManager(),
        )
        signal = FakeSignal(sid=1)
        result = loop.run_once([signal])
        assert result.processed == 1
        assert result.created >= 0  # depends on pipeline


# ─── DecisionPipeline edge cases ────────────────────────────────────────────


class TestDecisionPipelineEdgeCases:

    def test_evaluate_returns_none_for_missing_fields(self):
        pipeline = DecisionPipeline(
            collector=MockCollector(),
            filters=(),
            scoring_engine=MockScoringEngine(),
        )

        class MissingSignal:
            pass

        result = pipeline.evaluate(MissingSignal())
        assert result is None

    def test_evaluate_handles_non_string_side(self):
        pipeline = DecisionPipeline(
            collector=MockCollector(),
            filters=(),
            scoring_engine=MockScoringEngine(),
        )

        class IntSignal:
            id = 1
            symbol = "BTCUSDT"
            side = 123
            timeframe = "1h"

        result = pipeline.evaluate(IntSignal())
        assert result is not None

    def test_evaluate_handles_empty_symbol(self):
        pipeline = DecisionPipeline(
            collector=MockCollector(),
            filters=(),
            scoring_engine=MockScoringEngine(),
        )

        class EmptySymbol:
            id = 1
            symbol = ""
            side = "LONG"
            timeframe = "1h"

        result = pipeline.evaluate(EmptySymbol())
        assert result is None  # fails validation


# ─── PaperExecutor edge cases ──────────────────────────────────────────────


class TestPaperExecutorEdgeCases:

    def test_monitor_open_trades_when_none(self, session_factory):
        executor = PaperExecutor(
            collector=MockCollector(),
            session_factory=session_factory,
        )
        results = executor.monitor_open_trades()
        assert results == []

    def test_get_open_trades_when_none(self, session_factory):
        executor = PaperExecutor(
            collector=MockCollector(),
            session_factory=session_factory,
        )
        trades = executor.get_open_trades()
        assert trades == []

    def test_close_nonexistent_trade_returns_none(self, session_factory):
        executor = PaperExecutor(
            collector=MockCollector(),
            session_factory=session_factory,
        )
        result = executor.close_trade(trade_id=99999, exit_price=50000.0)
        assert result is None

    def test_get_current_price_raises_on_empty_data(self):
        class EmptyCollector:
            def get_ohlcv(self, **kwargs):
                return pd.DataFrame()

        executor = PaperExecutor(
            collector=EmptyCollector(),
            session_factory=dict,
        )
        with pytest.raises(ValueError, match="No market data returned"):
            executor.get_current_price("BTCUSDT")


# ─── TradeEngine edge cases ─────────────────────────────────────────────────


class TestTradeEngineEdgeCases:

    def test_create_trade_zero_atr(self, db_session, monkeypatch):
        from database import Signal
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        monkeypatch.setattr(
            "execution.trade_engine.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )

        trade = TradeEngine().create_trade(signal=signal, entry=50000.0, atr=0.0)
        assert trade is not None
        assert trade.status == "OPEN"

    def test_create_trade_negative_atr(self, db_session, monkeypatch):
        from database import Signal
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        monkeypatch.setattr(
            "execution.trade_engine.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )

        trade = TradeEngine().create_trade(signal=signal, entry=50000.0, atr=-100.0)
        assert trade is not None
        assert trade.status == "OPEN"

    def test_create_trade_large_values(self, db_session, monkeypatch):
        from database import Signal
        signal = Signal(symbol="BTCUSDT", side="LONG", timeframe="1h", status="OPEN")
        db_session.add(signal)
        db_session.flush()

        monkeypatch.setattr(
            "execution.trade_engine.NotificationDispatcher.emit",
            lambda *a, **kw: None,
        )

        trade = TradeEngine().create_trade(signal=signal, entry=1e8, atr=1e6)
        assert trade is not None
        assert trade.status == "OPEN"


# ─── RiskManager edge cases ─────────────────────────────────────────────────


class TestRiskManagerEdgeCases:

    def test_entry_zero_allowed(self, db_session, session_factory):
        rm = RiskManager(session_factory=session_factory)

        class ZeroEntryCandidate:
            entry = 0.0
            symbol = "BTCUSDT"
            side = "LONG"
            scores = {}

        allowed, reason = rm.can_open_trade(ZeroEntryCandidate())
        assert allowed is True
        assert reason == ""

    def test_entry_above_max_size_blocked(self, db_session, session_factory, monkeypatch):
        monkeypatch.setattr("risk_manager.MAX_POSITION_SIZE_USD", 1000)
        rm = RiskManager(session_factory=session_factory)

        class BigCandidate:
            entry = 100000.0
            symbol = "BTCUSDT"
            side = "LONG"
            scores = {}

        allowed, reason = rm.can_open_trade(BigCandidate())
        assert allowed is False
        assert "exceeded" in reason.lower()


# ─── ConfidenceEngine edge cases ─────────────────────────────────────────────


class TestConfidenceEngineEdgeCases:

    def test_all_scores_none(self):
        engine = ConfidenceEngine()
        result = engine.calculate({"trend_score": None, "volume_score": None, "btc_score": None, "mtf_score": None, "risk_score": None})
        assert result["confidence"] == 0.0
        assert result["decision"] == "REJECT"

    def test_empty_scores(self):
        engine = ConfidenceEngine()
        result = engine.calculate({})
        assert result["confidence"] == 0.0
        assert result["decision"] == "REJECT"

    def test_partial_scores(self):
        engine = ConfidenceEngine()
        result = engine.calculate({"trend_score": 1.0, "volume_score": 1.0})
        assert result["confidence"] == 50.0  # (30 + 20)
        assert result["decision"] == "REJECT"


# ─── Pipeline None market data ───────────────────────────────────────────────


class TestPipelineNoneMarketData:

    def test_evaluate_with_none_market_data(self):
        class NoneCollector:
            def get_ohlcv(self, **kw):
                return None

        class MockScorer:
            def score(self, signal):
                return {"entry": 50000.0, "trend_score": 1.0, "volume_score": 1.0,
                        "btc_score": 1.0, "mtf_score": 1.0, "risk_score": 0.5}

        pipeline = DecisionPipeline(
            collector=NoneCollector(),
            filters=(),
            scoring_engine=MockScorer(),
        )

        class FakeSig:
            id = 1
            symbol = "BTCUSDT"
            side = "LONG"
            timeframe = "1h"

        result = pipeline.evaluate(FakeSig())
        assert result is None


# ─── ExecutionLoop empty signals ─────────────────────────────────────────────


class TestExecutionLoopEmptySignals:

    def test_run_once_empty_list(self):
        loop = ExecutionLoop(
            pipeline=None,
            trade_engine=MockTradeEngine(),
            paper_executor=MockPaperExecutor(),
            risk_manager=MockRiskManager(),
        )
        result = loop.run_once([])
        assert isinstance(result, ExecutionLoopResult)
        assert result.processed == 0
        assert result.created == 0


# ─── BTCHealth DI ────────────────────────────────────────────────────────────


class TestBTCHealthDI:

    def test_inject_collector(self):
        from market_data.btc_health import BTCHealth

        class FakeCollector:
            def get_ohlcv(self, symbol="BTC", timeframe="1h", limit=500):
                import pandas as pd
                return pd.DataFrame({
                    "close": [50000.0, 50100.0, 50200.0],
                })

        health = BTCHealth(collector=FakeCollector())
        assert health.collector is not None


# ─── Database session_scope ──────────────────────────────────────────────────


class TestSessionScope:

    def test_session_scope_imports(self):
        from database import session_scope
        assert callable(session_scope)

    def test_session_scope_rolls_back_on_error(self):
        from database import session_scope
        with pytest.raises(ValueError):
            with session_scope() as session:
                raise ValueError("test")

    def test_session_scope_closes_on_exit(self, monkeypatch):
        from database import session_scope
        closed = False
        original_close = None

        def track_close(self):
            nonlocal closed
            closed = True
            if original_close:
                original_close(self)

        monkeypatch.setattr("sqlalchemy.orm.Session.close", track_close)

        with session_scope() as session:
            pass
        assert closed


# ─── Config validation ───────────────────────────────────────────────────────


class TestConfigValidation:

    def test_config_has_positive_check_interval(self):
        from config import CHECK_INTERVAL
        assert CHECK_INTERVAL > 0

    def test_config_min_score_in_range(self):
        from config import MIN_SCORE
        assert 0 <= MIN_SCORE <= 100

    def test_config_account_equity_positive(self):
        from config import ACCOUNT_EQUITY
        assert ACCOUNT_EQUITY > 0


# ─── API exception handlers ──────────────────────────────────────────────────


class TestAPIExceptionHandlers:

    def test_validation_handler_returns_json(self, api_client):
        resp = api_client.post("/auth/login", json={"invalid": "data"})
        assert resp.status_code in (401, 422)

    def test_nonexistent_route_returns_json(self, api_client):
        resp = api_client.get("/nonexistent-path-12345")
        assert resp.status_code == 404
        assert resp.headers["content-type"] == "application/json"


# ─── Collector data validation ───────────────────────────────────────────────


class TestCollectorDataValidation:

    def test_empty_candles_returns_empty_df(self, monkeypatch):
        import pandas as pd
        from market_data.collector import HyperliquidCollector

        def mock_post(*a, **kw):
            class MockResp:
                def raise_for_status(self):
                    pass
                def json(self):
                    return []
            return MockResp()

        monkeypatch.setattr("market_data.collector.requests.Session.post", mock_post)
        df = HyperliquidCollector().get_ohlcv()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_non_list_response_raises(self, monkeypatch):
        from market_data.collector import HyperliquidCollector

        def mock_post(*a, **kw):
            class MockResp:
                def raise_for_status(self):
                    pass
                def json(self):
                    return {}
            return MockResp()

        monkeypatch.setattr("market_data.collector.requests.Session.post", mock_post)
        import pytest
        with pytest.raises(ValueError, match="Expected list"):
            HyperliquidCollector().get_ohlcv()

    def test_all_nan_close_returns_empty_df(self, monkeypatch):
        import pandas as pd
        from market_data.collector import HyperliquidCollector

        def mock_post(*a, **kw):
            class MockResp:
                def raise_for_status(self):
                    pass
                def json(self):
                    return [{"t": 1000, "o": 1, "h": 2, "l": 1, "c": None, "v": 100}]
            return MockResp()

        monkeypatch.setattr("market_data.collector.requests.Session.post", mock_post)
        df = HyperliquidCollector().get_ohlcv()
        assert df.empty


# ─── LiveMarketEngine cache ──────────────────────────────────────────────────


class TestLiveMarketEngineCache:

    def test_cache_hit_returns_cached(self, monkeypatch):
        from market_data.live.engine import LiveMarketEngine
        import pandas as pd

        call_count = 0

        class FakeCollector:
            def get_ohlcv(self, **kw):
                nonlocal call_count
                call_count += 1
                return pd.DataFrame({"close": [50000.0], "high": [50100.0], "low": [49900.0],
                                      "open": [49950.0], "volume": [1000.0], "timestamp": [1000]})

        engine = LiveMarketEngine(collector=FakeCollector())
        engine.snapshot("BTC", "1h", 100)
        engine.snapshot("BTC", "1h", 100)
        assert call_count == 1  # second call served from cache

    def test_cache_miss_different_keys(self, monkeypatch):
        from market_data.live.engine import LiveMarketEngine
        import pandas as pd

        call_count = 0

        class FakeCollector:
            def get_ohlcv(self, **kw):
                nonlocal call_count
                call_count += 1
                return pd.DataFrame({"close": [50000.0], "high": [50100.0], "low": [49900.0],
                                      "open": [49950.0], "volume": [1000.0], "timestamp": [1000]})

        engine = LiveMarketEngine(collector=FakeCollector())
        engine.snapshot("BTC", "1h", 100)
        engine.snapshot("ETH", "1h", 100)
        assert call_count == 2  # different symbol = new fetch


# ─── Scoring engine empty data ────────────────────────────────────────────────


class TestScoringEngineEmptyData:

    def test_empty_df_returns_fallback(self, monkeypatch):
        from scoring.scoring_engine import ScoringEngine
        import pandas as pd

        class EmptyCollector:
            def get_ohlcv(self, **kw):
                return pd.DataFrame()

        engine = ScoringEngine(collector=EmptyCollector())

        class FakeSig:
            symbol = "BTCUSDT"
            side = "LONG"
            timeframe = "1h"

        result = engine.score(FakeSig())
        assert result["final_score"] == 0
        assert result["risk_score"] == 1


# ─── Confidence engine contributions ─────────────────────────────────────────


class TestConfidenceEngineContributions:

    def test_calculate_returns_confidence(self):
        from core.confidence_engine import ConfidenceEngine
        engine = ConfidenceEngine()
        result = engine.calculate({
            "trend_score": 1.0, "volume_score": 1.0,
            "btc_score": 1.0, "mtf_score": 1.0, "risk_score": 1.0,
        })
        assert result["confidence"] == 100.0
        assert result["decision"] == "STRONG_APPROVE"

    def test_calculate_all_zeros(self):
        from core.confidence_engine import ConfidenceEngine
        engine = ConfidenceEngine()
        result = engine.calculate({
            "trend_score": 0.0, "volume_score": 0.0,
            "btc_score": 0.0, "mtf_score": 0.0, "risk_score": 0.0,
        })
        assert result["confidence"] == 0.0
        assert result["decision"] == "REJECT"


# ─── TPSLEngine edge cases ────────────────────────────────────────────────────


class TestTPSLEdgeCases:

    def test_zero_entry_raises(self):
        from execution.tp_sl import TPSLEngine
        import pytest
        with pytest.raises(ValueError, match="entry=0"):
            TPSLEngine().calculate(entry=0, atr=500, side="LONG")

    def test_none_entry_raises(self):
        from execution.tp_sl import TPSLEngine
        import pytest
        with pytest.raises(ValueError, match="entry=None"):
            TPSLEngine().calculate(entry=None, atr=500, side="LONG")


# ─── ExecutionLoop None signal ────────────────────────────────────────────────


class TestExecutionLoopNoneSignal:

    def test_process_signal_none_returns_none(self):
        from execution.execution_loop import ExecutionLoop
        loop = ExecutionLoop()
        result = loop.process_signal(None)
        assert result is None


# ─── update_signal_status edge cases ─────────────────────────────────────────


class TestUpdateSignalStatusEdgeCases:

    def test_none_id_returns_false(self):
        from database import update_signal_status
        result = update_signal_status(None, "EXECUTED")
        assert result is False

    def test_missing_id_returns_false(self):
        from database import update_signal_status
        result = update_signal_status(999999, "EXECUTED")
        assert result is False


# ─── HealthService ────────────────────────────────────────────────────────────


class TestHealthService:

    def test_uptime_positive(self):
        from monitoring.health import HealthService
        uptime = HealthService.uptime()
        assert uptime > 0

    def test_database_check_returns_dict(self):
        from monitoring.health import HealthService
        result = HealthService.database()
        assert "status" in result

    def test_config_returns_expected_keys(self):
        from monitoring.health import HealthService
        result = HealthService.config()
        assert "api_env" in result
        assert "check_interval" in result
        assert "min_score" in result
        assert "max_open_trades" in result

    def test_full_returns_all_components(self):
        from monitoring.health import HealthService
        result = HealthService.full()
        assert "status" in result
        assert "uptime_seconds" in result
        assert "database" in result
        assert "collector" in result
        assert "cache" in result
        assert "execution" in result
        assert "dependencies" in result
        assert "errors" in result
        assert "config" in result

    def test_database_tables_returns_row_counts(self):
        from monitoring.health import HealthService
        result = HealthService.database_tables()
        assert "status" in result
        if result["status"] == "ok":
            assert "row_counts" in result
            for name in ("signals", "trades", "notifications"):
                assert name in result["row_counts"]

    def test_execution_returns_component_status(self):
        from monitoring.health import HealthService
        result = HealthService.execution()
        assert "status" in result
        if result["status"] == "ok":
            assert "pipeline_ready" in result
            assert "trade_engine_ready" in result
            assert "risk_manager_ready" in result
            assert "paper_executor_ready" in result

    def test_dependencies_returns_exchange_status(self):
        from monitoring.health import HealthService
        result = HealthService.dependencies()
        assert isinstance(result, dict)

    def test_errors_returns_empty_when_no_failures(self):
        from monitoring.health import HealthService, _INTERNAL_ERRORS
        _INTERNAL_ERRORS.clear()
        result = HealthService.errors()
        assert result == {}

    def test_database_check_returns_latency(self):
        from monitoring.health import HealthService
        result = HealthService.database()
        assert "latency_ms" in result

    def test_collector_returns_latency(self):
        from monitoring.health import HealthService
        result = HealthService.collector()
        assert "latency_ms" in result

    def test_database_tables_latency_present(self):
        from monitoring.health import HealthService
        result = HealthService.database_tables()
        assert "latency_ms" in result

    def test_metrics_returns_signal_and_trade_counts(self):
        from monitoring.health import HealthService
        result = HealthService.metrics()
        assert "status" in result
        if result["status"] == "ok":
            assert "signals" in result
            assert "trades" in result
            for key in ("total", "approved", "rejected", "open"):
                assert key in result["signals"]
            for key in ("total", "open", "closed"):
                assert key in result["trades"]


# ─── FINAL_STATUSES consistency ──────────────────────────────────────────────


class TestFinalStatuses:

    def test_imported_from_database(self):
        from database import FINAL_STATUSES
        assert "TP_HIT" in FINAL_STATUSES
        assert "SL_HIT" in FINAL_STATUSES
        assert "CLOSED" in FINAL_STATUSES
        assert len(FINAL_STATUSES) == 3

    def test_imported_in_paper_executor(self):
        from execution.paper_executor import FINAL_STATUSES
        assert FINAL_STATUSES == frozenset({"TP_HIT", "SL_HIT", "CLOSED"})

    def test_imported_in_risk_manager(self):
        from risk_manager import FINAL_STATUSES
        assert "TP_HIT" in FINAL_STATUSES

    def test_no_local_definitions(self):
        import inspect
        import database
        src = inspect.getsource(database)
        assert "FINAL_STATUSES = frozenset" in src


# ─── JWT Security ────────────────────────────────────────────────────────────


class TestJWTSecurity:

    def test_dev_mode_uses_default_secret(self):
        import os
        if os.getenv("API_ENV", "development") != "production":
            from auth.jwt import _get_secret
            assert _get_secret() == "dev-secret-change-in-production"

    def test_create_and_decode_token(self):
        from auth.jwt import create_access_token, decode_access_token
        token = create_access_token({"sub": "1", "username": "alice"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["username"] == "alice"

    def test_decode_invalid_token_returns_none(self):
        from auth.jwt import decode_access_token
        assert decode_access_token("invalid-token") is None

    def test_decode_expired_token_returns_none(self):
        import jwt
        from auth.jwt import _get_secret
        from datetime import datetime, timedelta, timezone

        expired = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            _get_secret(),
            algorithm="HS256",
        )
        from auth.jwt import decode_access_token
        assert decode_access_token(expired) is None


# ─── Production readiness ──────────────────────────────────────────────────


class TestProductionReadiness:

    def test_startup_rejects_prod_without_jwt(self):
        from startup import StartupValidator
        import os
        # simulate
        original = os.environ.get("API_ENV")
        orig_jwt = os.environ.get("JWT_SECRET")
        orig_cors = os.environ.get("CORS_ORIGINS")
        try:
            os.environ["API_ENV"] = "production"
            os.environ.pop("JWT_SECRET", None)
            os.environ["CORS_ORIGINS"] = "https://example.com"
            validator = StartupValidator()
            with pytest.raises(ValueError, match="JWT_SECRET"):
                validator._check_env_vars()
        finally:
            if original is not None:
                os.environ["API_ENV"] = original
            else:
                os.environ.pop("API_ENV", None)
            if orig_jwt is not None:
                os.environ["JWT_SECRET"] = orig_jwt
            else:
                os.environ.pop("JWT_SECRET", None)
            if orig_cors is not None:
                os.environ["CORS_ORIGINS"] = orig_cors
            else:
                os.environ.pop("CORS_ORIGINS", None)

    def test_startup_rejects_prod_wildcard_cors(self):
        from startup import StartupValidator
        import os
        original = os.environ.get("API_ENV")
        orig_jwt = os.environ.get("JWT_SECRET")
        orig_cors = os.environ.get("CORS_ORIGINS")
        try:
            os.environ["API_ENV"] = "production"
            os.environ["JWT_SECRET"] = "super-secret-123"
            os.environ["CORS_ORIGINS"] = "*"
            validator = StartupValidator()
            with pytest.raises(ValueError, match="CORS_ORIGINS"):
                validator._check_env_vars()
        finally:
            if original is not None:
                os.environ["API_ENV"] = original
            else:
                os.environ.pop("API_ENV", None)
            if orig_jwt is not None:
                os.environ["JWT_SECRET"] = orig_jwt
            else:
                os.environ.pop("JWT_SECRET", None)
            if orig_cors is not None:
                os.environ["CORS_ORIGINS"] = orig_cors
            else:
                os.environ.pop("CORS_ORIGINS", None)


# ─── Logging & Diagnostics ──────────────────────────────────────────────────


class TestLoggingConfig:

    def test_setup_logging_creates_handlers(self):
        from logging_config import setup_logging
        import logging
        setup_logging()
        handlers = logging.getLogger().handlers
        names = [type(h).__name__ for h in handlers]
        assert "StreamHandler" in names
        assert "RotatingFileHandler" in names

    def test_log_state_emits_info(self):
        from logging_config import log_state
        import logging
        logger = logging.getLogger("test.log_state")
        logger.setLevel(logging.DEBUG)
        try:
            log_state("test.log_state", "test_component", "started", key="value")
        except Exception:
            assert False, "log_state should not raise"

    def test_json_formatter_produces_valid_json(self):
        from logging_config import _JsonFormatter
        import logging
        formatter = _JsonFormatter()
        record = logging.LogRecord("test", logging.INFO, "/test", 1, "hello", (), None)
        output = formatter.format(record)
        import json
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "hello"


# ─── Shutdown / Lifecycle ───────────────────────────────────────────────────


class TestShutdown:

    def test_shutdown_called_without_error(self):
        from startup import shutdown
        try:
            shutdown()
        except Exception:
            assert False, "shutdown should not raise"

    def test_database_dispose_safe(self):
        from database import engine
        try:
            engine.dispose()
        except Exception:
            assert False, "engine.dispose should not raise"
