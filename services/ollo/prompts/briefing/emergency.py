def emergency_briefing(context: dict) -> str:
    portfolio = context.get("portfolio_summary", {})
    risk = context.get("risk_metrics", {})
    regime = context.get("market_regime", {})
    council = context.get("council_latest", {})

    parts = ["EMERGENCY BRIEFING."]
    parts.append(f"Portfolio status: {portfolio.get('open_trades', 0)} open trades. Current drawdown: ${portfolio.get('current_drawdown', 0):,.2f}.")
    if risk:
        parts.append(f"Risk metrics: VaR(95) ${risk.get('var_95', 0):,.2f}, expected downside ${risk.get('expected_downside', 0):,.2f}.")
    parts.append(f"Market regime: {regime.get('regime', 'UNKNOWN')}. Volatility: {regime.get('volatility_class', 'UNKNOWN')}.")
    parts.append("This is an emergency briefing. Assess the situation, identify the primary risk factors, and provide recommended protective actions without giving financial advice.")
    return " ".join(parts)
