"""Fetches and locally persists real historical OHLCV for the fixed 25-coin
universe -- the foundation for backtest/engine.py's parameter search.

Persisted locally only (data/historical/<symbol>_<timeframe>.parquet, gitignored)
-- never sent anywhere external. Re-running this only re-fetches symbols whose
saved file is missing or older than REFRESH_AFTER_HOURS, so repeated runs
don't re-hammer Hyperliquid/Binance for data that hasn't gone stale.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from config import FIXED_COIN_UNIVERSE
from market.provider import MultiProvider, get_shared_multi_provider

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "historical"
REFRESH_AFTER_HOURS = 24
# Real Hyperliquid candleSnapshot ceiling observed empirically -- see
# fetch_all_historical()'s docstring for how this was verified live.
MAX_CANDLES_PER_REQUEST = 5000


def _file_path(symbol: str, timeframe: str) -> Path:
    return DATA_DIR / f"{symbol}_{timeframe}.csv"


def _is_stale(path: Path) -> bool:
    if not path.exists():
        return True
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    return age_hours > REFRESH_AFTER_HOURS


def fetch_symbol_history(
    symbol: str,
    timeframe: str = "1h",
    limit: int = MAX_CANDLES_PER_REQUEST,
    provider: MultiProvider | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """Real historical OHLCV for one symbol -- from the local parquet cache
    if fresh, otherwise fetched live and saved. Never raises; returns an
    empty DataFrame on failure so a single bad symbol doesn't kill a full
    25-symbol batch fetch."""
    path = _file_path(symbol, timeframe)

    if not force and not _is_stale(path):
        try:
            return pd.read_csv(path, index_col=0, parse_dates=True)
        except Exception as e:
            logger.warning("Failed to read cached history for %s: %s, re-fetching", symbol, e)

    try:
        mp = provider or get_shared_multi_provider()
        df = mp.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        if df is None or df.empty:
            logger.warning("Empty historical OHLCV for %s %s", symbol, timeframe)
            return pd.DataFrame()

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(path)
        logger.info("Saved %d candles for %s %s -> %s", len(df), symbol, timeframe, path)
        return df
    except Exception as e:
        logger.warning("Failed to fetch historical OHLCV for %s: %s", symbol, e)
        return pd.DataFrame()


def fetch_all_historical(
    symbols: list[str] | None = None,
    timeframe: str = "1h",
    force: bool = False,
) -> dict[str, pd.DataFrame]:
    """Fetches (or loads from local cache) real historical OHLCV for every
    symbol in the fixed 25-coin universe, one at a time (not parallel --
    same reasoning as scanner/core.py's sequential scan: doesn't burst all
    25 requests at once against the same rate-limited providers).

    Includes "BTC" even if not already in the universe -- backtest/engine.py
    needs BTC's own history to reconstruct BTCHealth.score() at each
    historical point (see market_data/btc_health.py).
    """
    mp = get_shared_multi_provider()
    target_symbols = list(symbols or FIXED_COIN_UNIVERSE)
    if "BTCUSDT" not in target_symbols and "BTC" not in target_symbols:
        target_symbols.append("BTCUSDT")

    results: dict[str, pd.DataFrame] = {}
    for symbol in target_symbols:
        df = fetch_symbol_history(symbol, timeframe=timeframe, provider=mp, force=force)
        results[symbol] = df
        if not df.empty:
            start = df.index[0] if isinstance(df.index, pd.DatetimeIndex) else df.iloc[0].get("timestamp", "?")
            logger.info(
                "%s: %d candles, %s -> %s",
                symbol, len(df), start, datetime.now(UTC).isoformat(),
            )

    return results
