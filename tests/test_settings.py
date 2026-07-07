"""Deterministic tests for Settings.

No external dependencies, no HTTP, no exchange calls.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from core.settings import ConfigurationError, Settings


_VALID_ENV = {
    "HL_API_KEY": "test-api-key",
    "HL_SECRET": "test-secret",
    "HL_WALLET_ADDRESS": "0x1234567890abcdef",
    "DRY_RUN": "True",
    "ACCOUNT_EQUITY": "50000",
    "MAX_OPEN_TRADES": "5",
}


class TestSettingsLoad:

    def test_loads_all_required_secrets(self):
        s = Settings(env=dict(_VALID_ENV))
        s.load()
        assert s.hl_api_key == "test-api-key"
        assert s.hl_secret == "test-secret"
        assert s.hl_wallet_address == "0x1234567890abcdef"

    def test_loads_with_defaults(self):
        env = {k: v for k, v in _VALID_ENV.items()}
        s = Settings(env=env)
        s.load()
        assert s.dry_run is True
        assert s.account_equity == 50000.0
        assert s.max_open_trades == 5

    def test_defaults_applied_when_missing(self):
        env = {
            "HL_API_KEY": "key",
            "HL_SECRET": "secret",
            "HL_WALLET_ADDRESS": "0xaddr",
        }
        s = Settings(env=env)
        s.load()
        assert s.dry_run is True
        assert s.account_equity == 10000.0
        assert s.max_open_trades == 3
        assert s.check_interval == 10
        assert s.min_score == 85
        assert s.atr_multiplier == 1.5
        assert s.min_position_quantity == 0.001

    def test_override_default(self):
        env = {
            **_VALID_ENV,
            "DRY_RUN": "False",
            "ACCOUNT_EQUITY": "99999",
        }
        s = Settings(env=env)
        s.load()
        assert s.dry_run is False
        assert s.account_equity == 99999.0

    def test_bool_true_values(self):
        for val in ("1", "true", "True", "yes", "on"):
            env = {**_VALID_ENV, "DRY_RUN": val}
            s = Settings(env=env)
            s.load()
            assert s.dry_run is True, f"failed for {val}"

    def test_bool_false_values(self):
        for val in ("0", "false", "no", "off", ""):
            env = {**_VALID_ENV, "DRY_RUN": val}
            s = Settings(env=env)
            s.load()
            assert s.dry_run is False, f"failed for {val}"


class TestSettingsMissingRequired:

    def test_missing_hl_api_key(self):
        env = {k: v for k, v in _VALID_ENV.items() if k != "HL_API_KEY"}
        s = Settings(env=env)
        with pytest.raises(ConfigurationError, match="HL_API_KEY"):
            s.load()

    def test_missing_hl_secret(self):
        env = {k: v for k, v in _VALID_ENV.items() if k != "HL_SECRET"}
        s = Settings(env=env)
        with pytest.raises(ConfigurationError, match="HL_SECRET"):
            s.load()

    def test_missing_hl_wallet_address(self):
        env = {k: v for k, v in _VALID_ENV.items() if k != "HL_WALLET_ADDRESS"}
        s = Settings(env=env)
        with pytest.raises(ConfigurationError, match="HL_WALLET_ADDRESS"):
            s.load()

    def test_missing_all_required(self):
        s = Settings(env={})
        with pytest.raises(ConfigurationError):
            s.load()


class TestSettingsInvalidValues:

    def test_invalid_int(self):
        env = {**_VALID_ENV, "MAX_OPEN_TRADES": "not-a-number"}
        s = Settings(env=env)
        with pytest.raises(ConfigurationError, match="MAX_OPEN_TRADES"):
            s.load()

    def test_invalid_float(self):
        env = {**_VALID_ENV, "ACCOUNT_EQUITY": "not-a-float"}
        s = Settings(env=env)
        with pytest.raises(ConfigurationError, match="ACCOUNT_EQUITY"):
            s.load()


class TestSettingsConfigurationError:

    def test_is_exception(self):
        assert issubclass(ConfigurationError, Exception)

    def test_message(self):
        err = ConfigurationError("test message")
        assert str(err) == "test message"
