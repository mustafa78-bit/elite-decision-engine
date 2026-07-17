from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from whale.models import WalletActivity, WhaleEvent, TransferEvent
from whale.timestamp import TimestampHandler
from whale.logging import WhaleLogger


@dataclass
class SmartMoneyWallet:
    address: str
    reputation_score: float = 50.0
    total_volume_usd: float = 0.0
    total_transfers: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    behavior_type: str = "UNKNOWN"
    accumulation_score: float = 0.0
    distribution_score: float = 0.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "reputation_score": self.reputation_score,
            "total_volume_usd": self.total_volume_usd,
            "total_transfers": self.total_transfers,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "behavior_type": self.behavior_type,
            "accumulation_score": self.accumulation_score,
            "distribution_score": self.distribution_score,
            "tags": list(self.tags),
        }


class WalletReputation:

    BASE_SCORE = 50.0

    def __init__(self):
        self.wallets: Dict[str, SmartMoneyWallet] = {}
        self.logger = WhaleLogger("wallet_reputation")

    def get_or_create_wallet(self, address: str) -> SmartMoneyWallet:
        if address not in self.wallets:
            self.wallets[address] = SmartMoneyWallet(address=address)
        return self.wallets[address]

    def update_from_transfer(self, transfer: TransferEvent) -> None:
        wallet = self.get_or_create_wallet(transfer.from_address)
        wallet.total_volume_usd += transfer.value_usd
        wallet.total_transfers += 1
        candidates = [dt for dt in [wallet.last_seen, transfer.timestamp] if dt is not None]
        wallet.last_seen = max(candidates) if candidates else transfer.timestamp
        if wallet.first_seen is None:
            wallet.first_seen = transfer.timestamp

        if transfer.is_large:
            wallet.reputation_score = min(100.0, wallet.reputation_score + 1.0)
            self.logger.info(f"Reputation +1 for {transfer.from_address[:8]} (large transfer)")

    def calculate_score(self, address: str) -> float:
        wallet = self.wallets.get(address)
        if wallet is None:
            return self.BASE_SCORE
        return wallet.reputation_score


