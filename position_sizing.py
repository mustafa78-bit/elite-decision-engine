"""Position sizing for the Elite Decision Engine.

Calculates quantity, notional value, and risk amount per trade based on
account equity, risk percentage, and ATR.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from config import (
    ACCOUNT_EQUITY,
    ATR_MULTIPLIER,
    MAX_POSITION_SIZE_USD,
    MIN_POSITION_QUANTITY,
    RISK_PER_TRADE_PERCENT,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PositionSize:
    quantity: float
    notional_value: float
    risk_amount: float


class PositionSizingEngine:

    def __init__(
        self,
        account_equity: Optional[float] = None,
        risk_percentage: Optional[float] = None,
        atr_multiplier: Optional[float] = None,
        max_position_usd: Optional[float] = None,
        min_quantity: Optional[float] = None,
    ) -> None:
        self.account_equity = account_equity if account_equity is not None else ACCOUNT_EQUITY
        self.risk_percentage = risk_percentage if risk_percentage is not None else RISK_PER_TRADE_PERCENT
        self.atr_multiplier = atr_multiplier if atr_multiplier is not None else ATR_MULTIPLIER
        self.max_position_usd = max_position_usd if max_position_usd is not None else MAX_POSITION_SIZE_USD
        self.min_quantity = min_quantity if min_quantity is not None else MIN_POSITION_QUANTITY

    def calculate(self, candidate: Any) -> PositionSize:
        entry = candidate.entry or 0.0
        atr = candidate.scores.get("atr", 0.0)

        risk_per_unit = atr * self.atr_multiplier
        if risk_per_unit <= 0:
            logger.warning("ATR is zero or negative; using minimum position size")
            return PositionSize(
                quantity=self.min_quantity,
                notional_value=round(self.min_quantity * entry, 2),
                risk_amount=0.0,
            )

        account_risk = self.account_equity * self.risk_percentage / 100.0
        raw_quantity = account_risk / risk_per_unit

        notional = raw_quantity * entry
        if notional > self.max_position_usd:
            clamped = self.max_position_usd / entry if entry > 0 else 0.0
            final = max(clamped, self.min_quantity)
        else:
            final = max(raw_quantity, self.min_quantity)

        return PositionSize(
            quantity=round(final, 8),
            notional_value=round(final * entry, 2),
            risk_amount=round(final * risk_per_unit, 2),
        )
