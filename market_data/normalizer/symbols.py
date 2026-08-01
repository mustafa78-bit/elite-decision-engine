from __future__ import annotations

SYMBOL_MAP: dict[str, dict[str, str]] = {
    "hyperliquid": {
        "BTC": "BTC",
        "ETH": "ETH",
        "SOL": "SOL",
        "ARB": "ARB",
        "OP": "OP",
        "AVAX": "AVAX",
    },
    "binance": {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
        "SOL": "SOLUSDT",
        "ARB": "ARBUSDT",
        "OP": "OPUSDT",
        "AVAX": "AVAXUSDT",
    },
}

REVERSE_MAP: dict[str, dict[str, str]] = {
    exchange: {v: k for k, v in mapping.items()}
    for exchange, mapping in SYMBOL_MAP.items()
}


def to_exchange_symbol(standard: str, exchange: str) -> str:
    """Convert a standard symbol (e.g. 'BTC') to exchange-specific format."""
    mapping = SYMBOL_MAP.get(exchange, {})
    return mapping.get(standard.upper(), standard.upper())


def from_exchange_symbol(symbol: str, exchange: str) -> str:
    """Convert an exchange-specific symbol to the standard format."""
    mapping = REVERSE_MAP.get(exchange, {})
    return mapping.get(symbol.upper(), symbol.upper().replace("USDT", "").replace("USD", ""))


def standard_symbol(symbol: str) -> str:
    """Remove common suffixes to get the base symbol."""
    s = symbol.upper()
    for suffix in ["USDT", "USD", "USDC", "BUSD", "PERP"]:
        if s.endswith(suffix):
            return s[: -len(suffix)]
    return s
