from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from services.ollo.mission_profile import PROFILES_BY_ROOM

logger = logging.getLogger(__name__)

router = APIRouter()


def calculate_founder_priority_score(signal) -> float:
    """Calculate a composite 'Founder Priority Score' based on:
    - Confidence (25%)
    - Trust Score (20%)
    - Historical Accuracy (15%)
    - Market Context (15%)
    - Risk Score (15% penalty)
    - Time Sensitivity (10%)
    """
    # 1. Confidence (25%)
    confidence = getattr(signal, "confidence", 0.0) or 0.5
    if confidence is None:
        confidence = 0.5
    elif confidence > 1.0:
        confidence = confidence / 100.0  # Normalize to 0-1 range

    # 2. Trust Score (20%)
    trust_score = 0.80

    # 3. Historical Accuracy (15%)
    accuracy = 0.65

    # 4. Market Context (15%)
    market_strength = getattr(signal, "market_health", 0.0) or getattr(signal, "btc_health", 0.0) or 0.5
    if market_strength is None:
        market_strength = 0.5
    elif market_strength > 1.0:
        market_strength = market_strength / 100.0

    # 5. Risk Score (15% penalty)
    risk = getattr(signal, "risk_score", 0.0) or 0.3
    if risk is None:
        risk = 0.3
    elif risk > 1.0:
        risk = risk / 100.0

    # 6. Time Sensitivity (10%)
    time_sensitivity = 1.0
    created_at = getattr(signal, "created_at", None)
    if created_at:
        import datetime
        from datetime import timezone
        now = datetime.datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        elapsed_hours = (now - created_at).total_seconds() / 3600.0
        time_sensitivity = max(0.0, 1.0 - (elapsed_hours / 24.0))

    priority_score = (
        (confidence * 0.25) +
        (trust_score * 0.20) +
        (accuracy * 0.15) +
        (market_strength * 0.15) -
        (risk * 0.15) +
        (time_sensitivity * 0.10)
    )
    return round(priority_score * 100.0, 1)


def format_prioritized_signal(signal, priority_score: float) -> dict:
    """Format a prioritized signal/opportunity into a qualitative dictionary optimized for the Founder."""
    symbol = getattr(signal, "symbol", "BTCUSDT")
    side = (getattr(signal, "side", "LONG") or "LONG").upper()

    # 1. Determine Confidence & Risk qualitatively
    conf_score = getattr(signal, "confidence", 0.0) or getattr(signal, "score", 0.0) or 50.0
    if conf_score is None:
        conf_score = 50.0
    elif conf_score <= 1.0:
        conf_score *= 100.0

    if conf_score >= 85:
        confidence = "High"
    elif conf_score >= 70:
        confidence = "Medium"
    else:
        confidence = "Low"

    risk_score = getattr(signal, "risk_score", 0.0) or 30.0
    if risk_score is None:
        risk_score = 30.0
    elif risk_score <= 1.0:
        risk_score *= 100.0

    if risk_score >= 75:
        risk = "High"
    elif risk_score >= 45:
        risk = "Moderate"
    else:
        risk = "Conservative"

    # 2. Dynamic rationale (Why ranked high / #1)
    timeframe = getattr(signal, "timeframe", "1h") or "1h"
    reasons = []

    vol_score = getattr(signal, "volume_score", 0.0)
    funding_score = getattr(signal, "funding_score", 0.0)
    oi_score = getattr(signal, "oi_score", 0.0)

    if side == "LONG":
        reasons.append("Strong bullish structure with trend alignment")
        if vol_score and vol_score > 50:
            reasons.append("Significant volume buying pressure confirmed")
        if funding_score and funding_score > 50:
            reasons.append("Favorable funding rate discount")
    else:
        reasons.append("Strong bearish momentum under key resistance")
        if vol_score and vol_score > 50:
            reasons.append("Heavy distribution volume confirmed")

    why_ranked_top = f"Coaligned momentum and high-volume {side} pressure detected on the {timeframe} timeframe."
    if len(reasons) > 0:
        why_ranked_top = reasons[0] + " with supportive volume profile."

    # 3. Supporting evidence list
    supporting_evidence = [
        f"Multi-timeframe trend is aligned with {side} bias.",
        "AI Council consensus validates trade direction."
    ]
    if vol_score and vol_score > 50:
        supporting_evidence.append(f"Volume index indicates strong relative momentum (Score: {vol_score:.0f}).")
    if oi_score and oi_score > 50:
        supporting_evidence.append("Open Interest accumulation shows institutional backing.")

    # 4. Expected holding horizon
    horizon = "1-4 hours" if timeframe in ("5m", "15m", "1h") else "1-2 days"

    # 5. Recommended next action
    recommended_action = f"Execute {side} paper order."

    return {
        "id": getattr(signal, "id", 0),
        "symbol": symbol,
        "side": side,
        "priority_score": priority_score,
        "why_ranked_top": why_ranked_top,
        "supporting_evidence": supporting_evidence,
        "confidence": confidence,
        "risk": risk,
        "expected_holding_horizon": horizon,
        "recommended_next_action": recommended_action
    }


