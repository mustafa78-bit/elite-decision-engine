import logging
from enum import Enum
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class GuardOutcome(Enum):
    PASS = "PASS"
    WARN = "WARN"
    DEFER = "DEFER"
    REJECT = "REJECT"

class ConstraintGuard:
    """
    NEXUS Immutable Constraint Guard.
    Acts as a non-overrideable safety check gate. Completely isolates raw AI suggestions
    from execution paths and ensures strict alignment with portfolio parameters and founder preferences.
    """
    def __init__(
        self,
        max_open_trades: int = 3,
        max_exposure_per_symbol: float = 200000.0,
        max_daily_loss: float = 10000.0
    ):
        self.max_open_trades = max_open_trades
        self.max_exposure_per_symbol = max_exposure_per_symbol
        self.max_daily_loss = max_daily_loss

    def evaluate(
        self,
        symbol: str,
        active_trades_count: int,
        symbol_exposure: float,
        current_daily_loss: float,
        score: float
    ) -> Tuple[GuardOutcome, List[str]]:
        """
        Executes strict verification rules and returns a structured non-binary outcome:
        PASS, WARN, DEFER, or REJECT.
        """
        reasons = []
        outcomes = []

        # Rule 1: Critical Open Trades Cap
        if active_trades_count >= self.max_open_trades:
            reasons.append(f"REJECT: Open trades count ({active_trades_count}) meets limit ({self.max_open_trades}).")
            outcomes.append(GuardOutcome.REJECT)

        # Rule 2: Exposure Checks
        if symbol_exposure >= self.max_exposure_per_symbol:
            reasons.append(f"REJECT: Symbol exposure ({symbol_exposure}) exceeds limit ({self.max_exposure_per_symbol}).")
            outcomes.append(GuardOutcome.REJECT)
        elif symbol_exposure > (self.max_exposure_per_symbol * 0.8):
            reasons.append(f"WARN: Symbol exposure ({symbol_exposure}) is reaching critical limits.")
            outcomes.append(GuardOutcome.WARN)

        # Rule 3: Daily Loss Sentry
        if current_daily_loss >= self.max_daily_loss:
            reasons.append(f"REJECT: Current daily loss ({current_daily_loss}) exceeds threshold ({self.max_daily_loss}).")
            outcomes.append(GuardOutcome.REJECT)

        # Rule 4: Cognitive Score Minimum Requirements
        if score < 0.70:
            reasons.append(f"REJECT: Cognitive recommendation score ({score:.2f}) is too low.")
            outcomes.append(GuardOutcome.REJECT)
        elif score < 0.85:
            reasons.append(f"WARN: Recommendation score ({score:.2f}) is marginal.")
            outcomes.append(GuardOutcome.WARN)

        # Non-binary Outcome Consolidation Flow
        if GuardOutcome.REJECT in outcomes:
            return GuardOutcome.REJECT, reasons
        elif GuardOutcome.DEFER in outcomes:
            return GuardOutcome.DEFER, reasons
        elif GuardOutcome.WARN in outcomes:
            return GuardOutcome.WARN, reasons

        reasons.append("PASS: All system-wide hard constraints cleanly passed.")
        return GuardOutcome.PASS, reasons
