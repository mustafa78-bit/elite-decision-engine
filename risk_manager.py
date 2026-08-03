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
from database import FINAL_STATUSES, PaperTrade as PaperTradeModel, Trade, get_session
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

    def __init__(
        self,
        session_factory: Callable[[], Any] = get_session,
        position_sizer: Optional[Any] = None,
    ) -> None:
        self.session_factory = session_factory
        if position_sizer is None:
            from position_sizing import PositionSizingEngine
            self.position_sizer = PositionSizingEngine()
        else:
            self.position_sizer = position_sizer

    def can_open_trade(self, candidate: Any) -> tuple[bool, str]:
        """Check all risk rules (legacy interface).

        Returns:
            (True, "") if all rules pass,
            (False, "reason") on the first rule violation.
        """
        decision = self.evaluate_trade(candidate)
        return decision.allowed, decision.reason

    def evaluate_trade(self, candidate: Any) -> RiskDecision:
        """Evaluate a trade candidate against all portfolio risk rules.

        Returns a structured ``RiskDecision`` with per-check details.
        """
        session = self.session_factory()
        try:
            return self._evaluate(candidate, session)
        finally:
            session.close()

    def _evaluate(self, candidate: Any, session: Any) -> RiskDecision:
        entry = candidate.entry or 0.0

        # Determine candidate's marginal contribution (notional value)
        candidate_notional = 0.0
        if hasattr(candidate, "scores"):
            try:
                position_size = self.position_sizer.calculate(candidate)
                candidate_notional = position_size.notional_value
            except Exception as e:
                logger.warning("Failed to calculate position size speculatively: %s", e)
                candidate_notional = entry
        else:
            candidate_notional = entry
        candidate_notional = candidate_notional or 0.0

        checks: list[RiskCheckDetail] = []

        open_count = (
            session.query(Trade)
            .filter(Trade.status == "OPEN")
            .count()
        )
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

        symbol_trades = (
            session.query(Trade, PaperTradeModel)
            .outerjoin(PaperTradeModel, PaperTradeModel.position_id == Trade.id)
            .filter(Trade.symbol == candidate.symbol, Trade.status == "OPEN")
            .all()
        )
        current_symbol_total = 0.0
        for trade, paper_trade in symbol_trades:
            if paper_trade is not None:
                current_symbol_total += (paper_trade.quantity or 0.0) * (paper_trade.entry or 0.0)
            else:
                current_symbol_total += trade.entry or 0.0
        total_symbol = current_symbol_total + candidate_notional
        checks.append(RiskCheckDetail(
            name=RejectionCode.SYMBOL_EXPOSURE,
            passed=total_symbol <= MAX_EXPOSURE_PER_SYMBOL,
            detail=(
                f"Symbol exposure limit exceeded for {candidate.symbol}: "
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

        portfolio_trades = (
            session.query(Trade, PaperTradeModel)
            .outerjoin(PaperTradeModel, PaperTradeModel.position_id == Trade.id)
            .filter(Trade.status == "OPEN")
            .all()
        )
        current_total = 0.0
        for trade, paper_trade in portfolio_trades:
            if paper_trade is not None:
                current_total += (paper_trade.quantity or 0.0) * (paper_trade.entry or 0.0)
            else:
                current_total += trade.entry or 0.0
        portfolio_total = current_total + candidate_notional
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
            passed=entry <= MAX_POSITION_SIZE_USD,
            detail=(
                f"Position size limit exceeded: "
                f"{entry:.2f} > {MAX_POSITION_SIZE_USD}"
                if entry > MAX_POSITION_SIZE_USD else ""
            ),
            value=round(entry, 2),
            limit=MAX_POSITION_SIZE_USD,
        ))
        if entry > MAX_POSITION_SIZE_USD:
            decision = risk_decision_from_checks(checks)
            summarize_decision(decision, "RiskManager")
            return decision

        decision = risk_decision_from_checks(checks)
        summarize_decision(decision, "RiskManager")
        return decision
