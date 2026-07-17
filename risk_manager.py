"""Portfolio-level risk controls for the Elite Decision Engine.

Enforces hard limits on open trades, symbol exposure, portfolio exposure,
daily loss, and position size before a trade is opened.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from config import (
    MAX_DAILY_LOSS,
    MAX_EXPOSURE_PER_SYMBOL,
    MAX_OPEN_TRADES,
    MAX_POSITION_SIZE_USD,
    MAX_PORTFOLIO_EXPOSURE,
)
from database import FINAL_STATUSES, Trade, get_session
from risk.models import (
    RejectionCode,
    RiskCheckDetail,
    RiskDecision,
    risk_decision_from_checks,
    summarize_decision,
)

logger = logging.getLogger(__name__)


class RiskManager:
    """Enforce portfolio-level risk rules before a trade is opened.

    Each rule is checked in order. The first violation short-circuits.
    """

    def __init__(self, session_factory: Callable[[], Any] = get_session) -> None:
        self.session_factory = session_factory

    def can_open_trade(self, candidate: Any) -> tuple[bool, str]:
        """Check all risk rules (legacy interface).

        Returns:
            (True, "") if all rules pass,
            (False, "reason") on the first rule violation.
        """
        decision = self.evaluate_trade(candidate)
        return decision.allowed, decision.reason

    def evaluate_trade(self, candidate: Any, session: Optional[Any] = None) -> RiskDecision:
        """Evaluate a trade candidate against all portfolio risk rules.

        Returns a structured ``RiskDecision`` with per-check details.
        """
        if session is not None:
            return self._evaluate(candidate, session)
        session_instance = self.session_factory()
        try:
            return self._evaluate(candidate, session_instance)
        finally:
            session_instance.close()

    def _evaluate(self, candidate: Any, session: Any) -> RiskDecision:
        checks: list[RiskCheckDetail] = []

        # 1. Candidate structural validation
        symbol = getattr(candidate, "symbol", None)
        side = getattr(candidate, "side", None)
        entry = getattr(candidate, "entry", None)

        if not symbol or not isinstance(symbol, str) or len(symbol.strip()) == 0:
            checks.append(RiskCheckDetail(
                name=RejectionCode.INVALID_TRADE,
                passed=False,
                detail="Invalid trade candidate: missing or invalid symbol.",
                value=0.0,
                limit=0.0,
            ))
            decision = risk_decision_from_checks(checks)
            summarize_decision(decision, "RiskManager")
            return decision

        if not side or not isinstance(side, str) or side.upper() not in ("LONG", "SHORT"):
            checks.append(RiskCheckDetail(
                name=RejectionCode.INVALID_TRADE,
                passed=False,
                detail=f"Invalid trade candidate: invalid side '{side}'. Side must be LONG or SHORT.",
                value=0.0,
                limit=0.0,
            ))
            decision = risk_decision_from_checks(checks)
            summarize_decision(decision, "RiskManager")
            return decision

        entry_val = entry or 0.0
        if entry_val < 0:
            checks.append(RiskCheckDetail(
                name=RejectionCode.INVALID_TRADE,
                passed=False,
                detail=f"Invalid entry price: {entry_val:.2f}. Entry price cannot be negative.",
                value=float(entry_val),
                limit=0.0,
            ))
            decision = risk_decision_from_checks(checks)
            summarize_decision(decision, "RiskManager")
            return decision

        # 2. Performance Optimization: Consolidate 3 DB queries into 1 query for open trades
        open_trades = (
            session.query(Trade)
            .filter(Trade.status == "OPEN")
            .all()
        )
        open_count = len(open_trades)

        checks.append(RiskCheckDetail(
            name=RejectionCode.MAX_OPEN_TRADES,
            passed=open_count < MAX_OPEN_TRADES,
            detail=(
                f"Maximum open trades reached ({open_count}/{MAX_OPEN_TRADES})"
                if open_count >= MAX_OPEN_TRADES else ""
            ),
            value=float(open_count),
            limit=float(MAX_OPEN_TRADES),
        ))
        if open_count >= MAX_OPEN_TRADES:
            decision = risk_decision_from_checks(checks)
            summarize_decision(decision, "RiskManager")
            return decision

        current_symbol_total = sum(
            r.entry for r in open_trades
            if r.symbol == symbol and r.entry is not None
        )
        total_symbol = current_symbol_total + entry_val
        checks.append(RiskCheckDetail(
            name=RejectionCode.SYMBOL_EXPOSURE,
            passed=total_symbol <= MAX_EXPOSURE_PER_SYMBOL,
            detail=(
                f"Symbol exposure limit exceeded for {symbol}: "
                f"{total_symbol:.2f} > {MAX_EXPOSURE_PER_SYMBOL}"
                if total_symbol > MAX_EXPOSURE_PER_SYMBOL else ""
            ),
            value=round(total_symbol, 2),
            limit=MAX_EXPOSURE_PER_SYMBOL,
        ))
        if total_symbol > MAX_EXPOSURE_PER_SYMBOL:
            decision = risk_decision_from_checks(checks)
            summarize_decision(decision, "RiskManager")
            return decision

        current_total = sum(r.entry for r in open_trades if r.entry is not None)
        portfolio_total = current_total + entry_val
        checks.append(RiskCheckDetail(
            name=RejectionCode.PORTFOLIO_EXPOSURE,
            passed=portfolio_total <= MAX_PORTFOLIO_EXPOSURE,
            detail=(
                f"Portfolio exposure limit exceeded: "
                f"{portfolio_total:.2f} > {MAX_PORTFOLIO_EXPOSURE}"
                if portfolio_total > MAX_PORTFOLIO_EXPOSURE else ""
            ),
            value=round(portfolio_total, 2),
            limit=MAX_PORTFOLIO_EXPOSURE,
        ))
        if portfolio_total > MAX_PORTFOLIO_EXPOSURE:
            decision = risk_decision_from_checks(checks)
            summarize_decision(decision, "RiskManager")
            return decision

        # 3. Standardize timezone representation to tz-naive for maximum DB compatibility
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=None
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
        abs_loss = abs(total_loss)
        checks.append(RiskCheckDetail(
            name=RejectionCode.DAILY_LOSS_LIMIT,
            passed=abs_loss < MAX_DAILY_LOSS,
            detail=(
                f"Daily loss limit reached: "
                f"{abs_loss:.2f} >= {MAX_DAILY_LOSS}"
                if abs_loss >= MAX_DAILY_LOSS else ""
            ),
            value=round(abs_loss, 2),
            limit=MAX_DAILY_LOSS,
        ))
        if abs_loss >= MAX_DAILY_LOSS:
            decision = risk_decision_from_checks(checks)
            summarize_decision(decision, "RiskManager")
            return decision

        checks.append(RiskCheckDetail(
            name=RejectionCode.POSITION_SIZE_LIMIT,
            passed=entry_val <= MAX_POSITION_SIZE_USD,
            detail=(
                f"Position size limit exceeded: "
                f"{entry_val:.2f} > {MAX_POSITION_SIZE_USD}"
                if entry_val > MAX_POSITION_SIZE_USD else ""
            ),
            value=round(entry_val, 2),
            limit=MAX_POSITION_SIZE_USD,
        ))
        if entry_val > MAX_POSITION_SIZE_USD:
            decision = risk_decision_from_checks(checks)
            summarize_decision(decision, "RiskManager")
            return decision

        decision = risk_decision_from_checks(checks)
        summarize_decision(decision, "RiskManager")
        return decision
