def command_deck_greeting(context: dict) -> str:
    portfolio = context.get("portfolio_summary", {})
    risk = context.get("risk_metrics", {})

    open_trades = portfolio.get("open_trades", 0)
    total_pnl = portfolio.get("total_pnl", 0)
    win_rate = portfolio.get("win_rate", 0)

    parts = [f"Good to see you, Founder. The Command Deck is operational."]
    parts.append(f"You have {open_trades} open position{'s' if open_trades != 1 else ''}.")
    parts.append(f"Portfolio PnL stands at ${total_pnl:+,.2f} with a {win_rate:.1f}% win rate.")

    if risk:
        parts.append("Risk systems are active and monitoring.")

    parts.append("How would you like to proceed? I can prepare a briefing, review the scanner, or discuss portfolio strategy.")
    return " ".join(parts)
