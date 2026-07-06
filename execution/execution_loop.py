"""Execution loop for already-approved paper-trading decisions.

The loop coordinates existing components only:
DecisionEngine decides, TradeEngine creates an execution-ready trade,
and PaperExecutor monitors open paper trades.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Optional, Protocol

from execution.paper_executor import PaperExecutor
from execution.pipeline import TradeCandidate, TradingSignal
from execution.trade_engine import TradeEngine


class SignalSource(Protocol):
    """Callable source that returns the next signal, or None when idle."""

    def __call__(self) -> Optional[TradingSignal]:
        """Return the next signal to evaluate."""


@dataclass(frozen=True)
class ExecutionLoopResult:
    """Outcome of one execution loop cycle."""

    signal: Optional[TradingSignal]
    approved: bool
    trade: Optional[Any]
    monitored_count: int


class ExecutionLoop:
    """Coordinate approved trade creation and paper monitoring."""

    def __init__(
        self,
        pipeline: Optional[Any] = None,
        trade_engine: Optional[TradeEngine] = None,
        paper_executor: Optional[PaperExecutor] = None,
        signal_source: Optional[SignalSource] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create an execution loop with injectable dependencies."""

        self.pipeline = pipeline
        self.trade_engine = trade_engine or TradeEngine()
        self.paper_executor = paper_executor or PaperExecutor()
        self.signal_source = signal_source
        self.logger = logger or logging.getLogger(__name__)

    def run_once(self, signal: Optional[Any] = None) -> ExecutionLoopResult:
        """Run one approved trade execution and paper monitoring cycle."""

        candidate = self._coerce_candidate(signal or self._load_signal())
        if candidate is None:
            self.logger.debug("Execution loop idle: no approved trade candidate available")
            return ExecutionLoopResult(
                signal=None,
                approved=False,
                trade=None,
                monitored_count=0,
            )

        trade = self._create_trade(candidate)
        monitored = self._monitor_open_trades() if trade is not None else []

        return ExecutionLoopResult(
            signal=candidate.signal,
            approved=True,
            trade=trade,
            monitored_count=len(monitored),
        )

    def run(
        self,
        signals: Optional[Iterable[TradingSignal]] = None,
        max_iterations: Optional[int] = None,
        sleep_seconds: float = 0.0,
    ) -> list[ExecutionLoopResult]:
        """Run repeated execution cycles for provided or loaded signals."""

        results: list[ExecutionLoopResult] = []
        iterator = iter(signals) if signals is not None else None
        iterations = 0

        while max_iterations is None or iterations < max_iterations:
            signal = self._next_iterable_signal(iterator)
            result = self.run_once(signal)
            results.append(result)
            iterations += 1

            if self._should_stop(iterator, signal, max_iterations, iterations):
                break
            self._sleep_between_cycles(sleep_seconds)

        return results

    def _load_signal(self) -> Optional[TradingSignal]:
        if self.signal_source is None:
            return None
        return self.signal_source()

    @staticmethod
    def _coerce_candidate(signal_or_candidate: Optional[Any]) -> Optional[TradeCandidate]:
        if signal_or_candidate is None:
            return None

        required_attrs = ("signal", "entry", "scores", "decision")
        if all(hasattr(signal_or_candidate, attr) for attr in required_attrs):
            return signal_or_candidate

        return None

    def _create_trade(self, candidate: TradeCandidate) -> Optional[Any]:
        if not self._trade_signal_is_valid(candidate.signal):
            self.logger.warning("Approved candidate signal missing TradeEngine fields")
            return None

        entry = candidate.entry
        atr = self._score_value(candidate.scores, "atr")

        if entry is None or atr is None:
            self.logger.warning("Approved candidate missing entry or ATR; trade not created")
            return None

        trade = self.trade_engine.create_trade(
            signal=candidate.signal,
            entry=float(entry),
            atr=float(atr),
        )
        if trade is None:
            self.logger.warning("TradeEngine did not create a trade")
        else:
            self.logger.info("Trade created for approved signal")
        return trade

    def _monitor_open_trades(self) -> list[Any]:
        results = self.paper_executor.monitor_open_trades()
        self.logger.info("Monitored %s open paper trades", len(results))
        return results

    @staticmethod
    def _trade_signal_is_valid(signal: TradingSignal) -> bool:
        return all(getattr(signal, field, None) for field in ("id", "symbol", "side"))

    @staticmethod
    def _score_value(scores: Mapping[str, Any], key: str) -> Optional[float]:
        value = scores.get(key)
        if value is None:
            return None
        return float(value)

    @staticmethod
    def _next_iterable_signal(
        iterator: Optional[Iterable[TradingSignal]],
    ) -> Optional[TradingSignal]:
        if iterator is None:
            return None
        try:
            return next(iterator)  # type: ignore[arg-type]
        except StopIteration:
            return None

    @staticmethod
    def _should_stop(
        iterator: Optional[Iterable[TradingSignal]],
        signal: Optional[TradingSignal],
        max_iterations: Optional[int],
        iterations: int,
    ) -> bool:
        if max_iterations is not None and iterations >= max_iterations:
            return True
        return iterator is not None and signal is None

    @staticmethod
    def _sleep_between_cycles(sleep_seconds: float) -> None:
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