class SmartMoneyDetector:

    def __init__(self):
        self.reputation = WalletReputation()
        self.wallet_activities: Dict[str, WalletActivity] = {}
        self.transfers: List[TransferEvent] = []
        self.logger = WhaleLogger("smart_money_detector")
        self.repeated_windows: Dict[str, int] = {}

    def _assign_tags(self, address: str) -> None:
        wallet = self.wallet_activities.get(address)
        if wallet is None:
            return
        wallet.tags = []
        if wallet.behavior_type == "WHALE":
            wallet.tags.append("high_volume")
        if wallet.behavior_type == "ACCUMULATOR":
            wallet.tags.append("accumulator")
        if wallet.behavior_type == "DISTRIBUTOR":
            wallet.tags.append("distributor")
        if wallet.total_volume_usd >= 1_000_000:
            wallet.tags.append("million_plus")
        if wallet.transfer_count >= 5:
            wallet.tags.append("frequent_trader")
        if wallet.total_volume_usd >= 100_000 and wallet.total_volume_usd < 1_000_000:
            wallet.tags.append("mid_volume")
        if wallet.transfer_count >= 20:
            wallet.tags.append("veteran")
        if wallet.reputation_score >= 80:
            wallet.tags.append("high_reputation")

    def process_transfer(self, transfer: TransferEvent) -> Optional[WhaleEvent]:
        self.reputation.update_from_transfer(transfer)
        self.transfers.append(transfer)

        for addr in [transfer.from_address, transfer.to_address]:
            if addr not in self.wallet_activities:
                self.wallet_activities[addr] = WalletActivity(
                    wallet_address=addr,
                    first_seen=transfer.timestamp,
                    last_seen=transfer.timestamp,
                )
            else:
                self.wallet_activities[addr].last_seen = max(
                    self.wallet_activities[addr].last_seen,
                    transfer.timestamp,
                )
            self.wallet_activities[addr].total_volume_usd += transfer.value_usd
            self.wallet_activities[addr].transfer_count += 1

        self._assign_tags(transfer.from_address)
        self._assign_tags(transfer.to_address)

        events = []

        acc_event = self.detect_accumulation(transfer.to_address)
        if acc_event:
            events.append(acc_event)
            self.logger.whale_event("ACCUMULATION_DETECTED", {"address": transfer.to_address[:8]})

        dist_event = self.detect_distribution(transfer.from_address)
        if dist_event:
            events.append(dist_event)
            self.logger.whale_event("DISTRIBUTION_DETECTED", {"address": transfer.from_address[:8]})

        repeat_event = self.track_repeated_activity(transfer)
        if repeat_event:
            events.append(repeat_event)
            self.logger.whale_event("REPEATED_ACTIVITY", {"pair": f"{transfer.from_address[:8]}_{transfer.to_address[:8]}"})

        return events[0] if events else None

    def detect_accumulation(self, address: str) -> Optional[WhaleEvent]:
        wallet = self.wallet_activities.get(address)
        if wallet is None:
            return None

        incoming = [
            t
            for t in self.transfers
            if t.to_address.lower() == address.lower()
        ]
        total_incoming = sum(t.value_usd for t in incoming)

        if total_incoming >= 500000 and len(incoming) >= 2:
            wallet.behavior_type = "ACCUMULATOR"
            return WhaleEvent(
                event_id=f"acc_{address[:8]}_{int(TimestampHandler.utc_now().timestamp())}",
                wallet_address=address,
                event_type="ACCUMULATION",
                asset="MULTI",
                value_usd=total_incoming,
                confidence=0.6,
                detected_at=TimestampHandler.utc_now(),
                details={"incoming_count": len(incoming)},
            )
        return None

    def detect_distribution(self, address: str) -> Optional[WhaleEvent]:
        wallet = self.wallet_activities.get(address)
        if wallet is None:
            return None

        outgoing = [
            t
            for t in self.transfers
            if t.from_address.lower() == address.lower()
        ]
        total_outgoing = sum(t.value_usd for t in outgoing)

        if total_outgoing >= 500000 and len(outgoing) >= 2:
            wallet.behavior_type = "DISTRIBUTOR"
            return WhaleEvent(
                event_id=f"dist_{address[:8]}_{int(TimestampHandler.utc_now().timestamp())}",
                wallet_address=address,
                event_type="DISTRIBUTION",
                asset="MULTI",
                value_usd=total_outgoing,
                confidence=0.6,
                detected_at=TimestampHandler.utc_now(),
                details={"outgoing_count": len(outgoing)},
            )
        return None

    def track_repeated_activity(self, transfer: TransferEvent) -> Optional[WhaleEvent]:
        key = f"{transfer.from_address}_{transfer.to_address}"
        self.repeated_windows[key] = self.repeated_windows.get(key, 0) + 1

        if self.repeated_windows[key] >= 3:
            return WhaleEvent(
                event_id=f"repeat_{key[:16]}_{int(TimestampHandler.utc_now().timestamp())}",
                wallet_address=transfer.from_address,
                event_type="REPEATED_ACTIVITY",
                asset=transfer.asset,
                value_usd=transfer.value_usd * self.repeated_windows[key],
                confidence=0.7,
                detected_at=TimestampHandler.utc_now(),
                details={
                    "pair_key": key,
                    "repeat_count": self.repeated_windows[key],
                    "to_address": transfer.to_address,
                },
            )
        return None

    def classify_behavior(self, address: str) -> str:
        wallet = self.wallet_activities.get(address)
        if wallet is None:
            return "UNKNOWN"
        if wallet.transfer_count >= 10 and wallet.total_volume_usd >= 1_000_000:
            wallet.behavior_type = "WHALE"
            self.logger.whale_event("WHALE_CLASSIFIED", {"address": address[:8], "volume": wallet.total_volume_usd})
            return "WHALE"
        if wallet.transfer_count >= 5 and wallet.total_volume_usd >= 500_000:
            wallet.behavior_type = "SMART_MONEY"
            self.logger.whale_event("SMART_MONEY_CLASSIFIED", {"address": address[:8], "volume": wallet.total_volume_usd})
            return "SMART_MONEY"
        if wallet.transfer_count >= 3:
            wallet.behavior_type = "ACTIVE"
            return "ACTIVE"
        wallet.behavior_type = "OBSERVER"
        return "OBSERVER"

    def get_whale_signals(self) -> List[WhaleEvent]:
        signals = []
        for address in self.wallet_activities:
            classification = self.classify_behavior(address)
            if classification in ("WHALE", "SMART_MONEY"):
                wallet = self.wallet_activities[address]
                signals.append(
                    WhaleEvent(
                        event_id=f"signal_{address[:8]}",
                        wallet_address=address,
                        event_type=f"{classification}_DETECTED",
                        asset="MULTI",
                        value_usd=wallet.total_volume_usd,
                        confidence=min(100.0, wallet.total_volume_usd / 10000) / 100.0,
                        detected_at=TimestampHandler.utc_now(),
                        details={
                            "classification": classification,
                            "transfer_count": wallet.transfer_count,
                            "reputation": self.reputation.calculate_score(address),
                        },
                    )
                )
        return signals
