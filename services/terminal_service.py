"""TerminalService — unified data aggregation for the Elite Terminal."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from database import FINAL_STATUSES, Signal, Trade, get_session
from decision.aggregator import DecisionAggregator
from market.services import MarketDataService
from performance_engine import PerformanceEngine
from portfolio_engine import PortfolioEngine
from scanner.core import OpportunityScanner
from scoring.risk_engine import RiskEngine

logger = logging.getLogger(__name__)


class TerminalService:
    """Aggregate all platform data for terminal display."""

    def __init__(
        self,
        market_service: Optional[MarketDataService] = None,
        scanner: Optional[OpportunityScanner] = None,
        aggregator: Optional[DecisionAggregator] = None,
    ) -> None:
        self.market_service = market_service or MarketDataService()
        self.scanner = scanner or OpportunityScanner()
        self.aggregator = aggregator or DecisionAggregator()

    def get_overview(self) -> dict[str, Any]:
        return {
            "market": self._get_market_health(),
            "portfolio": self._get_portfolio_summary(),
            "performance": self._get_performance_summary(),
            "open_trades": self._get_open_trades(),
            "recent_signals": self._get_recent_signals(),
            "top_opportunities": self._get_top_opportunities(),
            "risk_status": self._get_risk_status(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_market(self) -> dict[str, Any]:
        return self._get_market_health()

    def get_open_trades(self) -> list[dict[str, Any]]:
        return self._get_open_trades()

    def get_scanner_opportunities(self, n: int = 5) -> list[dict[str, Any]]:
        return self._get_top_opportunities(n)

    def get_recent_signals(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._get_recent_signals(limit)

    def get_risk(self) -> dict[str, Any]:
        return self._get_risk_status()

    def get_portfolio(self) -> dict[str, Any]:
        return self._get_portfolio_summary()

    def get_performance(self) -> dict[str, Any]:
        return self._get_performance_summary()

    def _get_market_health(self) -> dict[str, Any]:
        asset = self.market_service.get_asset("BTC")
        if asset.is_empty:
            return {"status": "UNAVAILABLE", "price": 0, "btc_trend": "UNKNOWN"}

        ctx = asset.context
        btc_ctx = ctx.get("btc", {})
        indicators = asset.indicators
        intelligence = asset.intelligence

        fg_label = intelligence.fear_greed.get("label", "UNKNOWN") if intelligence and intelligence.fear_greed else "UNKNOWN"

        return {
            "status": "ACTIVE",
            "price": asset.price,
            "btc_trend": btc_ctx.get("btc_trend", "UNKNOWN"),
            "btc_price": btc_ctx.get("btc_price", 0),
            "session": ctx.get("session", ""),
            "funding_state": ctx.get("funding", {}).get("state", "UNKNOWN"),
            "fear_greed": fg_label,
            "rsi": indicators.get("rsi", 0),
            "volatility_score": indicators.get("volatility_score", 0),
            "volume_score": indicators.get("volume_score", 0),
        }

    def _get_portfolio_summary(self) -> dict[str, Any]:
        try:
            stats = PortfolioEngine().stats()
            return {
                "total_pnl": round(stats.total_pnl, 2),
                "total_trades": stats.total_trades,
                "open_trades": stats.open_trades,
                "win_rate": round(stats.win_rate, 4),
                "max_drawdown": round(stats.max_drawdown, 4),
            }
        except Exception as e:
            logger.warning("Portfolio summary error: %s", e)
            return {}

    def _get_performance_summary(self) -> dict[str, Any]:
        try:
            stats = PerformanceEngine().stats()
            return {
                "sharpe_ratio": round(stats.sharpe_ratio, 4),
                "profit_factor": round(stats.profit_factor, 4),
                "expectancy": round(stats.expectancy, 4),
                "avg_win": round(stats.avg_win, 2),
                "avg_loss": round(stats.avg_loss, 2),
                "consecutive_wins": stats.consecutive_wins,
                "consecutive_losses": stats.consecutive_losses,
            }
        except Exception as e:
            logger.warning("Performance summary error: %s", e)
            return {}

    def _get_open_trades(self) -> list[dict[str, Any]]:
        try:
            session = get_session()
            try:
                trades = session.query(Trade).filter(Trade.status == "OPEN").all()
            finally:
                session.close()

            return [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "side": t.side,
                    "entry_price": float(t.entry_price) if t.entry_price else 0,
                    "current_price": float(t.exit_price) if t.exit_price else float(t.entry_price or 0),
                    "quantity": float(t.quantity) if t.quantity else 0,
                    "pnl": round(float(t.pnl or 0), 2),
                    "created_at": t.created_at.isoformat() if t.created_at else "",
                }
                for t in trades
            ]
        except Exception as e:
            logger.warning("Open trades error: %s", e)
            return []

    def _get_recent_signals(self, limit: int = 10) -> list[dict[str, Any]]:
        try:
            session = get_session()
            try:
                rows = (
                    session.query(Signal)
                    .order_by(Signal.created_at.desc().nullslast())
                    .limit(limit)
                    .all()
                )
            finally:
                session.close()

            return [
                {
                    "id": s.id,
                    "symbol": s.symbol,
                    "side": s.side,
                    "score": round(s.score, 3) if s.score else 0,
                    "confidence": round(s.confidence, 2) if s.confidence else 0,
                    "status": s.status,
                    "created_at": s.created_at.isoformat() if s.created_at else "",
                }
                for s in rows
            ]
        except Exception as e:
            logger.warning("Recent signals error: %s", e)
            return []

    def _get_top_opportunities(self, n: int = 5) -> list[dict[str, Any]]:
        try:
            opportunities = self.scanner.top_opportunities(n=n)
            return [
                {
                    "rank": o.rank,
                    "symbol": o.symbol,
                    "side": o.side,
                    "strategy": o.strategy,
                    "score": o.score,
                    "probability": o.probability_score,
                    "risk_score": o.risk_score,
                    "confidence": o.confidence,
                    "price": o.price,
                }
                for o in opportunities
            ]
        except Exception as e:
            logger.warning("Top opportunities error: %s", e)
            return []

    def _get_risk_status(self) -> dict[str, Any]:
        try:
            session = get_session()
            try:
                all_trades = session.query(Trade).all()
            finally:
                session.close()

            open_count = len([t for t in all_trades if t.status == "OPEN"])
            engine = RiskEngine()
            risk_score = engine.score({"atr": 0}, {"score": 0})

            return {
                "risk_score": risk_score,
                "open_trades": open_count,
                "max_open_trades": 3,
                "total_trades": len(all_trades),
            }
        except Exception as e:
            logger.warning("Risk status error: %s", e)
            return {"risk_score": 0, "open_trades": 0}
