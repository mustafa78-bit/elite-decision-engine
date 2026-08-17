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


def council_advisory_prompt(
    symbol: str,
    side: str,
    consensus_direction: str,
    consensus_score: float,
    agreement_level: str,
    agent_summaries: list[str],
) -> str:
    """Builds a prompt asking for a qualitative sanity-check on a consensus
    the rule-based council has ALREADY computed -- this is deliberately not
    a vote, and the response must never be treated as changing the
    consensus_direction/consensus_score/risk_veto (see
    council/ai_advisor.py::get_ai_opinion()'s docstring for why)."""
    agents_block = "\n".join(f"- {s}" for s in agent_summaries)
    return f"""You are a second, independent pair of eyes reviewing a completed
trading-council analysis. A rule-based multi-agent system has ALREADY reached
a verdict below -- your job is not to vote or override it, only to sanity-check
it and flag anything a purely rule-based system might miss (e.g. a
contradiction between agents, an unusually thin agreement margin, a
consideration none of the agents' reasoning touches on).

Symbol: {symbol} ({side})
Rule-based consensus: {consensus_direction} (score {consensus_score:.2f}, agreement: {agreement_level})

Individual agent findings:
{agents_block}

In 2-3 sentences, give a brief qualitative take: does this consensus look
sound, or is there something worth a human's attention before acting on it?
Do not restate the agents' findings -- add something they didn't already say.
"""