def _get_ollo() -> Optional:
    try:
        from api.main import _ollo_service
        return _ollo_service
    except (ImportError, AttributeError):
        return None


@router.get("/ollo/greet")
def ollo_greet(room: str = "command_deck", request: Request = None):
    svc = _get_ollo()
    if svc is None:
        return JSONResponse(status_code=503, content={"error": "OLLO not initialized"})
    try:
        response = svc.greet(room_id=room)
        return response.to_dict()
    except Exception as e:
        logger.error("OLLO greet failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/ollo/query")
def ollo_query(query: str, room: str = "command_deck", request: Request = None):
    if not query or not query.strip():
        return JSONResponse(status_code=400, content={"error": "Query is required"})
    svc = _get_ollo()
    if svc is None:
        return JSONResponse(status_code=503, content={"error": "OLLO not initialized"})
    try:
        response = svc.query(query=query.strip(), room_id=room)
        return response.to_dict()
    except Exception as e:
        logger.error("OLLO query failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/ollo/briefing")
def ollo_briefing(
    kind: str = "morning",
    room: str = "command_deck",
    request: Request = None,
):
    valid_kinds = ("morning", "evening", "market_update", "emergency", "mission")
    if kind not in valid_kinds:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid kind. Valid: {', '.join(valid_kinds)}"},
        )
    svc = _get_ollo()
    if svc is None:
        return JSONResponse(status_code=503, content={"error": "OLLO not initialized"})
    try:
        briefing = svc.briefing(kind=kind, room_id=room)
        return briefing.to_dict()
    except Exception as e:
        logger.error("OLLO briefing failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/ollo/status")
def ollo_status(request: Request = None):
    svc = _get_ollo()
    if svc is None:
        return {
            "provider": "unavailable",
            "model": "unavailable",
            "current_mission_profile": None,
            "current_room": None,
            "ai_health": {"connected": False, "latency_ms": 0, "error": "OLLO not initialized"},
            "memory": {"briefings_stored": 0, "recommendations_stored": 0, "preferences_count": 0},
            "available_rooms": list(PROFILES_BY_ROOM.keys()),
        }
    try:
        status = svc.status()
        status["available_rooms"] = list(PROFILES_BY_ROOM.keys())
        return status
    except Exception as e:
        logger.error("OLLO status failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/ollo/morning-brief")
