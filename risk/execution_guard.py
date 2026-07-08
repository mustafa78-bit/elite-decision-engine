from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Optional

from config import (
    ACCOUNT_EQUITY,
    MAX_DAILY_LOSS,
    MAX_EXPOSURE_PER_SYMBOL,
    MAX_OPEN_TRADES,
    MAX_POSITION_SIZE_USD,
    MAX_PORTFOLIO_EXPOSURE,
    RISK_PER_TRADE_PERCENT,
)
from database import Trade, get_session
from exchange.base import ExchangeAdapter
from exchange.exceptions import ExchangeError
from scoring.regime_engine import RegimeEngine

logger = logging.getLogger(__name__)

FINAL_STATUSES = frozenset({"TP_HIT", "SL_HIT", "CLOSED"})


@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    reason: str
    checks: dict[str, Any]


class ExecutionGuard:
    """Pre-execution risk checks before an order is placed.

    Extends the existing ``RiskManager`` with exchange-specific and
    market-condition checks.
    """

    def __init__(
        self,
        exchange: Optional[ExchangeAdapter] = None,
        regime_engine: Optional[RegimeEngine] = None,
        session_factory: Callable[[], Any] = get_session,
    ) -> None:
        self.exchange = exchange
        self.regime_engine = regime_engine or RegimeEngine()
        self.session_factory = session_factory

    def set_exchange(self, exchange: ExchangeAdapter) -> None:
        self.exchange = exchange

    def can_execute(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
    ) -> GuardResult:
        """Run all pre-execution checks in order."""
        checks: dict[str, Any] = {}
        failures: list[str] = []

        # 1. Exchange connectivity
        if self.exchange is None:
            return GuardResult(False, "No exchange configured", {"exchange": False})
        try:
            checks["exchange_online"] = self.exchange.trading_enabled()
            if not checks["exchange_online"]:
                failures.append("Exchange trading is disabled")
        except ExchangeError as e:
            checks["exchange_online"] = False
            failures.append(f"Exchange offline: {e}")

        # 2. Market volatility condition
        try:
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
                checks["volatility_pct"] = round(atr_pct, 2)
                if atr_pct > 5:
                    failures.append(f"Volatility too high: {atr_pct:.1f}% ATR/price")
            else:
                checks["volatility_pct"] = None
        except Exception as e:
            logger.warning("Volatility check failed: %s", e)
            checks["volatility_pct"] = None

        # 3. Market regime
        try:
            reg = self.regime_engine.detect(None)
            regime_name = reg.get("regime", "UNKNOWN")
            checks["regime"] = regime_name
            if regime_name == "DEAD":
                failures.append("Market regime is DEAD")
        except Exception as e:
            logger.warning("Regime check failed: %s", e)
            checks["regime"] = "UNKNOWN"

        # 4. Max open trades
        session = self.session_factory()
        try:
            open_count = session.query(Trade).filter(Trade.status == "OPEN").count()
            checks["open_trades"] = open_count
            if open_count >= MAX_OPEN_TRADES:
                failures.append(f"Max open trades reached ({open_count}/{MAX_OPEN_TRADES})")
        finally:
            session.close()

        # 5. Position size vs account equity
        notional = entry_price * quantity
        max_notional = ACCOUNT_EQUITY * (RISK_PER_TRADE_PERCENT / 100.0)
        checks["notional"] = round(notional, 2)
        checks["max_notional"] = round(max_notional, 2)
        if notional > max_notional:
            failures.append(f"Position size {notional:.2f} exceeds risk budget {max_notional:.2f}")

        # 6. Daily loss check
        session = self.session_factory()
        try:
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            daily_losses = session.query(Trade.pnl).filter(
                Trade.status.in_(FINAL_STATUSES),
                Trade.closed_at >= today_start,
            ).all()
            total_loss = sum(r.pnl for r in daily_losses if r.pnl is not None and r.pnl < 0)
            checks["daily_loss"] = round(abs(total_loss), 2)
            if abs(total_loss) >= MAX_DAILY_LOSS:
                failures.append(f"Daily loss limit reached ({abs(total_loss):.2f})")
        finally:
            session.close()

        allowed = len(failures) == 0
        return GuardResult(
            allowed=allowed,
            reason="; ".join(failures) if failures else "",
            checks=checks,
        )

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
