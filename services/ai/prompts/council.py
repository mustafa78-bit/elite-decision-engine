def council_prompt(topic: str, context: str, agent_roles: list[str]) -> str:
    roles = "\n".join(f"- {role}" for role in agent_roles)
    return f"""You are participating in an AI council for a trading decision engine.

Topic: {topic}

Context:
{context}

Council Members:
{roles}

Provide your analysis and recommendation based on your designated role.
Consider the perspectives of other council members in your response.
"""
