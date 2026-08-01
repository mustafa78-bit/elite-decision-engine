def morning_briefing(context: dict) -> str:
    portfolio = context.get("portfolio_summary", {})
    performance = context.get("portfolio_performance", {})
    regime = context.get("market_regime", {})
    risk = context.get("risk_metrics", {})
    council = context.get("council_latest", {})
    scanner = context.get("scanner_signals", {})

    parts = ["Prepare the Morning Briefing."]
    parts.append(f"Portfolio: {portfolio.get('open_trades', 0)} open trades, total PnL ${portfolio.get('total_pnl', 0):+,.2f}, win rate {portfolio.get('win_rate', 0):.1f}%.")
    parts.append(f"Market regime: {regime.get('regime', 'UNKNOWN')} with {regime.get('trend', 'NEUTRAL')} trend ({regime.get('trend_strength', 'UNKNOWN')} strength). Volatility class: {regime.get('volatility_class', 'UNKNOWN')}.")
    if scanner:
        parts.append(f"Scanner reports {scanner.get('signal_count', 0)} signals.")
    if council:
        parts.append(f"AI Council: {council.get('agent_count', 0)} agents active.")
    parts.append("Provide a concise morning briefing covering portfolio status, market conditions, and the day's strategic outlook.")
    return " ".join(parts)
