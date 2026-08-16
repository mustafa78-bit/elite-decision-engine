from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from datetime import UTC
from typing import Optional

import requests

from market_data.open_interest.models import OpenInterest, OpenInterestResult, detect_oi_trend

logger = logging.getLogger(__name__)


class OpenInterestCollector:
    BASE_URL = "https://api.hyperliquid.xyz/info"
    MAX_RETRIES = 3

    # Same bulk "every symbol in one call" endpoint as
    # market_data/funding/collector.py's FundingCollector -- see that
    # class's _CACHE_TTL_SECONDS comment for why this must be a class-level
    # (not per-instance) cache and why 30s is safe. This does NOT cache
    # self._history / fetch_with_trend()'s trend derivation below -- only
    # the raw network snapshot fetch_all() itself would otherwise repeat.
    _CACHE_TTL_SECONDS = 30
    _cache: tuple[float, OpenInterestResult] | None = None

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self._session = requests.Session()
        # Hyperliquid's info API has no historical open-interest endpoint
        # (unlike fundingHistory for funding rates) -- fetch_with_trend()
        # accumulates real history across calls instead, so a trend becomes
        # available once this collector has been called at least twice for
        # a given symbol (still "unknown" on the very first call, which is
        # honest -- there's genuinely no prior data point yet).
        self._history: dict[str, deque[OpenInterest]] = defaultdict(lambda: deque(maxlen=24))

    def fetch_all(self) -> OpenInterestResult:
        cached = OpenInterestCollector._cache
        if cached is not None and time.time() - cached[0] < OpenInterestCollector._CACHE_TTL_SECONDS:
            return cached[1]

        # "openInterests" is not a real Hyperliquid info type -- every call
        # here 422'd and this collector has never actually returned data.
        # metaAndAssetCtxs (the same bulk endpoint market_data/funding/
        # collector.py's FundingCollector.fetch_all() uses) returns
        # [meta, assetCtxs] where meta["universe"][i]["name"] and
        # assetCtxs[i]["openInterest"] describe the same asset at the same
        # index. No per-entry timestamp is provided by this endpoint -- it's
        # a live snapshot, so "now" is the honest fetch timestamp.
        payload = {"type": "metaAndAssetCtxs"}
        try:
            response = self._session.post(
                self.BASE_URL,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list) or len(data) != 2:
                logger.warning("Unexpected metaAndAssetCtxs response shape: %s", type(data).__name__)
                return OpenInterestResult()
            meta, asset_ctxs = data[0], data[1]
            universe = meta.get("universe", []) if isinstance(meta, dict) else []
            if not isinstance(asset_ctxs, list) or not isinstance(universe, list):
                logger.warning("Unexpected metaAndAssetCtxs meta/assetCtxs types")
                return OpenInterestResult()
            now = int(time.time())
            records: list[OpenInterest] = []
            for asset, ctx in zip(universe, asset_ctxs):
                if not isinstance(asset, dict) or not isinstance(ctx, dict):
                    continue
                symbol = asset.get("name")
                oi = ctx.get("openInterest")
                if symbol is None or oi is None:
                    continue
                try:
                    records.append(OpenInterest(
                        symbol=str(symbol),
                        value=float(oi),
                        timestamp=now,
                    ))
                except (ValueError, TypeError) as e:
                    logger.debug("Failed to parse OI entry: %s", e)
                    continue
            result = OpenInterestResult(records=tuple(records))
            OpenInterestCollector._cache = (time.time(), result)
            return result
        except requests.RequestException as e:
            logger.warning("Failed to fetch open interest: %s", e)
            return OpenInterestResult()

    def fetch_for_symbol(self, symbol: str) -> OpenInterest | None:
        result = self.fetch_all()
        return result.for_symbol(symbol)

    def fetch_with_trend(self, symbol: str, limit: int = 24) -> dict:
        current = self.fetch_for_symbol(symbol)
        if current is None:
            return {"symbol": symbol, "value": 0, "trend": "unknown", "strength": 0.0}
        history = self._history[symbol]
        history.append(current)
        records = list(history)[-limit:]
        trend = detect_oi_trend(records)
        return {
            "symbol": symbol,
            "value": current.value,
            "trend": trend["trend"],
            "strength": trend["strength"],
            "timestamp": current.timestamp,
        }

    def check_freshness(self, symbol: str) -> dict:
        oi = self.fetch_for_symbol(symbol)
        if oi is None:
            return {"fresh": False, "reason": "No OI data available"}
        from datetime import datetime, timezone
        now = datetime.now(UTC).timestamp()
        ts = oi.timestamp
        if ts > 1e12:
            ts = ts / 1000
        age = now - ts
        max_age = 3600
        if age > max_age:
            return {"fresh": False, "reason": f"OI data is {age:.0f}s old"}
        return {"fresh": True, "age_seconds": int(age)}
