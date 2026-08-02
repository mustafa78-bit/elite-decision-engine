import logging
from typing import List
import database
from database import Signal
from scanner.models import Opportunity

logger = logging.getLogger(__name__)


def generate_signals_from_opportunities(
    opportunities: List[Opportunity],
    timeframe: str = "1h"
) -> int:
    """
    Takes a list of Opportunity objects.
    For each opportunity, creates a new Signal row in the database
    only if there isn't already an OPEN Signal for that exact symbol + side.

    Leaves fields with no real data at their column defaults.
    """
    session = database.get_session()
    created_count = 0
    try:
        for opp in opportunities:
            # Deduplicate against existing OPEN signals with same symbol and side
            existing_open = session.query(Signal).filter(
                Signal.symbol == opp.symbol,
                Signal.side == opp.side,
                Signal.status == "OPEN"
            ).first()

            if existing_open:
                logger.info(
                    "Signal generation skipped for %s %s: an OPEN signal already exists.",
                    opp.symbol, opp.side
                )
                continue

            # Create the signal
            signal = Signal(
                symbol=opp.symbol,
                side=opp.side,
                timeframe=timeframe,
                price=opp.price,
                score=opp.score,
                confidence=opp.confidence,
                trend_score=opp.trend_score,
                status="OPEN",
                reason=opp.reason
            )
            session.add(signal)
            created_count += 1
            logger.info(
                "Created new OPEN Signal for %s %s at price %s, composite score: %s, trend score: %s",
                opp.symbol, opp.side, opp.price, opp.score, opp.trend_score
            )

        if created_count > 0:
            session.commit()
            logger.info("Successfully committed %d new signals to database.", created_count)
    except Exception as e:
        session.rollback()
        logger.error("Failed to generate signals from opportunities: %s", e)
        raise
    finally:
        session.close()

    return created_count
