from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RejectionCode:
    MAX_OPEN_TRADES = "MAX_OPEN_TRADES"
    SYMBOL_EXPOSURE = "SYMBOL_EXPOSURE"
    PORTFOLIO_EXPOSURE = "PORTFOLIO_EXPOSURE"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    POSITION_SIZE_LIMIT = "POSITION_SIZE_LIMIT"
    VOLATILITY_TOO_HIGH = "VOLATILITY_TOO_HIGH"
    REGIME_DEAD = "REGIME_DEAD"
    EXCHANGE_OFFLINE = "EXCHANGE_OFFLINE"
    EXCHANGE_NOT_CONFIGURED = "EXCHANGE_NOT_CONFIGURED"
    RISK_BUDGET_EXCEEDED = "RISK_BUDGET_EXCEEDED"
    INVALID_TRADE = "INVALID_TRADE"


@dataclass(frozen=True)
class RiskCheckDetail:
    name: str
    passed: bool
    detail: str = ""
    value: Optional[float] = None
    limit: Optional[float] = None


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str = ""
    rejection_code: Optional[str] = None
    checks: tuple[RiskCheckDetail, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def first_failure(self) -> Optional[RiskCheckDetail]:
        for c in self.checks:
            if not c.passed:
                return c
        return None


def risk_decision_from_checks(
    checks: list[RiskCheckDetail],
    metadata: Optional[dict[str, Any]] = None,
) -> RiskDecision:
    failures = [c for c in checks if not c.passed]
    if failures:
        first = failures[0]
        return RiskDecision(
            allowed=False,
            reason=first.detail,
            rejection_code=first.name,
            checks=tuple(checks),
            metadata=metadata or {},
        )
    return RiskDecision(
        allowed=True,
        reason="",
        checks=tuple(checks),
        metadata=metadata or {},
    )


def summarize_decision(decision: RiskDecision, component: str) -> None:
    if decision.allowed:
        logger.info("[%s] Risk check passed: all %s checks OK", component, len(decision.checks))
    else:
        logger.warning(
            "[%s] Risk rejected: code=%s reason=%s",
            component, decision.rejection_code, decision.reason,
        )
