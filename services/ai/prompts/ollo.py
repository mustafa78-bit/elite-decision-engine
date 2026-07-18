def ollo_prompt(query: str, conversation_history: str = "") -> str:
    if conversation_history:
        return f"""You are OLLO, an AI trading assistant for the Elite Decision Engine.

Previous conversation:
{conversation_history}

User query: {query}

Respond helpfully and concisely. Focus on trading, portfolio management,
and market analysis topics.
"""
    return f"""You are OLLO, an AI trading assistant for the Elite Decision Engine.

User query: {query}

Respond helpfully and concisely. Focus on trading, portfolio management,
and market analysis topics.
"""
