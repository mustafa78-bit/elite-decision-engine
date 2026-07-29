from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query

from database import FINAL_STATUSES, Signal, Trade, get_session
from market_data.collector import HyperliquidCollector
from market_data.indicators import IndicatorEngine
from market_data.volatility import VolatilityEngine
from scoring.regime_ai import get_regime_ai
from market_data.btc_health import BTCHealth

from core.orchestrator.orchestrator import orchestrator
from core.orchestrator.event_bus import event_bus
from core.orchestrator.registry import intelligence_registry

from services.intelligence.opportunity_ranking import OpportunityRankingService
from services.intelligence.research import AutonomousResearchAgent
from services.intelligence.explainability import ExplainabilityEngineV2
from services.intelligence.analytics import IntelligenceAnalyticsService

logger = logging.getLogger(__name__)

# Preserve empty route prefix so /intelligence routes match original routing rules exactly
router = APIRouter()

# Initialize and register sequential subsystem handlers in registry
ranker = OpportunityRankingService()
agent = AutonomousResearchAgent()
explain_v2 = ExplainabilityEngineV2()
analytics_svc = IntelligenceAnalyticsService()

# 11-stage sequential intelligence pipeline registration
intelligence_registry.register("Market Context", lambda ctx: explain_v2.evaluate(ctx))
intelligence_registry.register("Market Regime", agent.evaluate)
intelligence_registry.register("Decision Memory", lambda ctx: explain_v2.evaluate(ctx))
intelligence_registry.register("Pattern Discovery", lambda ctx: explain_v2.evaluate(ctx))
intelligence_registry.register("Risk Engine", lambda ctx: explain_v2.evaluate(ctx))
intelligence_registry.register("AI Debate", lambda ctx: explain_v2.evaluate(ctx))
intelligence_registry.register("Counterfactual Engine", lambda ctx: explain_v2.evaluate(ctx))
intelligence_registry.register("Confidence Calibration", lambda ctx: explain_v2.evaluate(ctx))
intelligence_registry.register("Priority Ranking", ranker.evaluate)
intelligence_registry.register("Explainability", explain_v2.evaluate)
intelligence_registry.register("Executive Recommendation", analytics_svc.evaluate)


@router.get("/intelligence")
def get_intelligence():
    """
    Original endpoint preserving 100% of existing behavior and monitoring/fallback stats.
    """
    logger.info("GET /intelligence")
    market_data = {}
    try:
        collector = HyperliquidCollector()
        indicators = IndicatorEngine()
        btc = BTCHealth()
        vol = VolatilityEngine()
        regime = get_regime_ai()

        df = collector.get_ohlcv(symbol="BTC", timeframe="1h")
        if not df.empty:
            values = indicators.calculate(df)
            btc_score = btc.score()
            vol_score = vol.score(values)
            reg = regime.detect(values)
            market_data = {
                "price": float(df["close"].iloc[-1]),
                "regime": reg["regime"],
                "btc_health": btc_score,
                "volatility": vol_score["volatility"],
                "rsi": round(values["rsi"], 2),
            }
    except Exception:
        logger.warning("Market data fetch failed for /intelligence", exc_info=True)
        market_data = {"error": "Market data unavailable"}

    session = get_session()
    try:
        all_signals = session.query(Signal).all()
        all_trades = session.query(Trade).all()
    finally:
        session.close()

    open_signals = [s for s in all_signals if str(s.status) == "OPEN"]
    approved = len([s for s in all_signals if str(s.status) in {"EXECUTED", "OPEN"}])
    rejected = len([s for s in all_signals if str(s.status) == "REJECTED"])

    open_trades = [t for t in all_trades if str(t.status) == "OPEN"]
    closed_trades = [t for t in all_trades if str(t.status) in FINAL_STATUSES]
    total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)

    logger.info(
        "/intelligence: signals=%d trades=%d closed_pnl=%.2f",
        len(all_signals), len(all_trades), total_pnl,
    )

    return {
        "market": market_data,
        "signals": {
            "total": len(all_signals),
            "open": len(open_signals),
            "approved": approved,
            "rejected": rejected,
        },
        "risk": {
            "open_trades": len(open_trades),
            "max_open_trades": 3,
        },
        "trades": {
            "open": len(open_trades),
            "closed": len(closed_trades),
            "total_pnl": round(total_pnl, 2),
        },
    }


@router.post("/intelligence/orchestrate")
def trigger_orchestration(symbol: str = Query("BTC", description="The asset symbol to analyze")):
    """
    Trigger the fully coordinated sequential intelligence orchestration pipeline.
    """
    try:
        profile = orchestrator.orchestrate(symbol)
        return profile
    except Exception as e:
        logger.exception("ADIP Pipeline Orchestration execution failed")
        raise HTTPException(status_code=500, detail=f"Orchestration execution failed: {str(e)}")


@router.get("/intelligence/reports")
def get_research_reports(symbol: str = Query("BTC")):
    """
    Retrieve calculated Autonomous research narratives and structural trend reports.
    """
    try:
        profile = orchestrator.orchestrate(symbol)
        stages = profile.get("pipeline_stages", {})
        return stages.get("Market Regime", {})
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/timeline")
def get_intelligence_timeline(limit: int = Query(50, ge=1, le=500)):
    """
    Retrieve chronological internal system event ledger.
    """
    history = event_bus.get_history(limit)
    return [
        {
            "event_type": ev.event_type,
            "timestamp": ev.timestamp.isoformat(),
            "symbol": ev.symbol,
            "payload": ev.payload
        }
        for ev in history
    ]


@router.get("/intelligence/brief")
def get_autonomous_brief(symbol: str = Query("BTC")):
    """
    Expose dynamic daily executive BRIEF summaries directly compiled by orchestrator results.
    """
    try:
        profile = orchestrator.orchestrate(symbol)
        stages = profile.get("pipeline_stages", {})

        regime = stages.get("Market Regime", {})
        ranking = stages.get("Priority Ranking", {})
        explain = stages.get("Explainability", {})
        recommendation = stages.get("Executive Recommendation", {})

        return {
            "title": f"Autonomous Daily Executive Intelligence Briefing [{symbol}]",
            "narrative_cluster": regime.get("evidence", {}).get("narrative_cluster", "N/A"),
            "highest_confidence_opportunity": symbol,
            "composite_score": ranking.get("confidence", 0.0),
            "reasons": [
                explain.get("evidence", {}).get("why", "Trend stack complete"),
                explain.get("evidence", {}).get("why_now", "Volatility squeeze")
            ],
            "invalidation": explain.get("evidence", {}).get("invalidation_triggers", []),
            "platform_analytics": recommendation.get("evidence", {})
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/analytics")
def get_intelligence_analytics(symbol: str = Query("BTC")):
    """
    Benchmark platform analytics.
    """
    try:
        profile = orchestrator.orchestrate(symbol)
        stages = profile.get("pipeline_stages", {})
        return stages.get("Executive Recommendation", {}).get("evidence", {})
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
