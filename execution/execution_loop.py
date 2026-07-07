"""Execution loop orchestration for paper trading.

This module wires existing components together only. Decisions stay in
``DecisionPipeline``, trade persistence stays in ``TradeEngine``, and open
trade monitoring stays in the configured executor (PaperExecutor or
LiveExecutor via ExecutionRouter).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from config import DRY_RUN
from database import update_signal_status
from execution.paper_executor import PaperExecutor, TradeMonitorResult
from execution.pipeline import DecisionPipeline, TradeCandidate, TradingSignal
from execution.router import ExecutionRouter, TradingMode
from execution.trade_engine import TradeEngine
from position_sizing import PositionSizingEngine
from risk_manager import RiskManager


@dataclass(frozen=True)
class ExecutionLoopResult:
    """Summary of one batch execution loop pass."""

    processed: int
    created: int
    trades: list[Any]
    monitor_results: list[TradeMonitorResult]


def _is_success(result: Any) -> bool:
    """Check if an execution result indicates a successful trade."""
    if result is None:
        return False
    if hasattr(result, "accepted"):
        return bool(result.accepted)
    return True


class ExecutionLoop:
    """Orchestrate signal evaluation, trade creation, and trade monitoring."""

    def __init__(
        self,
        pipeline: Optional[DecisionPipeline] = None,
        trade_engine: Optional[TradeEngine] = None,
        paper_executor: Optional[PaperExecutor] = None,
        risk_manager: Optional[RiskManager] = None,
        position_sizer: Optional[PositionSizingEngine] = None,
        execution_router: Optional[ExecutionRouter] = None,
        dry_run: Optional[bool] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.pipeline = pipeline or DecisionPipeline()
        self.trade_engine = trade_engine or TradeEngine()
        self.paper_executor = paper_executor or PaperExecutor()
        self.risk_manager = risk_manager or RiskManager()
        self.position_sizer = position_sizer or PositionSizingEngine()
        self.execution_router = execution_router
        self.dry_run = DRY_RUN if dry_run is None else dry_run
        self.logger = logger or logging.getLogger(__name__)

    def run_once(self, signals: Iterable[TradingSignal]) -> ExecutionLoopResult:
        """Process a batch of signals and monitor open trades once."""

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

        allowed, reason = self.risk_manager.can_open_trade(candidate)
        if not allowed:
            self.logger.warning(
                "Trade rejected by risk manager: %s %s - %s",
                candidate.symbol,
                candidate.side,
                reason,
            )
            update_signal_status(candidate.signal.id, "REJECTED")
            return None

        position_size = self.position_sizer.calculate(candidate)
        self.logger.info(
            "Position sized for %s %s: qty=%s notional=%s risk=%s",
            candidate.symbol,
            candidate.side,
            position_size.quantity,
            position_size.notional_value,
            position_size.risk_amount,
        )

        trade = self._execute(candidate, position_size)
        if trade is not None:
            update_signal_status(signal.id, "EXECUTED")
        else:
            update_signal_status(signal.id, "OPEN")
        return trade

    def monitor(self) -> list[TradeMonitorResult]:
        """Monitor all open trades."""

        if self.execution_router is not None:
            results = self.execution_router.monitor_open_trades()
            self.logger.info("Monitored %s open trades", len(results))
            return results

        results = self.paper_executor.monitor_open_trades()
        self.logger.info("Monitored %s open paper trades", len(results))
        return results

    def _execute(self, candidate: TradeCandidate, size: Any) -> Optional[Any]:
        if self.execution_router is not None:
            if self.execution_router.mode == TradingMode.LIVE and self.dry_run:
                return self._dry_run(candidate, size)
            result = self.execution_router.execute(candidate, size)
            accepted = _is_success(result)
            if accepted:
                self.logger.info(
                    "Trade executed: %s %s via router (mode=%s)",
                    candidate.symbol,
                    candidate.side,
                    self.execution_router.mode.value,
                )
            else:
                self.logger.warning(
                    "Trade rejected by executor: %s %s",
                    candidate.symbol,
                    candidate.side,
                )
            return result if accepted else None

        return self._create_trade(candidate)

    def _dry_run(self, candidate: TradeCandidate, size: Any) -> None:
        self.logger.info(
            "DRY RUN: preparing order for %s %s (submitted=False)",
            candidate.symbol, candidate.side,
        )

        result = self.execution_router.prepare_order(candidate, size)

        log_entry = {
            "event": "dry_run",
            "symbol": candidate.symbol,
            "side": candidate.side,
            "quantity": getattr(size, "quantity", 0.0),
            "price": candidate.entry,
            "client_order_id": "",
            "validation_result": result.get("validated", False),
            "signature_present": result.get("signed", False),
            "submitted": False,
        }
        self.logger.info("DRY RUN result: %s", json.dumps(log_entry))
        return None

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
