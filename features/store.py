from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class FeatureEntry:
    symbol: str
    feature_type: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None


class FeatureStore:
    """In-memory feature store with TTL-based expiration.

    Stores computed features (indicators, volatility, volume, market state)
    keyed by ``(symbol, feature_type)``.
    """

    def __init__(self, max_size: int = 5000) -> None:
        self._store: dict[tuple[str, str], FeatureEntry] = {}
        self._max_size = max_size

    def _prune_expired(self) -> None:
        now = time.time()
        expired = [
            key for key, entry in self._store.items()
            if entry.ttl is not None and (now - entry.timestamp) > entry.ttl
        ]
        for k in expired:
            self._store.pop(k, None)

    def set(self, symbol: str, feature_type: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store a feature with optional TTL in seconds."""
        self._prune_expired()
        key = (symbol.upper(), feature_type)
        if len(self._store) >= self._max_size and key not in self._store:
            oldest_key = min(self._store.keys(), key=lambda k: self._store[k].timestamp)
            self._store.pop(oldest_key, None)

        self._store[key] = FeatureEntry(
            symbol=symbol.upper(),
            feature_type=feature_type,
            value=value,
            ttl=ttl,
        )
        logger.debug("Feature stored: %s %s = %s", symbol, feature_type, value)

    def get(self, symbol: str, feature_type: str) -> Optional[Any]:
        """Get a feature value, or None if expired or missing."""
        key = (symbol.upper(), feature_type)
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.ttl is not None and (time.time() - entry.timestamp) > entry.ttl:
            self._store.pop(key, None)
            return None
        return entry.value

    def get_all(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """Get all non-expired features, optionally filtered by symbol."""
        result: dict[str, Any] = {}
        now = time.time()
        for (sym, ftype), entry in list(self._store.items()):
            if symbol and sym != symbol.upper():
                continue
            if entry.ttl is not None and (now - entry.timestamp) > entry.ttl:
                self._store.pop((sym, ftype), None)
                continue
            result[ftype] = entry.value
        return result

    def set_batch(self, symbol: str, features: dict[str, Any], ttl: Optional[float] = None) -> None:
        """Store multiple features for a symbol at once."""
        for ftype, value in features.items():
            self.set(symbol, ftype, value, ttl)

    def delete(self, symbol: str, feature_type: str) -> bool:
        """Delete a feature entry."""
        key = (symbol.upper(), feature_type)
        return self._store.pop(key, None) is not None

    def clear(self, symbol: Optional[str] = None) -> int:
        """Clear features, optionally for a specific symbol."""
        if symbol is None:
            count = len(self._store)
            self._store.clear()
            return count
        sym = symbol.upper()
        keys = [k for k in self._store if k[0] == sym]
        for k in keys:
            self._store.pop(k)
        return len(keys)

    def count(self) -> int:
        return len(self._store)

    def snapshot(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """Get all non-expired features as a flat dict."""
        all_features = self.get_all(symbol)
        return {
            "symbol": symbol or "all",
            "feature_count": len(all_features),
            "features": all_features,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
