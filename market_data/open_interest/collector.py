from __future__ import annotations

import logging
from typing import Optional

import requests

from market_data.open_interest.models import OpenInterest, OpenInterestResult, detect_oi_trend

logger = logging.getLogger(__name__)


class OpenInterestCollector:
    BASE_URL = "https://api.hyperliquid.xyz/info"
    MAX_RETRIES = 3

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self._session = requests.Session()

    def fetch_all(self) -> OpenInterestResult:
        payload = {"type": "openInterests"}
        try:
            response = self._session.post(
                self.BASE_URL,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                logger.warning("Unexpected open interests response type: %s", type(data).__name__)
                return OpenInterestResult()
            records: list[OpenInterest] = []
            for entry in data:
                try:
                    records.append(OpenInterest(
                        symbol=str(entry.get("coin", "?")),
                        value=float(entry.get("value", 0)),
                        timestamp=int(entry.get("time", 0)),
                    ))
                except (ValueError, TypeError) as e:
                    logger.debug("Failed to parse OI entry: %s", e)
                    continue
            return OpenInterestResult(records=tuple(records))
        except requests.RequestException as e:
            logger.warning("Failed to fetch open interest: %s", e)
            return OpenInterestResult()

    def fetch_for_symbol(self, symbol: str) -> Optional[OpenInterest]:
        result = self.fetch_all()
        return result.for_symbol(symbol)

    def fetch_with_trend(self, symbol: str, limit: int = 24) -> dict:
        current = self.fetch_for_symbol(symbol)
        if current is None:
            return {"symbol": symbol, "value": 0, "trend": "unknown", "strength": 0.0}
        records = [current]
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
        now = datetime.now(timezone.utc).timestamp()
        ts = oi.timestamp
        if ts > 1e12:
            ts = ts / 1000
        age = now - ts
        max_age = 3600
        if age > max_age:
            return {"fresh": False, "reason": f"OI data is {age:.0f}s old"}
        return {"fresh": True, "age_seconds": int(age)}