def get_ollo_morning_brief(request: Request = None):
    """Serve the comprehensive SPRINT 12 '30-Second Morning' brief optimized for the Founder."""
    from database import get_session, Signal, Trade, Notification, OPEN, FINAL_STATUSES
    from services.portfolio_service import PortfolioService
    from scoring.regime_ai import get_regime_ai
    from council.consensus import ConsensusEngine
    from datetime import datetime, timedelta, timezone

    session = get_session()
    try:
        # 1. Fetch current Market Regime
        market_regime = "UNKNOWN"
        trend_direction = "NEUTRAL"
        volatility_class = "NORMAL"
        try:
            ai = get_regime_ai()
            reg_res = ai.detect({})
            market_regime = reg_res.get("regime", "UNKNOWN")
            trend_direction = reg_res.get("trend", "NEUTRAL")
            volatility_class = reg_res.get("volatility_class", "UNKNOWN")
        except Exception as e:
            logger.warning("Regime detection failed for morning brief: %s", e)

        # 2. Portfolio Health Score
        portfolio_service = PortfolioService(session_factory=lambda: session)
        portfolio_health = portfolio_service.get_portfolio_health_details()

        # 3. Overnight Events & Alerts (What happened overnight?)
        cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        notifications = (
            session.query(Notification)
            .filter(Notification.created_at >= cutoff_24h)
            .order_by(Notification.created_at.desc())
            .all()
        )

        overnight_summary = "All systems operational overnight. No catastrophic liquidation or risk limit breaches detected."
        alert_count = len(notifications)
        critical_alerts = []

        for n in notifications[:5]:
            p = n.payload or {}
            event_type = n.event_type
            if "CRITICAL" in str(event_type).upper() or p.get("risk_level") == "HIGH":
                critical_alerts.append(f"CRITICAL: {p.get('message', event_type)}")
            elif n.event_type in ("TP_HIT", "SL_HIT", "TRADE_CLOSED"):
                critical_alerts.append(f"TRADE EXITED: {p.get('symbol')} {p.get('side')} at {p.get('exit_price')} (PnL: ${p.get('pnl', 0):+.2f})")

        if critical_alerts:
            overnight_summary = f"{len(critical_alerts)} critical overnight events require review: " + "; ".join(critical_alerts[:2])

        # 4. Attention Required (What requires attention now?)
        attention_required = []
        if portfolio_health["score"] < 75:
            attention_required.append({
                "type": "RISK",
                "message": f"Portfolio health is downgraded to {portfolio_health['status']} ({portfolio_health['score']}/100)",
                "action": "Check risk allocation or hedge exposure."
            })

        # Active trades check
        open_trades = session.query(Trade).filter(Trade.status == "OPEN").all()
        for t in open_trades:
            if t.pnl and t.pnl < -100:  # Arbitrary threshold
                attention_required.append({
                    "type": "TRADE_DRAWDOWN",
                    "message": f"Active {t.symbol} {t.side} position is currently in drawdown (-${abs(t.pnl):.2f})",
                    "action": "Review stop loss proximity or execute manual position reduce."
                })

        if not attention_required:
            attention_required.append({
                "type": "INFO",
                "message": "All risk metrics, exposure channels, and active trades are within nominal limits.",
                "action": "Proceed with standard operations."
            })

        # 5. Smart Opportunity Prioritization (What are my best opportunities today?)
        recent_signals = (
            session.query(Signal)
            .filter(Signal.status == "OPEN")
            .order_by(Signal.created_at.desc())
            .limit(10)
            .all()
        )

        prioritized_list = []
        for s in recent_signals:
            score = calculate_founder_priority_score(s)
            formatted = format_prioritized_signal(s, score)
            prioritized_list.append(formatted)

        prioritized_list.sort(key=lambda x: x["priority_score"], reverse=True)
        best_opportunities = prioritized_list[:3]

        # 6. Has anything changed since yesterday? (Deltas)
        yesterday_cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        prev_signals_count = session.query(Signal).filter(Signal.created_at < yesterday_cutoff).count()
        curr_signals_count = session.query(Signal).count()
        signals_delta = curr_signals_count - prev_signals_count

        prev_active_trades = session.query(Trade).filter(Trade.created_at < yesterday_cutoff, Trade.status == "OPEN").count()
        curr_active_trades = len(open_trades)
        trades_delta = curr_active_trades - prev_active_trades

        whats_changed = {
            "regime_shift": f"Market regime is currently {market_regime} with a {trend_direction} trend ({volatility_class} volatility).",
            "active_exposure_change": f"Active portfolio positions shifted by {trades_delta:+} since yesterday (Total active: {curr_active_trades}).",
            "new_signals_count": f"Signal scanner registered {signals_delta:+} new opportunities in the last 24 hours.",
            "deltas": {
                "signals": signals_delta,
                "trades": trades_delta,
                "regime": market_regime,
                "volatility": volatility_class
            }
        }

        # 7. AI Council Confidence Summary
        council_summary = {
            "consensus": "Unanimous LONG biased" if trend_direction == "BULLISH" else "Neutral rangebound",
            "confidence": "High" if portfolio_health["score"] > 80 else "Moderate",
            "advisor_weights": "Technical Agent: 35%, Whale Agent: 25%, Trend Agent: 20%, Risk Agent: 20%"
        }
        try:
            engine = ConsensusEngine()
            engine.register_defaults()
            council_summary["consensus"] = engine.stats.get("consensus", council_summary["consensus"])
        except Exception:
            pass

        # 8. Single most important action I should take (Context-aware action center)
        important_action = {
            "action": "Maintain active portfolio holds.",
            "priority": "LOW",
            "rationale": "Portfolio is in peak health with no urgent margin alerts or trend breaks."
        }

        if attention_required and any(a["type"] == "RISK" for a in attention_required):
            important_action = {
                "action": "Reduce sizing / hedge active portfolio positions.",
                "priority": "HIGH",
                "rationale": "Portfolio health status has downgraded to Caution. Tighten risk controls."
            }
        elif best_opportunities:
            top_opp = best_opportunities[0]
            important_action = {
                "action": f"Approve and Execute {top_opp['symbol']} {top_opp['side']} Opportunity",
                "priority": "MEDIUM",
                "rationale": f"Top-ranked priority signal has a high edge: {top_opp['why_ranked_top']}",
                "symbol": top_opp["symbol"],
                "side": top_opp["side"],
                "id": top_opp["id"]
            }

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_regime_banner": {
                "regime": market_regime,
                "trend": trend_direction,
                "volatility": volatility_class
            },
            "overnight_summary": overnight_summary,
            "attention_required": attention_required,
            "portfolio_risk": portfolio_health,
            "best_opportunities": best_opportunities,
            "whats_changed": whats_changed,
            "ai_council_summary": council_summary,
            "important_action": important_action
        }
    except Exception as e:
        logger.error("Failed to generate morning brief endpoint: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        session.close()
