"""Portfolio-level risk controls for the Elite Decision Engine.

Enforces hard limits on open trades, symbol exposure, portfolio exposure,
daily loss, and position size before a trade is opened.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timezone
from typing import Any

from config import (
    MAX_DAILY_LOSS,
    MAX_EXPOSURE_PER_SYMBOL,
    MAX_OPEN_TRADES,
    MAX_PORTFOLIO_EXPOSURE,
    MAX_POSITION_SIZE_USD,
)
from database import FINAL_STATUSES, PaperTrade, Trade, get_session
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
        position_sizer: Any | None = None,
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
        # candidate_notional feeds directly into the SYMBOL_EXPOSURE/
        # PORTFOLIO_EXPOSURE checks below -- entry is a raw per-unit price,
        # not a dollar notional, so it must never be used as a silent
        # fallback (a real position could be several units, making entry a
        # large understatement of true notional). If real sizing can't be
        # computed, we can't safely evaluate exposure at all -- fail closed
        # instead of guessing.
        if not hasattr(candidate, "scores"):
            return risk_decision_from_checks([
                RiskCheckDetail(
                    name=RejectionCode.INVALID_TRADE,
                    passed=False,
                    detail="Candidate missing scores -- cannot compute real position size for exposure checks",
                )
            ])
        try:
            position_size = self.position_sizer.calculate(candidate)
            candidate_notional = position_size.notional_value or 0.0
        except Exception as e:
            logger.warning("Failed to calculate position size speculatively: %s", e)
            return risk_decision_from_checks([
                RiskCheckDetail(
                    name=RejectionCode.INVALID_TRADE,
                    passed=False,
                    detail=f"Position size calculation failed -- cannot safely evaluate exposure: {e}",
                )
            ])

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
            session.query(Trade, PaperTrade)
            .outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
            .filter(Trade.symbol == candidate.symbol, Trade.status == "OPEN")
            .all()
        )
        current_symbol_total = 0.0
        for trade, paper_trade in symbol_trades:
            if paper_trade is not None:
                current_symbol_total += (paper_trade.quantity or 0.0) * (paper_trade.entry or 0.0)
            else:
                # Trade has no matching PaperTrade row (e.g. the journal
                # write failed after the Trade was committed) -- Trade has
                # no quantity column, so trade.entry is a raw per-unit price,
                # not notional dollars. Mixing it into a dollar sum would
                # silently corrupt the exposure check; exclude and warn
                # instead of guessing.
                logger.warning(
                    "RiskManager: OPEN trade %s (%s) has no matching PaperTrade -- "
                    "excluded from symbol exposure total, not counted as notional",
                    trade.id, trade.symbol,
                )
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
            session.query(Trade, PaperTrade)
            .outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
            .filter(Trade.status == "OPEN")
            .all()
        )
        current_total = 0.0
        for trade, paper_trade in portfolio_trades:
            if paper_trade is not None:
                current_total += (paper_trade.quantity or 0.0) * (paper_trade.entry or 0.0)
            else:
                logger.warning(
                    "RiskManager: OPEN trade %s (%s) has no matching PaperTrade -- "
                    "excluded from portfolio exposure total, not counted as notional",
                    trade.id, trade.symbol,
                )
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

        today_start = datetime.now(UTC).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        daily_closed_trades = (
            session.query(Trade, PaperTrade)
            .outerjoin(PaperTrade, PaperTrade.position_id == Trade.id)
            .filter(
                Trade.status.in_(FINAL_STATUSES),
                Trade.closed_at >= today_start,
            )
            .all()
        )
        total_loss = 0.0
        for trade, paper_trade in daily_closed_trades:
            if trade.pnl is None:
                continue
            if paper_trade is not None:
                dollar_pnl = (paper_trade.quantity or 0.0) * trade.pnl
            else:
                logger.warning(
                    "RiskManager: closed trade %s (%s) has no matching PaperTrade -- "
                    "excluded from daily loss total, not counted as dollar PnL",
                    trade.id, trade.symbol,
                )
                continue
            if dollar_pnl < 0:
                total_loss += dollar_pnl
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

        decision = risk_decision_from_checks(checks)
        summarize_decision(decision, "RiskManager")
        return decision
