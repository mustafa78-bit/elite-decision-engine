from __future__ import annotations

import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    pass


class Settings:

    def __init__(self, env: Optional[dict[str, str]] = None) -> None:
        self._env = env  # injectable for testing; None means use real env
        self._loaded = False

    def load(self) -> None:
        if self._env is None:
            load_dotenv()
            self._env = os.environ

        # --- secrets (required) ---
        self.hl_api_key = self._required_str("HL_API_KEY")
        self.hl_secret = self._required_str("HL_SECRET")
        self.hl_wallet_address = self._required_str("HL_WALLET_ADDRESS")

        # --- trading config (with defaults) ---
        self.dry_run = self._bool("DRY_RUN", True)
        self.account_equity = self._float("ACCOUNT_EQUITY", 10000.0)
        self.max_open_trades = self._int("MAX_OPEN_TRADES", 3)
        self.max_exposure_per_symbol = self._float("MAX_EXPOSURE_PER_SYMBOL", 200000.0)
        self.max_portfolio_exposure = self._float("MAX_PORTFOLIO_EXPOSURE", 500000.0)
        self.max_daily_loss = self._float("MAX_DAILY_LOSS", 10000.0)
        self.max_position_size_usd = self._float("MAX_POSITION_SIZE_USD", 100000.0)
        self.risk_per_trade_percent = self._float("RISK_PER_TRADE_PERCENT", 1.0)
        self.atr_multiplier = self._float("ATR_MULTIPLIER", 1.5)
        self.min_position_quantity = self._float("MIN_POSITION_QUANTITY", 0.001)
        self.check_interval = self._int("CHECK_INTERVAL", 10)
        self.min_score = self._int("MIN_SCORE", 85)

        self._loaded = True
        logger.info(
            "Settings loaded: dry_run=%s account_equity=%s max_open_trades=%s",
            self.dry_run, self.account_equity, self.max_open_trades,
        )

    def _required_str(self, key: str) -> str:
        value = self._env.get(key) if self._env else os.getenv(key)
        if not value:
            raise ConfigurationError(f"Missing required environment variable: {key}")
        return value

    def _str(self, key: str, default: str) -> str:
        raw = self._env.get(key, default) if self._env else os.getenv(key, default)
        return raw

    def _int(self, key: str, default: int) -> int:
        raw = self._env.get(key, str(default)) if self._env else os.getenv(key, str(default))
        try:
            return int(raw)
        except (TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid integer for {key}: {raw!r}") from e

    def _float(self, key: str, default: float) -> float:
        raw = self._env.get(key, str(default)) if self._env else os.getenv(key, str(default))
        try:
            return float(raw)
        except (TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid float for {key}: {raw!r}") from e

    def _bool(self, key: str, default: bool) -> bool:
        raw = self._env.get(key, str(default)) if self._env else os.getenv(key, str(default))
        if isinstance(raw, bool):
            return raw
        return raw.lower() in ("1", "true", "yes", "on")
