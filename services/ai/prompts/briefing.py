def briefing_prompt(market_summary: str, portfolio_status: str) -> str:
    return f"""You are a market briefing assistant for a trading decision engine.

Market Summary:
{market_summary}

Portfolio Status:
{portfolio_status}

Provide a concise market briefing covering:
1. Current market regime and trend
2. Key levels to watch
3. Portfolio exposure recommendations
4. Risk considerations
"""
