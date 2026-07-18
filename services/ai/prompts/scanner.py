def scanner_prompt(
    symbol: str,
    technical_signals: str,
    volume_analysis: str,
    market_context: str,
) -> str:
    return f"""You are a market scanner AI for a trading decision engine.

Symbol: {symbol}

Technical Signals:
{technical_signals}

Volume Analysis:
{volume_analysis}

Market Context:
{market_context}

Analyze the above data and provide:
1. Signal strength assessment (STRONG, MODERATE, WEAK)
2. Key technical levels
3. Volume confirmation or divergence
4. Overall recommendation
"""
