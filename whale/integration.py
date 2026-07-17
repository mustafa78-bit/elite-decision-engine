from typing import Any, Dict, List, Optional

from whale.models import WhaleEvent, TransferEvent
from whale.analyzer import TransferAnalyzer
from whale.smart_money import SmartMoneyDetector
from whale.timestamp import TimestampHandler
from whale.logging import WhaleLogger
from whale.interfaces import WhaleFeatureExtractor

MAX_WHALE_EVENTS = 10000


class WhaleIntegration:

    def __init__(self):
        self.analyzer = TransferAnalyzer()
        self.smart_money = SmartMoneyDetector()
        self.feature_extractor = WhaleFeatureExtractor()
        self.logger = WhaleLogger("whale_integration")
        self.enabled = True
        self.events: List[WhaleEvent] = []
        self.seen_tx_ids: set = set()

    def process_transfer(self, transfer: TransferEvent) -> Optional[WhaleEvent]:
        if not self.enabled or transfer is None:
            return None

        if transfer.tx_id in self.seen_tx_ids:
            self.logger.info(f"Duplicate transfer suppressed: {transfer.tx_id}")
            return None
        self.seen_tx_ids.add(transfer.tx_id)
        if len(self.seen_tx_ids) > MAX_WHALE_EVENTS * 2:
            self.seen_tx_ids.clear()

        event = self.analyzer.analyze_transfer(transfer)
        self.smart_money.process_transfer(transfer)

        if event:
            self.events.append(event)
            if len(self.events) > MAX_WHALE_EVENTS:
                del self.events[0]
            self.logger.whale_event(event.event_type, {"tx_id": transfer.tx_id, "value_usd": transfer.value_usd})

        return event

    def get_whale_signals(self) -> List[WhaleEvent]:
        if not self.enabled:
            return []
        return self.smart_money.get_whale_signals()

    def get_features(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"whale_enabled": False}

        extractor_result = self.feature_extractor.extract(
            self.analyzer.transfer_history,
            self.smart_money.get_whale_signals(),
        )

        return {"whale_enabled": True, "whale_features": extractor_result["features"]}

    def get_contribution_log(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": e.event_id,
                "type": e.event_type,
                "value_usd": e.value_usd,
                "confidence": e.confidence,
                "detected_at": TimestampHandler.format_timestamp(e.detected_at),
            }
            for e in self.events[-20:]
        ]

    def evaluate(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "whale_available": False}
        return {
            "ok": True,
            "whale_available": True,
            "features": self.get_features(),
            "signals": len(self.get_whale_signals()),
            "events_logged": len(self.events),
        }
