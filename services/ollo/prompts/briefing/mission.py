def mission_briefing(context: dict) -> str:
    room = context.get("room", "command_deck")
    portfolio = context.get("portfolio_summary", {})
    regime = context.get("market_regime", {})
    risk = context.get("risk_metrics", {})

    parts = ["Prepare a Mission Briefing."]
    parts.append(f"Mission area: {room}.")
    parts.append(f"Portfolio: {portfolio.get('open_trades', 0)} open trades, PnL ${portfolio.get('total_pnl', 0):+,.2f}.")
    parts.append(f"Market regime: {regime.get('regime', 'UNKNOWN')}.")
    if risk:
        parts.append(f"Exposure: ${risk.get('current_exposure', 0):,.2f}.")
    parts.append("Provide a focused mission briefing tailored to the current room's purpose and priorities.")
    return " ".join(parts)
