"""Convert Scanner opportunities into persisted OPEN Signal rows.

Dedupes against already-open signals for the same symbol+side so a
symbol/side combination only ever has one live OPEN Signal at a time.
"""

from __future__ import annotations

import logging

from database import Signal, get_session
from scanner.models import Opportunity

logger = logging.getLogger(__name__)


def generate_signals(
    opportunities: list[Opportunity],
    timeframe: str = "1h",
    session=None,
) -> int:
    """Create a new OPEN Signal row for each opportunity that doesn't already
    have an OPEN Signal for the same symbol+side.

    Returns the number of new signals created.
    """
    owns_session = session is None
    session = session or get_session()
    created = 0
    try:
        for opp in opportunities:
            existing = (
                session.query(Signal)
                .filter(
                    Signal.symbol == opp.symbol,
                    Signal.side == opp.side,
                    Signal.status == "OPEN",
                )
                .first()
            )
            if existing is not None:
                continue

            signal = Signal(
                symbol=opp.symbol,
                side=opp.side,
                timeframe=timeframe,
                price=opp.price,
                score=opp.score,
                confidence=opp.confidence,
                trend_score=opp.trend_score,
                status="OPEN",
            )
            session.add(signal)
            created += 1

        if owns_session:
            session.commit()
        else:
            session.flush()
    finally:
        if owns_session:
            session.close()

    logger.info(
        "Signal generator: created %d new signal(s) from %d opportunity(ies)",
        created, len(opportunities),
    )
    return created
