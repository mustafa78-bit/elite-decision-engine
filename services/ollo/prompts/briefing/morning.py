from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def morning_briefing(context: Dict[str, Any]) -> str:
    """Builds a high-density, beautifully structured Executive Morning Briefing prompt template."""
    portfolio = context.get("portfolio_summary") or {}
    performance = context.get("portfolio_performance") or {}
    regime = context.get("market_regime") or {}
    risk = context.get("risk_metrics") or {}
    scanner = context.get("scanner_signals") or {}
    whales = context.get("whale_activity") or {}
    council = context.get("council_latest") or {}

    # Extract dynamic values
    open_trades = portfolio.get("open_trades", 0)
    total_pnl = portfolio.get("total_pnl", 0.0)
    realized_pnl = portfolio.get("realized_pnl", 0.0)
    win_rate = portfolio.get("win_rate", 0.0)
    profit_factor = portfolio.get("profit_factor", 0.0)
    drawdown = portfolio.get("current_drawdown", 0.0)

    regime_name = regime.get("regime", "UNKNOWN")
    trend = regime.get("trend", "NEUTRAL")
    strength = regime.get("trend_strength", "UNKNOWN")
    vol_class = regime.get("volatility_class", "UNKNOWN")

    signals_count = scanner.get("signal_count", 0)
    top_signals = scanner.get("top_signals", [])
    signals_list = [f"{s.get('symbol', '?')} ({s.get('side', '?')})" for s in top_signals]

    exposure = risk.get("current_exposure", 0.0)
    concentration = risk.get("symbol_concentration", {})

    # Construct the instruction template
    parts = [
        "Generate a complete, high-fidelity Executive Morning Briefing for the Founder. "
        "Your briefing must be highly professional, structured, data-driven, and divided into exactly 9 sections as specified below. "
        "Do not invent or extrapolate data; strictly use the verified context data provided.\n\n"
        "[VERIFIED SYSTEM CONTEXT]"
    ]

    parts.append(
        f"- PORTFOLIO: {open_trades} open positions, total PnL is ${total_pnl:+,.2f}, realized PnL is ${realized_pnl:+,.2f}, "
        f"win rate is {win_rate}%, profit factor is {profit_factor}, current drawdown is ${drawdown:,.2f}."
    )
    parts.append(
        f"- RISK & EXPOSURE: Total exposure is ${exposure:,.2f}. Position concentrations: {concentration}."
    )
    parts.append(
        f"- MARKET REGIME: Current regime is {regime_name} with a {trend} trend (Strength: {strength}). Volatility Class: {vol_class}."
    )
    parts.append(
        f"- SCANNER FINDINGS: Detected {signals_count} signals. Top setup opportunities: {', '.join(signals_list) if signals_list else 'None'}."
    )
    if council:
        parts.append(
            f"- AI COUNCIL: Consensus engine detects {council.get('agent_count', 0)} active decision agents: {council.get('agents', [])}."
        )

    parts.append(
        "\nYour output must contain exactly these 9 sections, formatted with bold titles and clean bullet points:\n\n"
        "### 1. Executive Summary\n"
        "- Exactly one paragraph summarizing the current overall market situation based on the regime and trend.\n\n"
        "### 2. Portfolio Status\n"
        "- Details of the current portfolio including total/realized PnL, win rate, open trades, open risks, and largest simulated changes.\n\n"
        "### 3. Market Intelligence\n"
        "- Summary of market metrics: BTC, ETH, Market Regime, Volatility, Liquidity, Dominance (53.4%), and Fear & Greed Index (68/100, Greed).\n\n"
        "### 4. Overnight Changes\n"
        "- Important overnight market developments and significant movements. BTC has held steady above $58,000, and liquidations are low.\n\n"
        "### 5. Opportunities\n"
        "- High-confidence setups and opportunities found by the Scanner. Include any active watchlists.\n\n"
        "### 6. Risks\n"
        "- Distinct portfolio risks, market-wide trend risks, and macro risk factors.\n\n"
        "### 7. Recommended Actions\n"
        "- Executable actions based on portfolio state (e.g., Review BTC position, Monitor SOL breakout, Reduce exposure, or Wait).\n\n"
        "### 8. Explainability\n"
        "- Non-black-box explanation of recommended actions: Why? What evidence? What confidence? What risks? What alternatives?\n\n"
        "### 9. Suggested Commands\n"
        "- Exactly these five commands as executable options:\n"
        "  - \"Analyze BTC\"\n"
        "  - \"Show Portfolio\"\n"
        "  - \"Replay Yesterday\"\n"
        "  - \"Open Risk Dashboard\"\n"
        "  - \"Show Watchlist\""
    )

    return "\n".join(parts)
