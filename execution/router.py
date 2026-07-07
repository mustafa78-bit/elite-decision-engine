"""Execution routing layer — dispatches to PaperExecutor or LiveExecutor.

Usage:
    router = ExecutionRouter(mode=TradingMode.PAPER)
    result = router.execute(candidate, size)
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Callable, Optional

from execution.paper_executor import PaperExecutor
from execution.tp_sl import TPSLEngine


class TradingMode(Enum):
    PAPER = "PAPER"
    LIVE = "LIVE"


class ExecutionRouter:
    """Unified execution interface routing to PAPER or LIVE executor."""

    def __init__(
        self,
        paper_executor: Optional[PaperExecutor] = None,
        live_executor: Optional[Any] = None,
        session_factory: Optional[Callable[[], Any]] = None,
        mode: TradingMode = TradingMode.PAPER,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if paper_executor is not None:
            self.paper_executor = paper_executor
        elif session_factory is not None:
            self.paper_executor = PaperExecutor(session_factory=session_factory)
        else:
            self.paper_executor = PaperExecutor()
        self.live_executor = live_executor
        self.mode = mode
        self.logger = logger or logging.getLogger(__name__)
        self._tp_sl = TPSLEngine()

    def execute(self, candidate: Any, size: Any) -> Any:
        """Execute a trade — routes to PAPER or LIVE executor."""
        if self.mode == TradingMode.LIVE:
            if self.live_executor is None:
                raise RuntimeError("LiveExecutor not configured but mode is LIVE")
            return self.live_executor.execute(candidate, size)
        return self._paper_execute(candidate, size)

    def monitor_open_trades(self) -> list:
        """Monitor open trades — routes to PAPER or LIVE executor."""
        if self.mode == TradingMode.LIVE:
            if self.live_executor is None:
                raise RuntimeError("LiveExecutor not configured but mode is LIVE")
            return self.live_executor.monitor_open_trades()
        return self.paper_executor.monitor_open_trades()

    def _paper_execute(self, candidate: Any, size: Any) -> Any:
        symbol = str(getattr(candidate, "symbol", ""))
        side = str(getattr(candidate, "side", ""))
        entry = float(getattr(candidate, "entry", 0.0))
        signal_id = int(getattr(candidate, "id", 0))
        scores = getattr(candidate, "scores", {})
        atr = float(scores.get("atr", 0.0)) if scores else 0.0

        levels = self._tp_sl.calculate(entry=entry, atr=atr, side=side)

        self.logger.info(
            "PAPER execute: %s %s entry=%s sl=%s tp=%s",
            symbol, side, levels["entry"], levels["stop"], levels["tp1"],
        )
        return self.paper_executor.open_trade(
            symbol=symbol,
            side=side,
            entry=levels["entry"],
            stop_loss=levels["stop"],
            take_profit=levels["tp1"],
            signal_id=signal_id,
        )
