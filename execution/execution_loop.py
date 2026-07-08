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
from position_sizing import PositionSizingEngine
from risk_manager import RiskManager
from scoring.signal_ranking_ai import SignalRankingAI


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
        risk_manager: Optional[RiskManager] = None,
        position_sizer: Optional[PositionSizingEngine] = None,
        logger: Optional[logging.Logger] = None,
        signal_ranker: Optional[SignalRankingAI] = None,
    ) -> None:
        self.pipeline = pipeline or DecisionPipeline()
        self.trade_engine = trade_engine or TradeEngine()
        self.paper_executor = paper_executor or PaperExecutor()
        self.risk_manager = risk_manager or RiskManager()
        self.position_sizer = position_sizer or PositionSizingEngine()
        self.logger = logger or logging.getLogger(__name__)
        self.signal_ranker = signal_ranker

    def run_once(self, signals: Iterable[TradingSignal]) -> ExecutionLoopResult:
        """Process a batch of signals and monitor open paper trades once."""

        signal_list = list(signals)

        self.logger.info(
            "ExecutionLoop run_once: %s signals received",
            len(signal_list),
        )
        if signal_list:
            self.logger.debug(
                "Signal IDs: %s",
                [getattr(s, "id", None) for s in signal_list],
            )

        if self.signal_ranker is not None:
            try:
                signal_dicts = [
                    {
                        "id": getattr(s, "id", None),
                        "symbol": getattr(s, "symbol", ""),
                        "side": getattr(s, "side", ""),
                        "timeframe": getattr(s, "timeframe", ""),
                    }
                    for s in signal_list
                ]
                ranked = self.signal_ranker.rank_signals(signal_dicts)
                rank_map = {r.identifier: r for r in ranked}
                signal_list.sort(
                    key=lambda s: rank_map.get(str(getattr(s, "id", None)), type("", (), {"composite_score": 0})()).composite_score,
                    reverse=True,
                )
                self.logger.info(
                    "Signals ranked by SignalRankingAI: %s",
                    [(r.identifier, r.composite_score, r.recommendation) for r in ranked],
                )
            except Exception as exc:
                self.logger.exception("SignalRankingAI failed (%s); processing without ranking", exc)

        processed = 0
        trades: list[Any] = []

        for signal in signal_list:
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

        if signal is None:
            self.logger.warning("Received None signal in process_signal")
            return None

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

        intelligence = {
            "confidence": candidate.confidence,
            "decision": candidate.decision,
            **candidate.scores,
        }

        if candidate.regime_context is not None:
            intelligence["regime_context"] = candidate.regime_context

        if candidate.memory_context is not None:
            intelligence["memory_context"] = candidate.memory_context

        trade = self.trade_engine.create_trade(
            signal=candidate.signal,
            entry=float(entry),
            atr=float(atr),
            intelligence=intelligence,
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
