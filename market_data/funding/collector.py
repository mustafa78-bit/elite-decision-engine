from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import requests

from market_data.funding.models import _FRESHNESS_THRESHOLD_SECONDS, FundingRate, FundingResult, validate_funding_rate

logger = logging.getLogger(__name__)


class FundingCollector:
    BASE_URL = "https://api.hyperliquid.xyz/info"
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2.0

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self._session = requests.Session()

    def fetch_all(self) -> FundingResult:
        # metaAndAssetCtxs is Hyperliquid's bulk endpoint for current
        # per-asset context (funding, mark price, open interest, ...) --
        # returns [meta, assetCtxs] where meta["universe"][i]["name"] and
        # assetCtxs[i] describe the same asset at the same index. Previously
        # this hit allMids (current mid-market PRICES, e.g. BTC ~60000.0)
        # and stored the raw price directly as the "funding rate", producing
        # an astronomically large annualized_rate for every symbol.
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
                return FundingResult()
            meta, asset_ctxs = data[0], data[1]
            universe = meta.get("universe", []) if isinstance(meta, dict) else []
            if not isinstance(asset_ctxs, list) or not isinstance(universe, list):
                logger.warning("Unexpected metaAndAssetCtxs meta/assetCtxs types")
                return FundingResult()
            rates: list[FundingRate] = []
            for asset, ctx in zip(universe, asset_ctxs):
                if not isinstance(asset, dict) or not isinstance(ctx, dict):
                    continue
                symbol = asset.get("name")
                funding = ctx.get("funding")
                if symbol is None or funding is None:
                    continue
                try:
                    rates.append(FundingRate(
                        symbol=str(symbol),
                        rate=float(funding),
                        timestamp=0,
                        next_funding_time=0,
                    ))
                except (ValueError, TypeError):
                    continue
            return FundingResult(rates=tuple(rates))
        except requests.RequestException as e:
            logger.warning("Failed to fetch funding data: %s", e)
            return FundingResult()

    def fetch_for_symbol(self, symbol: str) -> FundingRate | None:
        result = self.fetch_all()
        return result.rate_for(symbol)

    def fetch_funding_history(self, symbol: str, limit: int = 100) -> FundingResult:
        # Hyperliquid's fundingHistory takes "coin"/"startTime" as top-level
        # fields, not a nested "req" object, and has no direct "limit" --
        # the previous {"req": {"coin": ..., "limit": ...}} shape always
        # 422'd. Funding entries are ~8h apart (interval_hours default
        # below), so look back `limit` intervals plus a small buffer to
        # comfortably cover `limit` real entries, then truncate client-side.
        start_time = int(
            (datetime.now(UTC) - timedelta(hours=8 * (limit + 1))).timestamp() * 1000
        )
        payload = {
            "type": "fundingHistory",
            "coin": symbol.replace("USDT", ""),
            "startTime": start_time,
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
            data = data[-limit:]
            # Real fundingHistory entries never include an "interval" field
            # (only coin/fundingRate/premium/time) -- the old hardcoded
            # default of 8h silently understated annualized_rate by ~8x now
            # that Hyperliquid pays funding hourly, misclassifying real risk
            # as merely "elevated" instead of "extreme"/"high". Derive the
            # real interval from consecutive entry timestamps instead of
            # guessing; only fall back to 8h when there's too little data
            # (a single entry) to derive anything.
            fallback_interval_hours = 8.0
            times = [int(e["time"]) for e in data if isinstance(e, dict) and e.get("time") is not None]
            if len(times) >= 2:
                diffs = [b - a for a, b in zip(times, times[1:]) if b > a]
                if diffs:
                    fallback_interval_hours = (sum(diffs) / len(diffs)) / 1000 / 3600
            rates: list[FundingRate] = []
            for entry in data:
                try:
                    rate = FundingRate(
                        symbol=symbol,
                        rate=float(entry.get("fundingRate", 0)),
                        timestamp=int(entry.get("time", 0)),
                        next_funding_time=int(entry.get("nextFundingTime", 0)),
                        interval_hours=float(entry.get("interval", fallback_interval_hours)),
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
        if result.is_fresh:
            return {"fresh": True, "age_seconds": 0}
        return {"fresh": False, "reason": "Funding data is stale"}
