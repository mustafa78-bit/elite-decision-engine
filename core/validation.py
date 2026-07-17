import os
import re
from typing import Any, Dict, List, Optional


_SENSITIVE_KEYS = frozenset({
    "POSTGRES_PASSWORD",
    "TELEGRAM_TOKEN",
    "HL_API_KEY",
    "HL_SECRET",
})

_REQUIRED_CONFIG_KEYS = frozenset({
    "POSTGRES_HOST",
    "POSTGRES_DB",
})


class ConfigValidationError(Exception):
    pass


def mask_secret(value: Optional[str]) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return value[:4] + "****" + value[-4:]


def validate_secrets() -> List[str]:
    warnings = []
    for key in _SENSITIVE_KEYS:
        value = os.getenv(key)
        if not value:
            warnings.append(f"Secret '{key}' is not set")
        elif value in ("postgres", "password", "token", "key", "secret"):
            warnings.append(f"Secret '{key}' appears to use a default/placeholder value")
    return warnings


def validate_env(name: str, default: Any = None, required: bool = False, validator: Optional[callable] = None) -> Any:
    value = os.getenv(name, default)
    if required and value is None:
        raise ConfigValidationError(f"Required environment variable '{name}' is not set")
    if value is not None and validator:
        try:
            return validator(value)
        except (ValueError, TypeError) as e:
            raise ConfigValidationError(f"Environment variable '{name}' is invalid: {e}")
    return value


def validate_port(value: str) -> int:
    port = int(value)
    if not (0 < port <= 65535):
        raise ValueError(f"Port out of range: {port}")
    return port


def validate_positive_float(value: str) -> float:
    v = float(value)
    if v <= 0:
        raise ValueError(f"Value must be positive: {v}")
    return v


def validate_threshold(value: str) -> float:
    v = float(value)
    if not (0 <= v <= 100):
        raise ValueError(f"Threshold must be 0-100: {v}")
    return v


class ConfigValidator:

    def __init__(self):
        self._errors: List[str] = []

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self._errors.append(message)

    def validate(self) -> List[str]:
        return list(self._errors)

    @property
    def is_valid(self) -> bool:
        return len(self._errors) == 0


def validate_config() -> List[str]:
    validator = ConfigValidator()
    try:
        for key in _REQUIRED_CONFIG_KEYS:
            validator.check(
                os.getenv(key) is not None,
                f"{key} is required",
            )
        if os.getenv("POSTGRES_PORT"):
            try:
                validate_port(os.getenv("POSTGRES_PORT"))
            except ConfigValidationError as e:
                validator.check(False, str(e))
        secret_warnings = validate_secrets()
        for w in secret_warnings:
            validator.check(False, w)
    except Exception as e:
        validator.check(False, f"Config validation error: {e}")
    return validator.validate()


def validate_startup() -> List[str]:
    warnings = []
    warnings.extend(validate_config())
    port_raw = os.getenv("POSTGRES_PORT", "5432")
    try:
        validate_port(port_raw)
    except (ValueError, ConfigValidationError):
        warnings.append(f"Invalid POSTGRES_PORT: {port_raw}")
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if telegram_token and not re.match(r"^\d+:[A-Za-z0-9_-]+$", telegram_token):
        warnings.append("TELEGRAM_TOKEN format appears invalid")
    return warnings
