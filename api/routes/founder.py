from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import APIRouter, Query, HTTPException

from database import get_session, Signal, Trade, PaperTrade, DecisionExplanation
from services.founder.intelligence import (
    FounderBriefGenerator,
    OpportunityDetector,
    RiskDetector,
    ActionRecommendationEngine,
    FounderDashboardEngine,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/founder/brief")
def get_founder_brief(symbol: str = "BTC"):
    """Fetch the fully consolidated prioritized Founder Brief."""
    logger.info("GET /founder/brief | symbol=%s", symbol)
    try:
        generator = FounderBriefGenerator()
        brief = generator.generate_brief(symbol=symbol)
        return brief
    except Exception as e:
        logger.exception("Failed to generate founder brief")
        raise HTTPException(status_code=500, detail=f"Failed to generate brief: {str(e)}")


@router.get("/founder/opportunities")
def get_founder_opportunities(symbol: Optional[str] = None):
    """Fetch premium ranked opportunities."""
    logger.info("GET /founder/opportunities | symbol=%s", symbol)
    try:
        detector = OpportunityDetector()
        watchlist = [symbol] if symbol else None
        opportunities = detector.detect_opportunities(watchlist_symbols=watchlist)
        return opportunities
    except Exception as e:
        logger.exception("Failed to detect opportunities")
        raise HTTPException(status_code=500, detail=f"Failed to detect opportunities: {str(e)}")


@router.get("/founder/risks")
def get_founder_risks():
    """Fetch systemic risk profile metrics and leverage risk analysis."""
    logger.info("GET /founder/risks")
    try:
        from market_data.btc_health import BTCHealth
        btc_health = BTCHealth()
        btc_score = btc_health.score()

        detector = RiskDetector()
        risks = detector.evaluate_risks(btc_health_score=btc_score)
        return risks
    except Exception as e:
        logger.exception("Failed to evaluate risks")
        raise HTTPException(status_code=500, detail=f"Failed to evaluate risks: {str(e)}")


@router.get("/founder/actions")
def get_founder_actions():
    """Fetch state-derived actionable recommendations including detailed explanation indicators."""
    logger.info("GET /founder/actions")
    try:
        opp_detector = OpportunityDetector()
        opps = opp_detector.detect_opportunities()

        from market_data.btc_health import BTCHealth
        btc_health = BTCHealth()
        btc_score = btc_health.score()

        risk_detector = RiskDetector()
        risks = risk_detector.evaluate_risks(btc_health_score=btc_score)

        from services.founder.intelligence import WhaleIntelligenceSummary
        whale_summary_engine = WhaleIntelligenceSummary()
        whale = whale_summary_engine.generate_summary("BTC", volume_score=0.95, volatility_score=0.8)

        action_engine = ActionRecommendationEngine()
        recommendations = action_engine.generate_recommendations(opps, risks, whale)
        return recommendations
    except Exception as e:
        logger.exception("Failed to generate actionable recommendations")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.get("/founder/dashboard")
def get_founder_dashboard(symbol: str = "BTC"):
    """Main entrypoint for the Founder Command Center answering What Happened, Why It Matters, and What To Do."""
    logger.info("GET /founder/dashboard | symbol=%s", symbol)
    try:
        dashboard_engine = FounderDashboardEngine()
        data = dashboard_engine.get_dashboard_briefing(symbol)
        return data
    except Exception as e:
        logger.exception("Failed to generate founder dashboard summary")
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")


@router.get("/founder/history")
def get_founder_history(limit: int = Query(50, ge=1, le=100)):
    """Fetch a timeline historical trace of completed signals, past trades, and execution metrics."""
    logger.info("GET /founder/history | limit=%d", limit)
    session = get_session()
    try:
        past_signals = (
            session.query(Signal)
            .filter(Signal.status.in_(["EXECUTED", "REJECTED", "CLOSED"]))
            .order_by(Signal.created_at.desc())
            .limit(limit)
            .all()
        )
        past_trades = (
            session.query(Trade)
            .filter(Trade.status.in_(["CLOSED", "TP_HIT", "SL_HIT", "CANCEL"]))
            .order_by(Trade.created_at.desc())
            .limit(limit)
            .all()
        )
        past_explanations = (
            session.query(DecisionExplanation)
            .order_by(DecisionExplanation.created_at.desc())
            .limit(limit)
            .all()
        )

        signals_json = []
        for s in past_signals:
            signals_json.append({
                "id": s.id,
                "symbol": s.symbol,
                "side": s.side,
                "score": s.score,
                "confidence": s.confidence,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            })

        trades_json = []
        for t in past_trades:
            trades_json.append({
                "id": t.id,
                "symbol": t.symbol,
                "side": t.side,
                "entry": t.entry,
                "exit": t.exit_price,
                "pnl": t.pnl,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            })

        explanations_json = []
        for e in past_explanations:
            explanations_json.append({
                "id": e.id,
                "symbol": e.symbol,
                "side": e.side,
                "decision": e.decision,
                "confidence": e.confidence,
                "summary": e.summary,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            })

        return {
            "signals": signals_json,
            "trades": trades_json,
            "explanations": explanations_json,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.exception("Failed to query historical context")
        raise HTTPException(status_code=500, detail=f"Failed to query history: {str(e)}")
    finally:
        session.close()
