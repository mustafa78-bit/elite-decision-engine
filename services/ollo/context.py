from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class OLLOContext:
    portfolio_summary: dict | None = None
    portfolio_distribution: dict | None = None
    portfolio_performance: dict | None = None
    portfolio_risk: dict | None = None
    scanner_signals: dict | None = None
    market_regime: dict | None = None
    risk_metrics: dict | None = None
    whale_activity: dict | None = None
    council_latest: dict | None = None
    council_full: dict | None = None
    trade_history: dict | None = None
    recent_conversation: dict | None = None
    room: str = ""
    collected_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None or k in ("room", "collected_at")}

    def summary_line(self) -> str:
        loaded = [k for k, v in self.__dict__.items() if v is not None and k not in ("room", "collected_at", "errors")]
        return f"Context loaded: {', '.join(loaded)}"


_CONTEXT_LOADERS: dict[str, str] = {
    "portfolio_summary": "services.portfolio_service.PortfolioService",
    "portfolio_distribution": "services.portfolio_service.PortfolioService",
    "portfolio_performance": "services.portfolio_service.PortfolioService",
    "portfolio_risk": "services.portfolio_service.PortfolioService",
    "scanner_signals": "scanner.core.ScannerEngine",
    "market_regime": "scoring.regime_ai.RegimeAI",
    "risk_metrics": "risk_manager",
    "whale_activity": "market.intelligence.whale.WhaleService",
    "council_latest": "council.consensus.ConsensusEngine",
    "council_full": "council.consensus.ConsensusEngine",
    "trade_history": "memory.trade_memory.TradeMemory",
    "recent_conversation": "services.ollo.memory.CommanderMemory",
}


