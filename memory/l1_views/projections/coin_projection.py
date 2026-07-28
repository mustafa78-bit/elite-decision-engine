import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable

from database import get_session
from memory.l0_event_log.models import NEXUSEvent
from memory.l1_views.base import BaseProjection
from memory.l1_views.models import CoinView

logger = logging.getLogger(__name__)


class CoinProjection(BaseProjection):
    """Production-grade Coin Projection that maps L0 events to CoinView materialized records."""

    def __init__(self, session_factory: Callable[[], Any] = get_session) -> None:
        self.session_factory = session_factory

        # Metrics tracking
        self.processed_events = 0
        self.updated_coins = 0
        self.ignored_events = 0
        self.failed_updates = 0
        self.total_update_time = 0.0  # seconds

    @property
    def projection_name(self) -> str:
        return "CoinProjection"

    def supported_event_types(self) -> List[str]:
        return [
            "PriceUpdated",
            "TradeExecuted",
            "WhaleActivity",
            "NewsPublished",
            "CalibrationUpdated",
            "TrustUpdated",
            "PatternDetected",
            "MarketRegimeChanged",
        ]

    def apply(self, event: NEXUSEvent) -> None:
        """Applies a single L0 event, updating only affected fields of the CoinView model."""
        event_type = event.event_type
        if event_type not in self.supported_event_types():
            self.ignored_events += 1
            return

        start_time = time.perf_counter()
        session = self.session_factory()
        try:
            payload = event.payload or {}
            symbol = payload.get("symbol")

            # News Published can have related assets list instead of a single symbol
            symbols = [symbol] if symbol else []
            if event_type == "NewsPublished":
                symbols = payload.get("related_assets", [])

            if not symbols:
                self.ignored_events += 1
                return

            for sym in symbols:
                # Query the existing view
                coin = session.query(CoinView).filter(CoinView.symbol == sym).first()
                is_new = False
                if not coin:
                    is_new = True
                    coin = CoinView(
                        coin_id=payload.get("coin_id") or f"coin-{sym.lower()}",
                        symbol=sym,
                        replay_seq_id=event.seq_id,
                        updated_at=event.timestamp,
                    )
                    session.add(coin)

                # Monotonic sequence check for idempotency
                if not is_new and event.seq_id <= coin.replay_seq_id:
                    logger.debug(
                        "Duplicate/older event %s ignored for symbol %s in CoinProjection.",
                        event.seq_id,
                        sym,
                    )
                    continue

                # Apply specific event logic
                if event_type == "PriceUpdated":
                    coin.latest_price = float(payload.get("price", coin.latest_price))
                    # parse last_price_timestamp if any
                    coin.last_price_timestamp = event.timestamp

                elif event_type == "TradeExecuted":
                    # Update timestamp
                    coin.updated_at = event.timestamp

                elif event_type == "WhaleActivity":
                    coin.latest_whale_activity = payload

                elif event_type == "NewsPublished":
                    coin.latest_news_id = payload.get("news_id")
                    coin.latest_news_timestamp = event.timestamp

                elif event_type == "CalibrationUpdated":
                    coin.calibration_version = payload.get("calibration_version", coin.calibration_version)

                elif event_type == "TrustUpdated":
                    coin.trust_score = float(payload.get("trust_score", coin.trust_score))
                    coin.trust_version = payload.get("trust_version", coin.trust_version)

                elif event_type == "PatternDetected":
                    pat = payload.get("pattern")
                    if pat:
                        patterns = list(coin.active_patterns or [])
                        if pat not in patterns:
                            patterns.append(pat)
                        coin.active_patterns = patterns

                elif event_type == "MarketRegimeChanged":
                    coin.market_regime = payload.get("market_regime", coin.market_regime)
                    coin.confidence_score = float(payload.get("confidence_score", coin.confidence_score))

                coin.replay_seq_id = event.seq_id
                coin.updated_at = datetime.now(timezone.utc)
                self.updated_coins += 1

            session.commit()
            self.processed_events += 1
            self.total_update_time += (time.perf_counter() - start_time)
        except Exception as e:
            session.rollback()
            self.failed_updates += 1
            logger.error("Failed to apply event to CoinProjection: %s", e)
            raise
        finally:
            session.close()

    def rebuild(self) -> None:
        """Clears all materialized data in l1_coin_views and resets projection metrics."""
        session = self.session_factory()
        try:
            session.query(CoinView).delete()
            session.commit()
            # Reset metrics
            self.processed_events = 0
            self.updated_coins = 0
            self.ignored_events = 0
            self.failed_updates = 0
            self.total_update_time = 0.0
            logger.info("CoinProjection rebuilt successfully.")
        except Exception as e:
            session.rollback()
            logger.error("Failed to rebuild CoinProjection: %s", e)
            raise
        finally:
            session.close()

    def snapshot(self) -> Dict[str, Any]:
        """Captures a serializable snapshot state of the CoinProjection."""
        session = self.session_factory()
        try:
            coins = session.query(CoinView).all()
            return {
                "coins": [
                    {
                        "coin_id": c.coin_id,
                        "symbol": c.symbol,
                        "latest_price": c.latest_price,
                        "last_price_timestamp": c.last_price_timestamp.isoformat() if c.last_price_timestamp else None,
                        "market_regime": c.market_regime,
                        "trust_score": c.trust_score,
                        "confidence_score": c.confidence_score,
                        "latest_news_id": c.latest_news_id,
                        "latest_news_timestamp": c.latest_news_timestamp.isoformat() if c.latest_news_timestamp else None,
                        "latest_whale_activity": c.latest_whale_activity,
                        "active_patterns": c.active_patterns,
                        "calibration_version": c.calibration_version,
                        "trust_version": c.trust_version,
                        "replay_seq_id": c.replay_seq_id,
                    }
                    for c in coins
                ]
            }
        finally:
            session.close()

    def restore_snapshot(self, state: Dict[str, Any]) -> None:
        """Restores the CoinView table from the serialized snapshot state."""
        session = self.session_factory()
        try:
            # Clear current views
            session.query(CoinView).delete()

            # Insert snapshotted records
            for data in state.get("coins", []):
                last_price_ts = None
                if data.get("last_price_timestamp"):
                    last_price_ts = datetime.fromisoformat(data["last_price_timestamp"])

                news_ts = None
                if data.get("latest_news_timestamp"):
                    news_ts = datetime.fromisoformat(data["latest_news_timestamp"])

                coin = CoinView(
                    coin_id=data["coin_id"],
                    symbol=data["symbol"],
                    latest_price=data["latest_price"],
                    last_price_timestamp=last_price_ts,
                    market_regime=data["market_regime"],
                    trust_score=data["trust_score"],
                    confidence_score=data["confidence_score"],
                    latest_news_id=data["latest_news_id"],
                    latest_news_timestamp=news_ts,
                    latest_whale_activity=data["latest_whale_activity"],
                    active_patterns=data["active_patterns"],
                    calibration_version=data["calibration_version"],
                    trust_version=data["trust_version"],
                    replay_seq_id=data["replay_seq_id"],
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(coin)

            session.commit()
            logger.info("CoinProjection snapshot restored successfully with %d coins.", len(state.get("coins", [])))
        except Exception as e:
            session.rollback()
            logger.error("Failed to restore CoinProjection snapshot: %s", e)
            raise
        finally:
            session.close()

    def validate(self) -> bool:
        """Validates current database entries against sanity constraints."""
        session = self.session_factory()
        try:
            coins = session.query(CoinView).all()
            for c in coins:
                if not c.symbol or len(c.symbol) > 20:
                    return False
                if c.latest_price < 0:
                    return False
            return True
        except Exception:
            return False
        finally:
            session.close()

    def health(self) -> Dict[str, Any]:
        """Returns health diagnostics and tracking metrics."""
        avg_latency = 0.0
        if self.processed_events > 0:
            avg_latency = self.total_update_time / self.processed_events

        return {
            "status": "HEALTHY" if self.failed_updates == 0 else "DEGRADED",
            "processed_events": self.processed_events,
            "updated_coins": self.updated_coins,
            "ignored_events": self.ignored_events,
            "failed_updates": self.failed_updates,
            "average_update_latency": avg_latency,
        }
