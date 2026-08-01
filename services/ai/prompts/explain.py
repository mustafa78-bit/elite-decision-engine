def explain_prompt(
    symbol: str,
    side: str,
    score_breakdown: str,
    risk_context: str,
    market_regime: str,
) -> str:
    return f"""You are an explainable AI for a trading decision engine.

Explain the following trading signal:

Symbol: {symbol}
Side: {side}

Score Breakdown:
{score_breakdown}

Risk Context:
{risk_context}

Market Regime:
{market_regime}

Provide a clear, human-readable explanation of:
1. Why this signal was generated
2. The confidence level and key contributing factors
3. Risk considerations
4. Market context
"""
