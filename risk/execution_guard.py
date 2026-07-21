from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

from config import ACCOUNT_EQUITY, RISK_PER_TRADE_PERCENT
import database
from exchange.base import ExchangeAdapter
from exchange.exceptions import ExchangeError
from risk.models import (
    RejectionCode,
    RiskCheckDetail,
    RiskDecision,
    risk_decision_from_checks,
    summarize_decision,
)
from risk_manager import RiskManager
from scoring.regime_ai import get_regime_ai

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    reason: str
    checks: dict[str, Any]


@dataclass(frozen=True)
class _Candidate:
    symbol: str
    entry: float


class ExecutionGuard:
    """Pre-execution risk checks before an order is placed.

    Extends the existing ``RiskManager`` with exchange-specific and
    market-condition checks.
    """

    def __init__(
        self,
        exchange: Optional[ExchangeAdapter] = None,
        regime_engine: Optional["RegimeAI"] = None,
        session_factory: Optional[Callable[[], Any]] = None,
        market_service: Optional[Any] = None,
    ) -> None:
        self.exchange = exchange
        self.regime_engine = regime_engine or get_regime_ai()
        self.session_factory = session_factory or database.get_session
        self.market_service = market_service

    def set_exchange(self, exchange: ExchangeAdapter) -> None:
        self.exchange = exchange

    def can_execute(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
    ) -> GuardResult:
        """Run all pre-execution checks in order (legacy interface).

        Returns a ``GuardResult`` for backward compatibility.
        For structured results, use ``evaluate_execution``.
        """
        decision = self.evaluate_execution(symbol, side, entry_price, quantity)
        checks: dict[str, Any] = {}
        for c in decision.checks:
            checks[c.name] = c.passed
            if c.value is not None:
                checks[f"{c.name}_value"] = c.value
            if c.limit is not None:
                checks[f"{c.name}_limit"] = c.limit
        return GuardResult(
            allowed=decision.allowed,
            reason=decision.reason,
            checks=checks,
        )

    def evaluate_execution(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
    ) -> RiskDecision:
        """Run all pre-execution checks and return a structured ``RiskDecision``."""
        checks: list[RiskCheckDetail] = []
        metadata: dict[str, Any] = {}

        # 1. Exchange connectivity
        if self.exchange is None:
            decision = risk_decision_from_checks([
                RiskCheckDetail(
                    name=RejectionCode.EXCHANGE_NOT_CONFIGURED,
                    passed=False,
                    detail="No exchange configured",
                ),
            ])
            summarize_decision(decision, "ExecutionGuard")
            return decision
        try:
            online = self.exchange.trading_enabled()
            checks.append(RiskCheckDetail(
                name=RejectionCode.EXCHANGE_OFFLINE,
                passed=online,
                detail="Exchange trading is disabled" if not online else "",
            ))
            if not online:
                decision = risk_decision_from_checks(checks)
                summarize_decision(decision, "ExecutionGuard")
                return decision
        except Exception as e:
            decision = risk_decision_from_checks([
                RiskCheckDetail(
                    name=RejectionCode.EXCHANGE_OFFLINE,
                    passed=False,
                    detail=f"Exchange offline: {e}",
                ),
            ])
            summarize_decision(decision, "ExecutionGuard")
            return decision

        # 2. Market volatility condition
        try:
            if self.market_service is not None:
                indicators = self.market_service.get_indicators(symbol)
                price = self.market_service.get_price(symbol)
                atr = float(indicators.get("atr", 0))
                atr_pct = (atr / price) * 100 if price > 0 else 0
            else:
                from market_data.indicators import IndicatorEngine
                from market_data.collector import HyperliquidCollector
                collector = HyperliquidCollector()
                df = collector.get_ohlcv(symbol=symbol, timeframe="1h", limit=100)
                if not df.empty:
                    indicators = IndicatorEngine()
                    values = indicators.calculate(df)
                    atr = float(values.get("atr", 0))
                    price = float(df["close"].iloc[-1])
                    atr_pct = (atr / price) * 100 if price > 0 else 0
                else:
                    atr_pct = 0
            metadata["volatility_pct"] = round(atr_pct, 2)
            checks.append(RiskCheckDetail(
                name=RejectionCode.VOLATILITY_TOO_HIGH,
                passed=atr_pct <= 5,
                detail=(
                    f"Volatility too high: {atr_pct:.1f}% ATR/price"
                    if atr_pct > 5 else ""
                ),
                value=round(atr_pct, 2),
                limit=5.0,
            ))
            if atr_pct > 5:
                decision = risk_decision_from_checks(checks, metadata)
                summarize_decision(decision, "ExecutionGuard")
                return decision
        except Exception as e:
            logger.warning("Volatility check failed: %s", e)
            metadata["volatility_pct"] = None

        # 3. Market regime
        try:
            reg = self.regime_engine.detect(None)
            regime_name = reg.get("regime", "UNKNOWN")
            metadata["regime"] = regime_name
            checks.append(RiskCheckDetail(
                name=RejectionCode.REGIME_DEAD,
                passed=regime_name != "DEAD",
                detail="Market regime is DEAD" if regime_name == "DEAD" else "",
            ))
            if regime_name == "DEAD":
                decision = risk_decision_from_checks(checks, metadata)
                summarize_decision(decision, "ExecutionGuard")
                return decision
        except Exception as e:
            logger.warning("Regime check failed: %s", e)
            metadata["regime"] = "UNKNOWN"

        # 4. Delegate portfolio-level checks to RiskManager
        candidate = _Candidate(symbol=symbol, entry=entry_price * quantity)
        risk_mgr = RiskManager(session_factory=self.session_factory)
        portfolio_decision = risk_mgr.evaluate_trade(candidate)
        metadata["portfolio_decision"] = portfolio_decision
        checks.extend(portfolio_decision.checks)
        if not portfolio_decision.allowed:
            decision = risk_decision_from_checks(checks, metadata)
            summarize_decision(decision, "ExecutionGuard")
            return decision

        # 5. Position size vs account equity
        notional = entry_price * quantity
        max_notional = ACCOUNT_EQUITY * (RISK_PER_TRADE_PERCENT / 100.0)
        metadata["notional"] = round(notional, 2)
        metadata["max_notional"] = round(max_notional, 2)
        checks.append(RiskCheckDetail(
            name=RejectionCode.RISK_BUDGET_EXCEEDED,
            passed=notional <= max_notional,
            detail=(
                f"Position size {notional:.2f} exceeds risk budget {max_notional:.2f}"
                if notional > max_notional else ""
            ),
            value=round(notional, 2),
            limit=round(max_notional, 2),
        ))
        if notional > max_notional:
            decision = risk_decision_from_checks(checks, metadata)
            summarize_decision(decision, "ExecutionGuard")
            return decision

        decision = risk_decision_from_checks(checks, metadata)
        summarize_decision(decision, "ExecutionGuard")
        return decision

    def estimate_position_size(
        self,
        entry_price: float,
        stop_price: float,
        account_equity: Optional[float] = None,
    ) -> float:
        """Calculate position size based on risk-per-trade."""
        equity = account_equity or float(ACCOUNT_EQUITY)
        risk_amount = equity * (RISK_PER_TRADE_PERCENT / 100.0)
        price_risk = abs(entry_price - stop_price)
        if price_risk <= 0:
            return 0.0
        return risk_amount / price_risk
