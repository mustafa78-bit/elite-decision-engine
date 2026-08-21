from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import requests

from market_data.funding.models import _FRESHNESS_THRESHOLD_SECONDS, FundingRate, FundingResult, validate_funding_rate

logger = logging.getLogger(__name__)


class FundingCollector:
    BASE_URL = "https://api.hyperliquid.xyz/info"
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2.0

    # metaAndAssetCtxs is a bulk "every symbol in one call" endpoint, so
    # every caller across the whole process asking for any symbol's funding
    # rate is really asking for the exact same snapshot. Without this, each
    # of the many independent places that construct their own
    # FundingCollector() (IntelligenceService per scanned symbol,
    # api/routes/funding.py, HyperliquidProvider, WhaleService, ...) fired
    # its own redundant network call for identical data -- a single 25-
    # symbol scanner pass alone could fire 25 of them, tripping
    # Hyperliquid's rate limiting and hanging the scanner. Cached at the
    # class level (not per-instance) so it collapses calls across separate
    # instances too, not just repeated calls on one. Real funding rates
    # update roughly hourly, so 30s is a large practical win with no
    # meaningful staleness cost.
    _CACHE_TTL_SECONDS = 30
    _cache: tuple[float, FundingResult] | None = None
    # Without this, N concurrent callers who all see a stale/empty cache at
    # once (e.g. every scanner symbol firing at process startup) each fire
    # their own network call before any of them populates the cache -- the
    # exact thundering-herd burst that trips Hyperliquid's real rate limit.
    # Only the first caller to acquire this actually hits the network; the
    # rest block, then read the now-fresh cache the first one just filled.
    _cache_lock = threading.Lock()

    # fetch_funding_history() (per-symbol, unlike the bulk fetch_all() above)
    # had NO cache at all until this fix -- confirmed live 2026-08-21 as a
    # real, significant contributor to Hyperliquid 429 storms: WhaleService
    # calls it once per scanned symbol with zero throttling, so a single
    # 25-symbol scan fired 25 uncached, unthrottled requests back-to-back,
    # independent of and in addition to whatever market/provider's shared
    # rate limiter was doing for OHLCV. Same class-level, per-key cache
    # pattern as fetch_all(), just keyed by (symbol, limit) since this data
    # is genuinely per-symbol, not a shared bulk snapshot.
    _history_cache: dict[tuple[str, int], tuple[float, FundingResult]] = {}
    _history_cache_lock = threading.Lock()

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self._session = requests.Session()

    def fetch_all(self) -> FundingResult:
        cached = FundingCollector._cache
        if cached is not None and time.time() - cached[0] < FundingCollector._CACHE_TTL_SECONDS:
            return cached[1]

        with FundingCollector._cache_lock:
            # Re-check: another thread may have refilled the cache while we
            # were waiting for the lock.
            cached = FundingCollector._cache
            if cached is not None and time.time() - cached[0] < FundingCollector._CACHE_TTL_SECONDS:
                return cached[1]
            return self._fetch_all_uncached()

    def _fetch_all_uncached(self) -> FundingResult:
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
            result = FundingResult(rates=tuple(rates))
            FundingCollector._cache = (time.time(), result)
            return result
        except requests.RequestException as e:
            logger.warning("Failed to fetch funding data: %s", e)
            return FundingResult()

    def fetch_for_symbol(self, symbol: str) -> FundingRate | None:
        result = self.fetch_all()
        return result.rate_for(symbol)

    def fetch_funding_history(self, symbol: str, limit: int = 100) -> FundingResult:
        cache_key = (symbol, limit)
        cached = FundingCollector._history_cache.get(cache_key)
        if cached is not None and time.time() - cached[0] < FundingCollector._CACHE_TTL_SECONDS:
            return cached[1]

        with FundingCollector._history_cache_lock:
            cached = FundingCollector._history_cache.get(cache_key)
            if cached is not None and time.time() - cached[0] < FundingCollector._CACHE_TTL_SECONDS:
                return cached[1]
            result = self._fetch_funding_history_uncached(symbol, limit)
            FundingCollector._history_cache[cache_key] = (time.time(), result)
            return result

    def _fetch_funding_history_uncached(self, symbol: str, limit: int = 100) -> FundingResult:
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
