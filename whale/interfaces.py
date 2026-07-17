from typing import Any, Dict, List, Optional

from whale.models import TransferEvent


class WhaleFeatureExtractor:

    def __init__(self):
        self.enabled = True
        self._feature_names = [
            "recent_large_transfer_count",
            "total_large_transfer_volume",
            "whale_wallet_count",
            "total_transfers_analyzed",
        ]

    def extract(self, transfer_history: List[TransferEvent], whale_signals: List) -> Dict[str, Any]:
        recent = [t for t in transfer_history[-10:] if t.is_large]
        features = {
            "recent_large_transfer_count": len(recent),
            "total_large_transfer_volume": sum(t.value_usd for t in recent),
            "whale_wallet_count": len(whale_signals),
            "total_transfers_analyzed": len(transfer_history),
        }
        return {"ok": True, "features": features}

    def get_feature_names(self) -> List[str]:
        return list(self._feature_names)

    def evaluate(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"ok": True, "features": {}, "reason": "use extract() with transfer history and signals"}


class WhaleDataSource:

    def __init__(self):
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def fetch_recent_transfers(self, limit: int = 100) -> List[Dict[str, Any]]:
        return []

    def is_available(self) -> bool:
        return self.connected