class ContextBuilder:

    def build(self, context_keys: list[str], room: str = "") -> OLLOContext:
        ctx = OLLOContext(room=room)
        for key in context_keys:
            try:
                loader = _CONTEXT_LOADERS.get(key)
                if loader is None:
                    ctx.errors.append(f"No loader for context key: {key}")
                    continue
                data = self._load(key, loader, room=room)
                if data is not None:
                    setattr(ctx, key, data)
            except Exception as e:
                msg = f"Failed to load {key}: {e}"
                logger.warning(msg)
                ctx.errors.append(msg)
        return ctx

    def _load(self, key: str, loader_path: str, room: str = "") -> Any:
        if loader_path == "services.portfolio_service.PortfolioService":
            return self._load_portfolio(key)
        if loader_path == "scanner.core.ScannerEngine":
            return self._load_scanner()
        if loader_path == "scoring.regime_ai.RegimeAI":
            return self._load_regime()
        if loader_path == "risk_manager":
            return self._load_risk()
        if loader_path == "market.intelligence.whale.WhaleService":
            return self._load_whale()
        if loader_path == "council.consensus.ConsensusEngine":
            return self._load_council(key)
        if loader_path == "memory.trade_memory.TradeMemory":
            return self._load_trade_history()
        if loader_path == "services.ollo.memory.CommanderMemory":
            return self._load_recent_conversation(room)
        return None

    def _load_portfolio(self, key: str) -> Any:
        try:
            from services.portfolio_service import PortfolioService
            svc = PortfolioService()
            mapping = {
                "portfolio_summary": svc.summary,
                "portfolio_distribution": svc.distribution,
                "portfolio_performance": svc.performance,
                "portfolio_risk": svc.risk_metrics,
            }
            method = mapping.get(key)
            return method() if method else None
        except Exception as e:
            logger.warning("Portfolio load failed for %s: %s", key, e)
            return None

    def _load_scanner(self) -> Any:
        try:
            from scanner.core import ScannerEngine
            engine = ScannerEngine()
            results = engine.scan()
            count = len(results) if results else 0
            return {
                "signal_count": count,
                "top_signals": [self._summarize_signal(s) for s in (results or [])[:5]],
            }
        except Exception as e:
            logger.warning("Scanner load failed: %s", e)
            return None

    def _summarize_signal(self, signal: Any) -> dict:
        try:
            return {
                "symbol": getattr(signal, "symbol", "?"),
                "side": getattr(signal, "side", "?"),
                "score": getattr(signal, "score", 0),
                "timeframe": getattr(signal, "timeframe", "?"),
            }
        except Exception:
            return {"symbol": "?", "side": "?", "score": 0}

    def _load_regime(self) -> Any:
        try:
            from scoring.regime_ai import get_regime_ai
            ai = get_regime_ai()
            result = ai.detect({})
            return {
                "regime": result.get("regime", "UNKNOWN"),
                "trend": result.get("trend", "NEUTRAL"),
                "trend_strength": result.get("trend_strength", "UNKNOWN"),
                "volatility_class": result.get("volatility_class", "UNKNOWN"),
            }
        except Exception as e:
            logger.warning("Regime load failed: %s", e)
            return None

    def _load_risk(self) -> Any:
        try:
            from config import MAX_DAILY_LOSS, MAX_OPEN_TRADES, MAX_PORTFOLIO_EXPOSURE
            from risk_manager import RiskManager

            class DummyCandidate:
                def __init__(self, symbol: str = "BTC", entry: float = 0.0) -> None:
                    self.symbol = symbol
                    self.entry = entry

            rm = RiskManager()
            candidate = DummyCandidate()
            decision = rm.evaluate_trade(candidate)

            metrics = {
                "allowed": decision.allowed,
                "reason": decision.reason,
                "open_trades": 0,
                "max_open_trades": MAX_OPEN_TRADES,
                "portfolio_exposure": 0.0,
                "max_portfolio_exposure": MAX_PORTFOLIO_EXPOSURE,
                "daily_loss": 0.0,
                "max_daily_loss": MAX_DAILY_LOSS,
                "status": "active"
            }

            for check in decision.checks:
                if check.name == "MAX_OPEN_TRADES":
                    metrics["open_trades"] = int(check.value) if check.value is not None else 0
                elif check.name == "PORTFOLIO_EXPOSURE":
                    metrics["portfolio_exposure"] = check.value if check.value is not None else 0.0
                elif check.name == "DAILY_LOSS_LIMIT":
                    metrics["daily_loss"] = check.value if check.value is not None else 0.0

            present_check_names = {check.name for check in decision.checks}
            need_exposure = "PORTFOLIO_EXPOSURE" not in present_check_names
            need_daily_loss = "DAILY_LOSS_LIMIT" not in present_check_names

            if need_exposure or need_daily_loss:
                from database import FINAL_STATUSES, Trade
                session = rm.session_factory()
                try:
                    if need_exposure:
                        total_exposure = session.query(Trade.entry).filter(Trade.status == "OPEN").all()
                        metrics["portfolio_exposure"] = round(sum(r.entry for r in total_exposure if r.entry is not None), 2)

                    if need_daily_loss:
                        today_start = datetime.now(UTC).replace(
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
                        metrics["daily_loss"] = round(abs(total_loss), 2)
                finally:
                    session.close()

            return metrics
        except Exception as e:
            logger.warning("Risk load failed: %s", e)
            return None

    def _load_whale(self) -> Any:
        try:
            from market.intelligence.whale import WhaleService
            from market.services import MarketDataService

            ws = WhaleService()
            mds = MarketDataService()

            target_symbols = ["BTC", "ETH"]
            all_signals = []

            for symbol in target_symbols:
                asset = mds.get_asset(symbol)
                if asset and not asset.is_empty:
                    volume_score = asset.indicators.get("volume_score")
                    volatility_score = asset.indicators.get("volatility_score")
                    price = asset.price

                    if asset.intelligence and getattr(asset.intelligence, "whales", None):
                        all_signals.extend(asset.intelligence.whales)
                    else:
                        signals = ws.detect(
                            symbol=symbol,
                            volume_score=volume_score,
                            volatility_score=volatility_score,
                            price=price
                        )
                        all_signals.extend(signals)

            return {
                "signals": all_signals,
                "signal_count": len(all_signals),
                "status": "active"
            }
        except Exception as e:
            logger.warning("Whale load failed: %s", e)
            return None

    def _load_council(self, key: str) -> Any:
        try:
            from council.consensus import ConsensusEngine
            engine = ConsensusEngine()
            engine.register_defaults()
            if key == "council_full":
                return engine.stats
            return {
                "agent_count": len(engine.agents),
                "agents": list(engine.agents.keys()),
            }
        except Exception as e:
            logger.warning("Council load failed: %s", e)
            return None

    def _load_trade_history(self) -> Any:
        try:
            from memory.trade_memory import TradeMemory
            tm = TradeMemory()
            stats = tm.stats()
            # list returns TradeMemoryEntry objects
            all_trades = tm.list(limit=20)
            closed_trades = [t for t in all_trades if t.result != "PENDING"][:5]
            recent_closed_trades = [
                {
                    "symbol": t.symbol,
                    "side": t.side,
                    "result": t.result,
                    "pnl": t.pnl,
                    "lessons": t.lessons,
                }
                for t in closed_trades
            ]
            return {
                "stats": stats,
                "recent_closed_trades": recent_closed_trades,
            }
        except Exception as e:
            logger.warning("Trade history load failed: %s", e)
            return None

    def _load_recent_conversation(self, room: str) -> Any:
        try:
            from services.ollo.memory import CommanderMemory
            mem = CommanderMemory()
            recs = mem.recent_recommendations(limit=3, room=room)
            last_briefing_rec = mem.last_briefing()

            recent_exchanges = []
            for r in recs:
                # Truncate response_text to roughly 200 chars
                truncated_resp = r.response_text
                if truncated_resp and len(truncated_resp) > 200:
                    truncated_resp = truncated_resp[:200] + "..."
                recent_exchanges.append({
                    "query": r.query,
                    "response_text": truncated_resp,
                    "timestamp": r.timestamp,
                })

            last_briefing = None
            if last_briefing_rec:
                truncated_text = last_briefing_rec.text
                if truncated_text and len(truncated_text) > 200:
                    truncated_text = truncated_text[:200] + "..."
                last_briefing = {
                    "kind": last_briefing_rec.kind,
                    "text": truncated_text,
                    "timestamp": last_briefing_rec.timestamp,
                }

            return {
                "recent_exchanges": recent_exchanges,
                "last_briefing": last_briefing,
            }
        except Exception as e:
            logger.warning("Recent conversation load failed: %s", e)
            return None
