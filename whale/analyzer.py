from typing import Dict, List, Optional

from whale.models import TransferEvent, WhaleEvent
from whale.timestamp import TimestampHandler
from whale.logging import WhaleLogger


EXCHANGE_ADDRESSES: Dict[str, List[str]] = {
    "binance": [
        "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",
        "0xd551234ae421e3bcba99a0da6d736074f22192ff",
        "0x564286362092d8e7936f0542a1b5c7b1c4bfc8c3",
    ],
    "coinbase": [
        "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
        "0x503828976d22510aad0201ac7ec88293211d23da",
        "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740",
    ],
    "kraken": [
        "0x291c3b1b6e5a36b5035a6e0ba04d80e73d72002e",
        "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13",
    ],
    "bybit": [
        "0x1db92e2eebc8e0c075a02bea49a2935bcd2dfcf4",
    ],
    "okx": [
        "0x6fb624b48d929967be35c3204b28e7ad1d6260e0",
        "0x2b6f9c7f2e6942b4f3e5e5c59e1e57b1ab5a5e5e",
    ],
}

LARGE_TRANSFER_THRESHOLD_USD = 100000.0
MAX_TRANSFER_HISTORY = 10000


class TransferAnalyzer:

    def __init__(self):
        self.logger = WhaleLogger("transfer_analyzer")
        self.large_threshold = LARGE_TRANSFER_THRESHOLD_USD
        self.exchange_addresses = {
            addr: exchange
            for exchange, addresses in EXCHANGE_ADDRESSES.items()
            for addr in addresses
        }
        self.transfer_history: List[TransferEvent] = []

    def is_large_transfer(self, value_usd: float) -> bool:
        if value_usd is None or value_usd < 0:
            return False
        return value_usd >= self.large_threshold

    def classify_direction(self, from_addr: str, to_addr: str) -> str:
        if not from_addr or not to_addr:
            return "WALLET_TO_WALLET"
        from_lower = from_addr.lower()
        to_lower = to_addr.lower()

        if from_lower in self.exchange_addresses:
            return "EXCHANGE_OUTFLOW"
        if to_lower in self.exchange_addresses:
            return "EXCHANGE_INFLOW"

        return "WALLET_TO_WALLET"

    def calculate_confidence(self, transfer: TransferEvent) -> float:
        if transfer is None:
            return 0.5
        score = 0.5

        if transfer.is_large:
            score += 0.2
        if transfer.direction in ("EXCHANGE_INFLOW", "EXCHANGE_OUTFLOW"):
            score += 0.15

        if transfer.amount and transfer.amount > 0:
            str_amount = str(transfer.amount)
            if "." in str_amount:
                precision = len(str_amount.split(".")[-1])
            else:
                precision = 0
            if precision <= 2:
                score -= 0.05
            if precision >= 6:
                score += 0.05

        return min(max(score, 0.0), 1.0)

    def detect_suspicious(self, transfer: TransferEvent, recent_window: int = 300) -> List[str]:
        flags = []

        if transfer.is_large and transfer.direction == "WALLET_TO_WALLET":
            flags.append("LARGE_WALLET_TO_WALLET")

        recent = [
            t for t in self.transfer_history[-50:]
            if (
                t.from_address.lower() == transfer.from_address.lower()
                or t.to_address.lower() == transfer.to_address.lower()
            )
            and abs(
                (
                    TimestampHandler.normalize(transfer.timestamp)
                    - TimestampHandler.normalize(t.timestamp)
                ).total_seconds()
            )
            < recent_window
        ]

        if len(recent) >= 3:
            flags.append("RAPID_SUCCESSIVE_TRANSFERS")

        return flags

    def analyze_transfer(self, transfer: TransferEvent) -> WhaleEvent:
        transfer.direction = self.classify_direction(
            transfer.from_address, transfer.to_address
        )
        transfer.is_large = self.is_large_transfer(transfer.value_usd)
        transfer.confidence = self.calculate_confidence(transfer)
        transfer.is_suspicious = len(self.detect_suspicious(transfer)) > 0

        self.transfer_history.append(transfer)
        if len(self.transfer_history) > MAX_TRANSFER_HISTORY:
            del self.transfer_history[0]

        event = WhaleEvent(
            event_id=f"whale_{len(self.transfer_history)}_{transfer.tx_id[:8]}",
            wallet_address=transfer.from_address,
            event_type="LARGE_TRANSFER" if transfer.is_large else "TRANSFER",
            asset=transfer.asset,
            value_usd=transfer.value_usd,
            confidence=transfer.confidence,
            detected_at=TimestampHandler.utc_now(),
            details={
                "direction": transfer.direction,
                "is_suspicious": transfer.is_suspicious,
                "to_address": transfer.to_address,
                "tx_id": transfer.tx_id,
            },
        )

        if transfer.is_large:
            self.logger.whale_event(
                "LARGE_TRANSFER",
                {
                    "asset": transfer.asset,
                    "value_usd": transfer.value_usd,
                    "direction": transfer.direction,
                },
            )

        return event

    def estimate_usd_value(self, amount: float, price_usd: float) -> float:
        if amount is None or price_usd is None:
            return 0.0
        return amount * price_usd

    def get_recent_large_transfers(
        self, min_value: Optional[float] = None, limit: int = 20
    ) -> List[TransferEvent]:
        if limit <= 0:
            return []
        threshold = min_value if min_value is not None else self.large_threshold
        if threshold < 0:
            threshold = 0
        return [
            t
            for t in self.transfer_history[-limit:]
            if t.value_usd >= threshold
        ]

    def get_transfer_summary(self) -> Dict[str, int]:
        summary = {
            "total": len(self.transfer_history),
            "large": 0,
            "exchange_inflow": 0,
            "exchange_outflow": 0,
            "wallet_to_wallet": 0,
        }
        for t in self.transfer_history:
            if t.is_large:
                summary["large"] += 1
            key = t.direction.lower()
            summary[key] = summary.get(key, 0) + 1
        return summary
