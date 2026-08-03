"""Shared Binance REST client utility with multi-host fallback support."""

from __future__ import annotations

import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


def fetch_binance_depth(symbol: str) -> dict[str, Any] | None:
    """Fetch order book depth for a symbol from Binance using multi-host fallback."""
    symbol_upper = symbol.upper()
    if not symbol_upper.endswith("USDT") and not symbol_upper.endswith("BUSD"):
        symbol_upper = f"{symbol_upper}USDT"

    hosts = [
        "https://api.binance.com",
        "https://api.binance.us",
        "https://api1.binance.com",
        "https://api2.binance.com",
        "https://api3.binance.com",
    ]

    for host in hosts:
        try:
            url = f"{host}/api/v3/depth"
            resp = requests.get(url, params={"symbol": symbol_upper, "limit": 100}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "bids" in data and "asks" in data:
                    return data
            elif resp.status_code == 429:
                logger.debug("Rate limited by Binance host %s", host)
            else:
                logger.debug("Received status %d from Binance host %s", resp.status_code, host)
        except Exception as e:
            logger.debug("Failed to fetch depth from Binance host %s: %s", host, e)

    return None
