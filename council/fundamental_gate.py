"""Fundamental veto gate for the REAL execution path.

Context: execution/pipeline.py's DecisionPipeline (the only place that
actually opens a paper trade) scores signals from purely technical/price
data (scoring/scoring_engine.py's trend/volume/btc/mtf/risk) -- it has zero
news/macro/whale awareness. council/consensus.py's ConsensusEngine has that
awareness (NewsAgent/WhaleAgent/MacroAgent) but is advisory-only, never
wired into a real trade decision.

This module is the bridge, built deliberately narrow and conservative:
  - Only the 3 fundamental/context agents run here (News, Whale, Macro) --
    NOT Technical/Trend (redundant with ScoringEngine's own technical
    signals, would double-count) and NOT Risk (a separate, already-existing
    gate in RiskManager with a different, portfolio-level meaning).
  - This is a VETO gate, not a scoring input: it can only block a trade
    ScoringEngine/ConfidenceEngine already approved, never add points to
    approve one they rejected. Keeps this a hard safety net, not a second
    optimization surface.
  - Requires a MAJORITY (2 of 3) of the fundamental agents to independently
    and strongly disagree with the trade direction before vetoing --
    a single agent's disagreement is not enough. Fundamental signals are
    noisier and less directly predictive than price action for the
    short/intraday timeframes this system trades (see council/consensus.py's
    DEFAULT_WEIGHTS rebalance comment) -- this gate exists to catch a
    genuinely alarming confluence (bad news + whale selling + extreme
    funding all at once), not to second-guess every trade.
  - Exception: a single-agent emergency override exists for Whale/Macro
    only (not News -- LLM-derived sentiment, noisier by this project's own
    repeated observation) at an EXTREME confidence
    (_EMERGENCY_OVERRIDE_CONFIDENCE_THRESHOLD). 742+ real signals with zero
    quorum-based vetoes (2026-08-19 audit) showed the 2-of-3 requirement
    alone was too conservative to ever fire in practice -- this override
    lets one genuinely extreme reading (not just an ordinary confident one)
    still block a trade without waiting for a second agent to independently
    agree.
  - Fails OPEN on any error or missing data (never veto because a data
    source was unavailable -- that would make an outage more disruptive
    than the thing it's meant to catch).
  - Uses market.services.MarketDataService.get_asset(), which already goes
    through market.intelligence.service.IntelligenceService's per-symbol
    cache -- safe to call on every signal evaluation without reproducing
    the rate-limit storms fixed elsewhere today.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import NamedTuple

from council.base import DIRECTION_BEARISH

logger = logging.getLogger(__name__)

# An agent's disagreement only counts toward a veto above this confidence --
# keeps a weak/uncertain reading from contributing to blocking a trade.
# Was 0.6 -- live-observed 2026-08-19 across 742+ real signals, this gate
# had triggered zero times, not because nothing alarming ever happened but
# because the bar was too high for how noisy News/Whale/Macro confidence
# readings actually are in practice (founder + independent review agreed).
# Lowered to 0.45 -- still below "more likely than not" (0.5), so a weak
# reading still doesn't count, but a real majority-confidence contradiction
# now does.
_CONTRADICTION_CONFIDENCE_THRESHOLD = 0.45
# How many of the 3 fundamental agents must independently, strongly
# contradict the trade direction before it's actually vetoed.
_VETO_QUORUM = 2

# Emergency single-agent override: if Whale or Macro alone reports an
# EXTREME bearish confidence, veto without waiting for a second agent to
# agree. Deliberately excludes News -- it's the one fundamental agent whose
# signal is LLM-derived sentiment (market/intelligence/news.py), which this
# project has repeatedly found noisier/less consistent than Whale's real
# trade data or Macro's rule-based funding/OI/fear-greed inputs. A single
# noisy News reading should not be able to unilaterally block a trade the
# same way a single Whale/Macro reading can.
_EMERGENCY_OVERRIDE_CONFIDENCE_THRESHOLD = 0.85
_EMERGENCY_OVERRIDE_AGENTS = frozenset({"Whale", "Macro"})


class FundamentalVetoResult(NamedTuple):
    vetoed: bool
    reason: str | None


def check_fundamental_veto(symbol: str, side: str, timeframe: str = "1h") -> FundamentalVetoResult:
    """Returns whether News/Whale/Macro intelligence strongly contradicts a
    trade about to be approved. Never raises -- any failure fails open
    (vetoed=False)."""
    try:
        from market.services import MarketDataService

        mds = MarketDataService()
        asset = mds.get_asset(symbol, timeframe=timeframe)
        bundle = asset.intelligence
        if bundle is None:
            return FundamentalVetoResult(False, None)

        from council.macro_agent import MacroAgent
        from council.news_agent import NewsAgent
        from council.whale_agent import WhaleAgent

        # A minimal stand-in for TradingSignal -- these agents only read
        # .symbol/.side off it.
        signal = SimpleNamespace(symbol=symbol, side=side)

        reports = [
            NewsAgent().evaluate(signal=signal, intelligence_bundle=bundle),
            WhaleAgent().evaluate(signal=signal, intelligence_bundle=bundle),
            MacroAgent().evaluate(signal=signal, intelligence_bundle=bundle),
        ]

        emergency = [
            r for r in reports
            if r.agent_name in _EMERGENCY_OVERRIDE_AGENTS
            and r.direction == DIRECTION_BEARISH
            and r.confidence > _EMERGENCY_OVERRIDE_CONFIDENCE_THRESHOLD
        ]
        if emergency:
            r = emergency[0]
            reason = f"Emergency override: {r.agent_name} reports extreme confidence ({r.confidence:.2f}) contradicting this {side} on {symbol}"
            logger.info("Fundamental veto: %s", reason)
            return FundamentalVetoResult(True, reason)

        contradicting = [
            r for r in reports
            if r.direction == DIRECTION_BEARISH and r.confidence > _CONTRADICTION_CONFIDENCE_THRESHOLD
        ]

        if len(contradicting) >= _VETO_QUORUM:
            names = ", ".join(r.agent_name for r in contradicting)
            reason = f"{len(contradicting)}/3 fundamental agents ({names}) strongly contradict this {side} on {symbol}"
            logger.info("Fundamental veto: %s", reason)
            return FundamentalVetoResult(True, reason)

        return FundamentalVetoResult(False, None)
    except Exception as e:
        logger.warning("Fundamental veto check failed for %s, failing open: %s", symbol, e)
        return FundamentalVetoResult(False, None)
