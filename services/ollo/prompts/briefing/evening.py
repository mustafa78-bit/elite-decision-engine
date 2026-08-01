def evening_briefing(context: dict) -> str:
    portfolio = context.get("portfolio_summary", {})
    performance = context.get("portfolio_performance", {})
    regime = context.get("market_regime", {})
    risk = context.get("risk_metrics", {})

    parts = ["Prepare the Evening Briefing."]
    parts.append(f"Portfolio: realized PnL ${portfolio.get('realized_pnl', 0):+,.2f}, open PnL ${portfolio.get('open_pnl', 0):+,.2f}.")
    parts.append(f"Total trades closed: {portfolio.get('total_trades', 0)}. Win rate: {portfolio.get('win_rate', 0):.1f}%. Profit factor: {portfolio.get('profit_factor', 0):.2f}.")
    parts.append(f"Market regime: {regime.get('regime', 'UNKNOWN')}.")
    if risk:
        parts.append(f"Max drawdown: {portfolio.get('max_drawdown', 0):,.2f}. VaR(95): {risk.get('var_95', 0):,.2f}.")
    parts.append("Provide an end-of-day briefing summarizing today's performance, key events, and positioning for tomorrow.")
    return " ".join(parts)
