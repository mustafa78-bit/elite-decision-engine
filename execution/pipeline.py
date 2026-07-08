"""Decision orchestration pipeline for trade candidates.

This module intentionally does not execute orders, persist records, or notify
external services. It only coordinates existing market data, filters, scoring,
and confidence decision components.
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol, Sequence

from core.confidence_engine import ConfidenceEngine
from filters.btc_filter import BTCHealthFilter
from market_data.collector import HyperliquidCollector
from memory.trade_memory import TradeMemory
from scoring.regime_ai import RegimeAI
from scoring.scoring_engine import ScoringEngine


APPROVED_DECISIONS = frozenset({"APPROVE", "STRONG_APPROVE"})


class TradingSignal(Protocol):
    """Minimum signal interface required by the pipeline."""

    id: int
    symbol: str
    side: str
    timeframe: str


class MarketDataCollector(Protocol):
    """Collector interface used to fetch market data for filters."""

    def get_ohlcv(self, symbol: str = "BTC", timeframe: str = "1h", limit: int = 500) -> Any:
        """Return OHLCV market data for the given symbol and timeframe."""


class SignalFilter(Protocol):
    """Filter interface supported by the pipeline."""

    def evaluate(self, data: Any = None) -> Any:
        """Evaluate market data and return a boolean or result mapping."""


class SignalScorer(Protocol):
    """Scoring engine interface used by the pipeline."""

    def score(self, signal: TradingSignal) -> Mapping[str, Any]:
        """Return component scores for the provided signal."""


class ConfidenceCalculator(Protocol):
    """Confidence engine interface used by the pipeline."""

    def calculate(self, score: Mapping[str, Any]) -> Mapping[str, Any]:
        """Return confidence and decision data for component scores."""


@dataclass(frozen=True)
class TradeCandidate:
    """Approved trade candidate produced by the orchestration pipeline."""

    id: int
    symbol: str
    side: str
    timeframe: str
    entry: Optional[float]
    scores: Mapping[str, Any]
    confidence: float
    decision: str
    signal: TradingSignal
    regime_context: Optional[dict[str, Any]] = None
    memory_context: Optional[dict[str, Any]] = None


class DecisionPipeline:
    """Coordinate market data, filters, scoring, and confidence decisions."""

    def __init__(
        self,
        collector: Optional[MarketDataCollector] = None,
        filters: Optional[Sequence[Any]] = None,
        scoring_engine: Optional[SignalScorer] = None,
        confidence_engine: Optional[ConfidenceCalculator] = None,
        logger: Optional[logging.Logger] = None,
        market_data_limit: int = 500,
        regime_ai: Optional[RegimeAI] = None,
        trade_memory: Optional[TradeMemory] = None,
    ) -> None:
        """Initialize the pipeline with injectable dependencies."""

        self.collector = collector or HyperliquidCollector()
        self.filters = tuple(filters) if filters is not None else (BTCHealthFilter(),)
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.confidence_engine = confidence_engine or ConfidenceEngine()
        self.logger = logger or logging.getLogger(__name__)
        self.market_data_limit = market_data_limit
        self.regime_ai = regime_ai
        self.trade_memory = trade_memory

    def evaluate(self, signal: TradingSignal) -> Optional[TradeCandidate]:
        """Return an approved trade candidate for a signal, or ``None``."""

        try:
            self._validate_signal(signal)
            market_data = self._fetch_market_data(signal)

            if self._is_empty_market_data(market_data):
                self.logger.warning("Market data fetch returned no rows for %s", signal.symbol)
                return None

            if not self._passes_filters(market_data):
                self.logger.info("Signal rejected by filters: %s %s", signal.symbol, signal.side)
                return None

            scores = self.scoring_engine.score(signal)
            decision_data = self.confidence_engine.calculate(scores)
            decision = str(decision_data.get("decision", "REJECT"))

            self.logger.info(
                "Pipeline decision for %s %s %s: %s",
                signal.symbol,
                signal.side,
                signal.timeframe,
                decision,
            )

            if decision not in APPROVED_DECISIONS:
                self.logger.info(
                    "Rejected %s %s: decision=%s confidence=%s final_score=%s",
                    signal.symbol, signal.side,
                    decision,
                    decision_data.get("confidence"),
                    scores.get("final_score"),
                )
                return None

            regime_context: Optional[dict[str, Any]] = None
            if self.regime_ai is not None:
                regime_values = {
                    "ema20": scores.get("ema20"),
                    "ema50": scores.get("ema50"),
                    "ema200": scores.get("ema200"),
                    "atr": scores.get("atr"),
                    "close": scores.get("entry"),
                    "rsi": scores.get("rsi"),
                }
                regime_context = self.regime_ai.detect(regime_values)
                self.logger.info(
                    "Regime context for %s: %s",
                    signal.symbol,
                    regime_context.get("regime", "UNKNOWN"),
                )

            memory_context: Optional[dict[str, Any]] = None
            if self.trade_memory is not None:
                recent = self.trade_memory.list(limit=20)
                same_symbol = [
                    e for e in recent
                    if e.symbol == signal.symbol.upper()
                    and e.side == signal.side.upper()
                ]
                if same_symbol:
                    memory_context = {
                        "past_trades": len(same_symbol),
                        "wins": sum(1 for e in same_symbol if e.result == "WIN"),
                        "losses": sum(1 for e in same_symbol if e.result == "LOSS"),
                        "avg_pnl": round(
                            sum(e.pnl for e in same_symbol) / len(same_symbol), 2
                        ),
                    }
                    self.logger.info(
                        "Memory context for %s %s: %s past trades",
                        signal.symbol,
                        signal.side,
                        memory_context["past_trades"],
                    )

            return TradeCandidate(
                id=signal.id,
                symbol=signal.symbol,
                side=signal.side,
                timeframe=signal.timeframe,
                entry=self._optional_float(scores.get("entry")),
                scores=scores,
                confidence=float(decision_data.get("confidence", 0.0)),
                decision=decision,
                signal=signal,
                regime_context=regime_context,
                memory_context=memory_context,
            )

        except Exception as exc:
            self.logger.exception("Decision pipeline failed for signal %r: %s", signal, exc)
            return None

    def run(self, signal: TradingSignal) -> Optional[TradeCandidate]:
        """Backward-friendly alias for ``evaluate``."""

        return self.evaluate(signal)

    def _fetch_market_data(self, signal: TradingSignal) -> Any:
        symbol = signal.symbol.replace("USDT", "")
        self.logger.debug(
            "Fetching market data for %s on %s with limit %s",
            symbol,
            signal.timeframe,
            self.market_data_limit,
        )
        return self.collector.get_ohlcv(
            symbol=symbol,
            timeframe=signal.timeframe,
            limit=self.market_data_limit,
        )

    def _passes_filters(self, market_data: Any) -> bool:
        for signal_filter in self.filters:
            result = self._evaluate_filter(signal_filter, market_data)
            if not self._filter_passed(result):
                self.logger.info(
                    "Filter rejected signal: %s returned %r",
                    signal_filter.__class__.__name__,
                    result,
                )
                return False
        return True

    def _evaluate_filter(self, signal_filter: Any, market_data: Any) -> Any:
        evaluate = getattr(signal_filter, "evaluate", None)
        if callable(evaluate):
            signature = inspect.signature(evaluate)
            if len(signature.parameters) == 0:
                return evaluate()
            return evaluate(market_data)

        is_healthy = getattr(signal_filter, "is_healthy", None)
        if callable(is_healthy):
            return is_healthy()

        raise TypeError(
            f"Filter {signal_filter.__class__.__name__} must define evaluate() or is_healthy()."
        )

    @staticmethod
    def _filter_passed(result: Any) -> bool:
        if isinstance(result, bool):
            return result

        if isinstance(result, Mapping):
            if "ok" in result:
                return bool(result["ok"])
            if "passed" in result:
                return bool(result["passed"])
            if "approved" in result:
                return bool(result["approved"])

        return bool(result)

    @staticmethod
    def _is_empty_market_data(market_data: Any) -> bool:
        empty = getattr(market_data, "empty", None)
        if isinstance(empty, bool):
            return empty
        try:
            return len(market_data) == 0
        except TypeError:
            return market_data is None

    @staticmethod
    def _optional_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        return float(value)

    @staticmethod
    def _validate_signal(signal: TradingSignal) -> None:
        missing = [
            field
            for field in ("id", "symbol", "side", "timeframe")
            if not getattr(signal, field, None)
        ]
        if missing:
            raise ValueError(f"Signal is missing required fields: {', '.join(missing)}")
