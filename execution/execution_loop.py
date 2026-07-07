"""Execution loop orchestration for paper trading.

This module wires existing components together only. Decisions stay in
``DecisionPipeline``, trade persistence stays in ``TradeEngine``, and open
paper trade monitoring stays in ``PaperExecutor``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from database import update_signal_status
from execution.paper_executor import PaperExecutor, TradeMonitorResult
from execution.pipeline import DecisionPipeline, TradeCandidate, TradingSignal
from execution.trade_engine import TradeEngine


@dataclass(frozen=True)
class ExecutionLoopResult:
    """Summary of one batch execution loop pass."""

    processed: int
    created: int
    trades: list[Any]
    monitor_results: list[TradeMonitorResult]


class ExecutionLoop:
    """Orchestrate signal evaluation, trade creation, and paper monitoring."""

    def __init__(
        self,
        pipeline: Optional[DecisionPipeline] = None,
        trade_engine: Optional[TradeEngine] = None,
        paper_executor: Optional[PaperExecutor] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.pipeline = pipeline or DecisionPipeline()
        self.trade_engine = trade_engine or TradeEngine()
        self.paper_executor = paper_executor or PaperExecutor()
        self.logger = logger or logging.getLogger(__name__)

    def run_once(self, signals: Iterable[TradingSignal]) -> ExecutionLoopResult:
        """Process a batch of signals and monitor open paper trades once."""

        processed = 0
        trades: list[Any] = []

        for signal in signals:
            processed += 1
            trade = self.process_signal(signal)
            if trade is not None:
                trades.append(trade)

        monitor_results = self.monitor()
        return ExecutionLoopResult(
            processed=processed,
            created=len(trades),
            trades=trades,
            monitor_results=monitor_results,
        )

    def process_signal(self, signal: TradingSignal) -> Optional[Any]:
        """Evaluate one signal and create a trade only when approved."""

        candidate = self.pipeline.evaluate(signal)
        if candidate is None:
            self.logger.info(
                "Signal rejected by decision pipeline: %s %s",
                getattr(signal, "symbol", None),
                getattr(signal, "side", None),
            )
            update_signal_status(signal.id, "REJECTED")
            return None

        self.logger.info(
            "Signal approved by decision pipeline: %s %s %s",
            candidate.symbol,
            candidate.side,
            candidate.decision,
        )
        trade = self._create_trade(candidate)
        if trade is not None:
            update_signal_status(signal.id, "EXECUTED")
        else:
            update_signal_status(signal.id, "OPEN")
        return trade

    def monitor(self) -> list[TradeMonitorResult]:
        """Monitor all open paper trades."""

        results = self.paper_executor.monitor_open_trades()
        self.logger.info("Monitored %s open paper trades", len(results))
        return results

    def _create_trade(self, candidate: TradeCandidate) -> Optional[Any]:
        entry = candidate.entry
        atr = candidate.scores.get("atr")

        if entry is None or atr is None:
            self.logger.warning(
                "Approved candidate missing entry or ATR; trade not created: %s %s",
                candidate.symbol,
                candidate.side,
            )
            return None

        trade = self.trade_engine.create_trade(
            signal=candidate.signal,
            entry=float(entry),
            atr=float(atr),
        )

        if trade is None:
            self.logger.warning(
                "TradeEngine did not create a trade: %s %s",
                candidate.symbol,
                candidate.side,
            )
        else:
            self.logger.info("Trade created: %s %s", candidate.symbol, candidate.side)

        return trade
