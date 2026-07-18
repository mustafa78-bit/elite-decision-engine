from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class OLLOContext:
    portfolio_summary: Optional[dict] = None
    portfolio_distribution: Optional[dict] = None
    portfolio_performance: Optional[dict] = None
    portfolio_risk: Optional[dict] = None
    scanner_signals: Optional[dict] = None
    market_regime: Optional[dict] = None
    risk_metrics: Optional[dict] = None
    whale_activity: Optional[dict] = None
    council_latest: Optional[dict] = None
    council_full: Optional[dict] = None
    room: str = ""
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
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
    "whale_activity": "market.intelligence.whale.WhaleAnalyzer",
    "council_latest": "council.consensus.ConsensusEngine",
    "council_full": "council.consensus.ConsensusEngine",
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
                data = self._load(key, loader)
                if data is not None:
                    setattr(ctx, key, data)
            except Exception as e:
                msg = f"Failed to load {key}: {e}"
                logger.warning(msg)
                ctx.errors.append(msg)
        return ctx

    def _load(self, key: str, loader_path: str) -> Any:
        if loader_path == "services.portfolio_service.PortfolioService":
            return self._load_portfolio(key)
        if loader_path == "scanner.core.ScannerEngine":
            return self._load_scanner()
        if loader_path == "scoring.regime_ai.RegimeAI":
            return self._load_regime()
        if loader_path == "risk_manager":
            return self._load_risk()
        if loader_path == "market.intelligence.whale.WhaleAnalyzer":
            return self._load_whale()
        if loader_path == "council.consensus.ConsensusEngine":
            return self._load_council(key)
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
            from risk_manager import RiskManager
            rm = RiskManager()
            return {"status": "loaded"}
        except Exception as e:
            logger.warning("Risk load failed: %s", e)
            return None

    def _load_whale(self) -> Any:
        try:
            from market.intelligence.whale import WhaleAnalyzer
            wa = WhaleAnalyzer()
            return {"status": "loaded"}
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
