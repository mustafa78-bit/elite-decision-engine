"""Portfolio-level risk controls for the Elite Decision Engine.

Enforces hard limits on open trades, symbol exposure, portfolio exposure,
daily loss, and position size before a trade is opened.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable

from config import (
    MAX_DAILY_LOSS,
    MAX_EXPOSURE_PER_SYMBOL,
    MAX_OPEN_TRADES,
    MAX_POSITION_SIZE_USD,
    MAX_PORTFOLIO_EXPOSURE,
)
from database import FINAL_STATUSES, Trade, get_session

logger = logging.getLogger(__name__)


class RiskManager:
    """Enforce portfolio-level risk rules before a trade is opened.

    Each rule is checked in order. The first violation short-circuits
    and returns ``(False, "reason")``.
    """

    def __init__(self, session_factory: Callable[[], Any] = get_session) -> None:
        self.session_factory = session_factory

    def can_open_trade(self, candidate: Any) -> tuple[bool, str]:
        """Check all risk rules for the proposed trade.

        Returns:
            (True, "") if all rules pass,
            (False, "reason") on the first rule violation.
        """
        session = self.session_factory()
        try:
            return self._check(candidate, session)
        finally:
            session.close()

    def _check(self, candidate: Any, session: Any) -> tuple[bool, str]:
        entry = candidate.entry or 0.0

        open_count = (
            session.query(Trade)
            .filter(Trade.status == "OPEN")
            .count()
        )
        if open_count >= MAX_OPEN_TRADES:
            reason = f"Maximum open trades reached ({open_count}/{MAX_OPEN_TRADES})"
            logger.warning("Risk rejected: %s", reason)
            return False, reason

        symbol_exposure = (
            session.query(Trade.entry)
            .filter(Trade.symbol == candidate.symbol, Trade.status == "OPEN")
            .all()
        )
        current_symbol_total = sum(r.entry for r in symbol_exposure)
        total_symbol = current_symbol_total + entry
        if total_symbol > MAX_EXPOSURE_PER_SYMBOL:
            reason = (
                f"Symbol exposure limit exceeded for {candidate.symbol}: "
                f"{total_symbol:.2f} > {MAX_EXPOSURE_PER_SYMBOL}"
            )
            logger.warning("Risk rejected: %s", reason)
            return False, reason

        total_exposure = (
            session.query(Trade.entry)
            .filter(Trade.status == "OPEN")
            .all()
        )
        current_total = sum(r.entry for r in total_exposure)
        portfolio_total = current_total + entry
        if portfolio_total > MAX_PORTFOLIO_EXPOSURE:
            reason = (
                f"Portfolio exposure limit exceeded: "
                f"{portfolio_total:.2f} > {MAX_PORTFOLIO_EXPOSURE}"
            )
            logger.warning("Risk rejected: %s", reason)
            return False, reason

        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        daily_losses = (
            session.query(Trade.pnl)
            .filter(
                Trade.status.in_(FINAL_STATUSES),
                Trade.closed_at >= today_start,
            )
            .all()
        )
        total_loss = sum(r.pnl for r in daily_losses if r.pnl is not None and r.pnl < 0)
        if abs(total_loss) >= MAX_DAILY_LOSS:
            reason = (
                f"Daily loss limit reached: "
                f"{abs(total_loss):.2f} >= {MAX_DAILY_LOSS}"
            )
            logger.warning("Risk rejected: %s", reason)
            return False, reason

        if entry > MAX_POSITION_SIZE_USD:
            reason = (
                f"Position size limit exceeded: "
                f"{entry:.2f} > {MAX_POSITION_SIZE_USD}"
            )
            logger.warning("Risk rejected: %s", reason)
            return False, reason

        return True, ""
