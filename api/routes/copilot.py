from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from database import Signal, Trade, get_session
from portfolio_engine import PortfolioEngine
from risk_manager import RiskManager
from config import (
    MAX_OPEN_TRADES,
    MAX_EXPOSURE_PER_SYMBOL,
    MAX_PORTFOLIO_EXPOSURE,
    MAX_DAILY_LOSS,
    ACCOUNT_EQUITY,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Pydantic Schemas ---

class CopilotChatRequest(BaseModel):
    message: str = Field(..., description="The user query to the AI Copilot")
    symbol: Optional[str] = Field("BTC", description="Optional context symbol")

class CopilotLink(BaseModel):
    label: str
    path: str

class CopilotChatResponse(BaseModel):
    reply: str
    suggestions: List[str]
    links: List[CopilotLink]
    metrics: Dict[str, Any]

# --- Query Handlers ---

def handle_why_buy(symbol: str, session: Any) -> CopilotChatResponse:
    # 1. Fetch latest signal
    sig = (
        session.query(Signal)
        .filter(Signal.symbol == symbol.upper())
        .order_by(Signal.created_at.desc())
        .first()
    )

    # 2. Get market info or use fallback
    from api.main import get_mip
    try:
        mip = get_mip()
        asset = mip.get_asset(symbol.upper())
        price = asset.price or (sig.price if sig else 0.0)
        regime = asset.indicators.get("regime", "UNKNOWN") if asset.indicators else "UNKNOWN"
        rsi = asset.indicators.get("rsi", 50.0) if asset.indicators else 50.0
        atr = asset.indicators.get("atr", 0.0) if asset.indicators else 0.0
    except Exception as e:
        logger.warning("Could not load real-time market data for copilot: %s", e)
        price = sig.price if sig else 0.0
        regime = "UNKNOWN"
        rsi = 50.0
        atr = 0.0

    if sig:
        trend = sig.trend_score or 0.0
        vol = sig.volume_score or 0.0
        btc = sig.btc_health or 0.0
        risk = sig.risk_score or 0.0
        total_score = sig.score or 0.0
        confidence = sig.confidence or 0.0
        side = sig.side or "LONG"
    else:
        # Fallback default values
        trend, vol, btc, risk, total_score, confidence, side = 0.5, 0.5, 0.5, 0.5, 50.0, 50.0, "LONG"

    # Compile the reply
    reply = (
        f"### AI Analysis: Why Buy {symbol.upper()}?\n\n"
        f"Based on the latest decision engine evaluation, **{symbol.upper()}** has the following profile:\n\n"
        f"- **Current Action/Side**: `{side}`\n"
        f"- **Current Price**: `${price:,.2f}`\n"
        f"- **Overall Score**: `{total_score:.1f}` (Confidence: `{confidence:.1f}%`)\n"
        f"- **Market Regime**: `{regime}`\n"
        f"- **RSI (1h)**: `{rsi:.1f}`\n"
        f"- **ATR (1h)**: `{atr:.2f}`\n\n"
        f"#### Score Breakdown:\n"
        f"- 📈 **Trend Strength**: `{trend * 100:.1f}%`\n"
        f"- 📊 **Volume Participation**: `{vol * 100:.1f}%`\n"
        f"- 🛡️ **BTC Health Context**: `{btc * 100:.1f}%`\n"
        f"- ⚠️ **Risk Score Penalty**: `{risk * 100:.1f}%`\n\n"
    )

    if total_score >= 80:
        reply += (
            f"**Conclusion**: **STRONG APPROVE**. {symbol.upper()} is showing solid bullish trend alignment with "
            f"positive volume surge and supportive BTC health context. RSI is in a healthy momentum zone."
        )
    elif total_score >= 70:
        reply += (
            f"**Conclusion**: **APPROVE / WATCH**. Trend momentum is supportive, but minor risk factors or "
            f"volume exhaustion are present. Consider scaling in incrementally."
        )
    else:
        reply += (
            f"**Conclusion**: **REJECT**. Score is below minimum guidelines. Volatility may be extreme or BTC context "
            f"is bearish. Better to wait for setup confirmation."
        )

    suggestions = [
        f"What is the current RSI of {symbol.upper()}?",
        "What are the biggest portfolio risks?",
        "Show me the best opportunities today.",
    ]
    links = [
        CopilotLink(label="Decision Center", path="/decisions"),
        CopilotLink(label="Signals Dashboard", path="/signals"),
    ]
    metrics = {
        "symbol": symbol.upper(),
        "price": price,
        "score": total_score,
        "confidence": confidence,
        "regime": regime,
        "rsi": rsi,
        "atr": atr,
        "trend_score": trend,
        "volume_score": vol,
        "btc_score": btc,
        "risk_score": risk,
    }

    return CopilotChatResponse(reply=reply, suggestions=suggestions, links=links, metrics=metrics)


def handle_what_changed(session: Any) -> CopilotChatResponse:
    # 1. Fetch recent signals in last hour
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    # SQLite naive timezone support
    one_hour_ago_naive = one_hour_ago.replace(tzinfo=None)

    recent_signals = (
        session.query(Signal)
        .filter(Signal.created_at >= one_hour_ago_naive)
        .all()
    )

    # 2. Get latest BTC updates
    from api.main import get_mip
    btc_regime = "UNKNOWN"
    btc_price = 0.0
    try:
        mip = get_mip()
        btc_asset = mip.get_asset("BTC")
        btc_regime = btc_asset.indicators.get("regime", "UNKNOWN") if btc_asset.indicators else "UNKNOWN"
        btc_price = btc_asset.price
    except Exception:
        pass

    reply = "### Market Changes (Last 1 Hour)\n\n"
    if recent_signals:
        reply += f"Detected **{len(recent_signals)}** new trading signals generated in the last hour:\n\n"
        for sig in recent_signals:
            price_val = sig.price if sig.price is not None else 0.0
            score_val = sig.score if sig.score is not None else 0.0
            conf_val = sig.confidence if sig.confidence is not None else 0.0
            reply += (
                f"- **{sig.symbol}** ({sig.side}): Score: `{score_val:.1f}` | "
                f"Confidence: `{conf_val:.1f}%` | Price: `${price_val:,.2f}`\n"
            )
        reply += "\n"
    else:
        reply += "No new trading signals were generated in the last hour. Markets are consolidating within current ranges.\n\n"

    reply += "#### Current Benchmark Status:\n"
    reply += f"- **BTC/USDT Price**: `${btc_price:,.2f}`\n"
    reply += f"- **Current Market Regime**: `{btc_regime}`\n\n"
    reply += "Stay alert for unexpected volatility spikes. Ensure Stop Losses are configured."

    suggestions = [
        "Show me the best opportunities today.",
        "What happens if BTC drops 10%?",
        "What are the biggest portfolio risks?",
    ]
    links = [
        CopilotLink(label="Timeline Page", path="/timeline"),
        CopilotLink(label="Live Market", path="/live-market"),
    ]
    metrics = {
        "recent_signals_count": len(recent_signals),
        "btc_price": btc_price,
        "btc_regime": btc_regime,
    }

    return CopilotChatResponse(reply=reply, suggestions=suggestions, links=links, metrics=metrics)


def handle_portfolio_risks(session: Any) -> CopilotChatResponse:
    # 1. Fetch portfolio metrics
    engine = PortfolioEngine(session_factory=lambda: session)
    stats = engine.stats()

    # 2. Extract risk components
    open_trades_count = stats.open_trades
    portfolio_exposure = stats.current_open_exposure
    daily_loss = abs(stats.daily_pnl) if stats.daily_pnl < 0 else 0.0

    # Calculate limits utilization
    trades_pct = (open_trades_count / MAX_OPEN_TRADES) * 100
    exposure_pct = (portfolio_exposure / MAX_PORTFOLIO_EXPOSURE) * 100
    loss_pct = (daily_loss / MAX_DAILY_LOSS) * 100

    reply = (
        "### 🛡️ Portfolio Risk Assessment\n\n"
        "Here is the active risk profile of your portfolio:\n\n"
        "| Risk Factor | Current Value | Hard Limit | Utilization |\n"
        "| :--- | :--- | :--- | :--- |\n"
        f"| **Active Positions** | `{open_trades_count}` trades | `{MAX_OPEN_TRADES}` trades | `{trades_pct:.1f}%` |\n"
        f"| **Total Exposure** | `${portfolio_exposure:,.2f}` | `${MAX_PORTFOLIO_EXPOSURE:,.2f}` | `{exposure_pct:.1f}%` |\n"
        f"| **Daily Realized Loss** | `${daily_loss:,.2f}` | `${MAX_DAILY_LOSS:,.2f}` | `{loss_pct:.1f}%` |\n\n"
    )

    risk_warnings = []
    if trades_pct >= 100:
        risk_warnings.append("⚠️ **Max Trades Reached**: Trading engine will reject new positions to enforce safety margins.")
    if exposure_pct >= 80:
        risk_warnings.append("⚠️ **High Capital Exposure**: Portfolio exposure is nearing limits. De-leveraging is recommended.")
    if loss_pct >= 80:
        risk_warnings.append("🚨 **Daily Loss Warning**: Nearing maximum daily drawdown threshold. Consider pausing automatic strategies.")

    if not risk_warnings:
        reply += "✅ **Overall Status: HEALTHY**. All parameters are within optimal safety ranges."
    else:
        reply += "#### Active Warnings:\n" + "\n".join(risk_warnings)

    suggestions = [
        "What happens if BTC drops 10%?",
        "Show me the best opportunities today.",
        "Why should I buy BTC?",
    ]
    links = [
        CopilotLink(label="Risk Settings", path="/risk"),
        CopilotLink(label="Portfolio Stats", path="/portfolio"),
    ]
    metrics = {
        "open_trades": open_trades_count,
        "max_trades": MAX_OPEN_TRADES,
        "portfolio_exposure": portfolio_exposure,
        "max_exposure": MAX_PORTFOLIO_EXPOSURE,
        "daily_loss": daily_loss,
        "max_daily_loss": MAX_DAILY_LOSS,
    }

    return CopilotChatResponse(reply=reply, suggestions=suggestions, links=links, metrics=metrics)


def handle_what_if_drops(session: Any) -> CopilotChatResponse:
    # 1. Simulate a 10% drop on BTC and portfolio
    engine = PortfolioEngine(session_factory=lambda: session)
    stats = engine.stats()

    # Get open trades to find exposures
    open_trades = session.query(Trade).filter(Trade.status == "OPEN").all()
    btc_positions = [t for t in open_trades if "BTC" in t.symbol.upper()]
    other_positions = [t for t in open_trades if "BTC" not in t.symbol.upper()]

    # 10% drop simulation:
    # BTC positions drop 10%. Non-BTC positions drop 15% due to higher beta (typical for crypto).
    simulated_loss = 0.0
    for t in btc_positions:
        entry = t.entry or 0.0
        # typical 10% hit
        simulated_loss += entry * 0.10
    for t in other_positions:
        entry = t.entry or 0.0
        # higher beta crypto drops 15%
        simulated_loss += entry * 0.15

    new_unrealized_pnl = stats.unrealized_pnl - simulated_loss
    new_equity = stats.equity - simulated_loss
    drawdown_pct = (simulated_loss / stats.equity * 100) if stats.equity > 0 else 0.0

    reply = (
        "### 📉 Stress Test Simulation: BTC Drops 10%\n\n"
        "Simulating a **-10.0% market correction** on your active portfolio:\n\n"
        f"- **Current Portfolio Equity**: `${stats.equity:,.2f}`\n"
        f"- **Simulated Drawdown Hit**: `- ${simulated_loss:,.2f}` (`{drawdown_pct:.2f}%` equity hit)\n"
        f"- **Projected Portfolio Equity**: `${new_equity:,.2f}`\n"
        f"- **Projected Unrealized PnL**: `${new_unrealized_pnl:,.2f}`\n\n"
        "#### Impact Analysis:\n"
    )

    if simulated_loss > MAX_DAILY_LOSS:
        reply += f"❌ **CRITICAL VIOLATION**: Simulated loss exceeds the maximum Daily Loss limit of `${MAX_DAILY_LOSS:,.2f}`. This would trigger automated position reductions.\n"
    else:
        reply += "✅ **SAFE LIMITS**: Projected loss remains within manageable drawdown rules.\n"

    reply += "\n*Recommendations: Ensure Stop Losses are tightly configured and reduce leverage on high-beta altcoins.*"

    suggestions = [
        "What are the biggest portfolio risks?",
        "Show me top trading opportunities",
        "Why should I buy BTC?",
    ]
    links = [
        CopilotLink(label="Risk Controls", path="/risk"),
        CopilotLink(label="Paper Portfolio", path="/paper-trading"),
    ]
    metrics = {
        "current_equity": stats.equity,
        "simulated_loss": simulated_loss,
        "projected_equity": new_equity,
        "drawdown_pct": drawdown_pct,
        "limit_violated": simulated_loss > MAX_DAILY_LOSS,
    }

    return CopilotChatResponse(reply=reply, suggestions=suggestions, links=links, metrics=metrics)


def handle_best_opportunities(session: Any) -> CopilotChatResponse:
    # 1. Fetch high score signals (score >= 70 or sorted by score desc)
    signals = (
        session.query(Signal)
        .order_by(Signal.score.desc())
        .limit(5)
        .all()
    )

    reply = "### ⚡ Top Trading Opportunities Today\n\n"
    if signals:
        reply += "Here are the top-rated setups from the Elite Decision Engine:\n\n"
        for i, sig in enumerate(signals, 1):
            side_badge = "🟩 BUY" if sig.side == "LONG" or sig.side == "BUY" else "🟥 SELL"
            price_val = sig.price if sig.price is not None else 0.0
            score_val = sig.score if sig.score is not None else 0.0
            conf_val = sig.confidence if sig.confidence is not None else 0.0
            trend_val = sig.trend_score if sig.trend_score is not None else 0.0
            vol_val = sig.volume_score if sig.volume_score is not None else 0.0
            reply += (
                f"{i}. **{sig.symbol}** ({sig.timeframe}) — {side_badge}\n"
                f"   - **Decision Score**: `{score_val:.1f}` (Confidence: `{conf_val:.1f}%`)\n"
                f"   - **Entry Target**: `${price_val:,.2f}`\n"
                f"   - **Trend Align**: `{trend_val * 100:.1f}%` | "
                f"Volume Confirm: `{vol_val * 100:.1f}%`\n\n"
            )
    else:
        reply += "No clear technical opportunities detected currently. Volatility might be sub-optimal or trend structures are neutral. Consider monitoring high-volume watchlist items.\n\n"

    reply += "*Disclaimer: Leverage trading carries risk. Confirm risk-to-reward ratios before execution.*"

    suggestions = [
        "Why should I buy BTC?",
        "What changed in the last hour?",
        "What are the biggest portfolio risks?",
    ]
    links = [
        CopilotLink(label="Decision Center", path="/decisions"),
        CopilotLink(label="Signals Table", path="/signals"),
    ]
    metrics = {
        "opportunities_count": len(signals),
        "top_symbol": signals[0].symbol if signals else None,
    }

    return CopilotChatResponse(reply=reply, suggestions=suggestions, links=links, metrics=metrics)


def handle_fallback(message: str, symbol: str, session: Any) -> CopilotChatResponse:
    reply = (
        f"### Elite Decision Assistant\n\n"
        f"Hello! I am your conversational intelligence copilot. I am fully integrated with the "
        f"**Decision Engine**, **Portfolio Stats**, **Risk Engine**, and **Market Indicators**.\n\n"
        f"I received your message: *\"{message}\"*\n\n"
        f"You can ask me highly-contextual questions such as:\n"
        f"- 📊 **\"Why should I buy {symbol}?\"**\n"
        f"- 🕒 **\"What changed in the last hour?\"**\n"
        f"- 🛡️ **\"What are the biggest portfolio risks?\"**\n"
        f"- 📉 **\"What happens if BTC drops 10%?\"**\n"
        f"- ⚡ **\"Show me the best opportunities today.\"**\n\n"
        f"How would you like to proceed?"
    )

    suggestions = [
        f"Why should I buy {symbol}?",
        "What changed in the last hour?",
        "What are the biggest portfolio risks?",
        "What happens if BTC drops 10%?",
        "Show me the best opportunities today.",
    ]
    links = [
        CopilotLink(label="Dashboard", path="/dashboard"),
    ]
    metrics = {
        "status": "fallback",
        "symbol": symbol,
    }

    return CopilotChatResponse(reply=reply, suggestions=suggestions, links=links, metrics=metrics)

# --- Chat Endpoint ---

@router.post("/copilot/chat", response_model=CopilotChatResponse)
def copilot_chat(payload: CopilotChatRequest):
    session = get_session()
    try:
        msg = payload.message.lower().strip()
        symbol = payload.symbol or "BTC"

        # Route request based on intent keywords
        if "why should i buy" in msg or "why buy" in msg:
            return handle_why_buy(symbol, session)
        elif "what changed in" in msg or "last hour" in msg or "what changed" in msg:
            return handle_what_changed(session)
        elif "biggest portfolio risks" in msg or "portfolio risks" in msg or "portfolio risk" in msg:
            return handle_portfolio_risks(session)
        elif "btc drops 10%" in msg or "if btc drops" in msg or "drops 10%" in msg or "drops 10" in msg:
            return handle_what_if_drops(session)
        elif "best opportunities" in msg or "opportunities today" in msg or "opportunities" in msg:
            return handle_best_opportunities(session)
        else:
            return handle_fallback(payload.message, symbol, session)
    except Exception as e:
        logger.exception("AI Copilot failed to process message: %s", e)
        raise HTTPException(status_code=500, detail=f"AI Copilot Error: {str(e)}")
    finally:
        session.close()
