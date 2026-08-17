"""Optional AI second-opinion on an already-computed council consensus.

Deliberately NOT a BaseAgent / not part of ConsensusEngine._compute_consensus()'s
weighted vote. The council's actual decision math stays 100% rule-based and
deterministic -- a trading-relevant verdict must not depend on an external
API's availability, latency, or occasional hallucination. This module runs
strictly AFTER the real consensus is already final, purely as commentary:
it can flag something worth a human's attention, but it can never change
consensus_direction, consensus_score, or risk_veto.

Also opt-in, not automatic -- see api/routes/council.py's `ai_opinion` query
param -- so the default /council/evaluate path stays exactly as fast/cheap
as it was before this module existed, and this doesn't add a new automatic
NVIDIA consumer to a system already coordinated to stay within its rate
limit (see services/ai/provider_factory.get_shared_provider()).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from services.ai.prompts.council import council_advisory_prompt

if TYPE_CHECKING:
    from council.consensus import CouncilReport

logger = logging.getLogger(__name__)


def get_ai_opinion(report: "CouncilReport") -> str | None:
    """Returns a short qualitative sanity-check string, or None if the AI
    call fails/is unavailable -- a missing opinion must never block or
    degrade the council report it's attached to."""
    try:
        from services.ai.provider_factory import get_shared_provider

        agent_summaries = [
            f"{r.agent_name}: {r.direction} (confidence {r.confidence:.2f}) -- "
            f"{'; '.join(r.reasoning) if r.reasoning else 'no reasoning provided'}"
            for r in report.agent_reports
        ]

        prompt = council_advisory_prompt(
            symbol=report.symbol,
            side=report.side,
            consensus_direction=report.consensus_direction,
            consensus_score=report.consensus_score,
            agreement_level=report.agreement_level,
            agent_summaries=agent_summaries,
        )

        provider = get_shared_provider()
        result = provider.generate(prompt)
        if result.error or not result.content:
            logger.info("AI council opinion unavailable for %s: %s", report.symbol, result.error)
            return None
        return result.content.strip()
    except Exception as e:
        logger.warning("AI council opinion failed for %s: %s", report.symbol, e)
        return None
