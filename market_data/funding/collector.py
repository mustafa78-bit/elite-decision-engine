from __future__ import annotations

import logging
from typing import Any, Optional

import requests

from market_data.funding.models import FundingRate, FundingResult, _FRESHNESS_THRESHOLD_SECONDS, validate_funding_rate

logger = logging.getLogger(__name__)


class FundingCollector:
    BASE_URL = "https://api.hyperliquid.xyz/info"
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2.0

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self._session = requests.Session()

    def fetch_all(self) -> FundingResult:
        payload = {"type": "allMids"}
        try:
            response = self._session.post(
                self.BASE_URL,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                logger.warning("Unexpected allMids response type: %s", type(data).__name__)
                return FundingResult()
            rates: list[FundingRate] = []
            for symbol, mid in data.items():
                rates.append(FundingRate(
                    symbol=str(symbol),
                    rate=float(mid) if isinstance(mid, (int, float)) else 0.0,
                    timestamp=0,
                    next_funding_time=0,
                ))
            return FundingResult(rates=tuple(rates))
        except requests.RequestException as e:
            logger.warning("Failed to fetch funding data: %s", e)
            return FundingResult()

    def fetch_for_symbol(self, symbol: str) -> Optional[FundingRate]:
        result = self.fetch_all()
        return result.rate_for(symbol)

    def fetch_funding_history(self, symbol: str, limit: int = 100) -> FundingResult:
        payload = {
            "type": "fundingHistory",
            "req": {
                "coin": symbol.replace("USDT", ""),
                "limit": limit,
            },
        }
        try:
            response = self._session.post(
                self.BASE_URL,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                logger.warning("Unexpected funding history response type: %s", type(data).__name__)
                return FundingResult()
            rates: list[FundingRate] = []
            for entry in data:
                try:
                    rate = FundingRate(
                        symbol=symbol,
                        rate=float(entry.get("fundingRate", 0)),
                        timestamp=int(entry.get("time", 0)),
                        next_funding_time=int(entry.get("nextFundingTime", 0)),
                        interval_hours=float(entry.get("interval", 8)),
                    )
                    errors = validate_funding_rate(rate)
                    if errors:
                        logger.debug("Skipping invalid funding entry for %s: %s", symbol, errors)
                        continue
                    rates.append(rate)
                except (ValueError, TypeError) as e:
                    logger.debug("Failed to parse funding entry for %s: %s", symbol, e)
                    continue
            return FundingResult(rates=tuple(rates))
        except requests.RequestException as e:
            logger.warning("Failed to fetch funding history for %s: %s", symbol, e)
            return FundingResult()

    def check_freshness(self, symbol: str) -> dict:
        result = self.fetch_funding_history(symbol, limit=1)
        if result.empty:
            return {"fresh": False, "reason": "No funding data available"}
        rate = result.rates[0]
        if result.is_fresh:
            return {"fresh": True, "age_seconds": 0}
        return {"fresh": False, "reason": "Funding data is stale"}
