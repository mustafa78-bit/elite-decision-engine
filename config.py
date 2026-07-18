import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("config")

API_ENV = os.getenv("API_ENV", "development")
VERSION = os.getenv("APP_VERSION", "0.9.0")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
if LOG_LEVEL not in VALID_LOG_LEVELS:
    LOG_LEVEL = "INFO"

CRITICAL_VARS = {
    "JWT_SECRET": "Authentication will not work",
}
RECOMMENDED_VARS = {
    "DATABASE_URL": "Falling back to POSTGRES_* env vars",
    "TELEGRAM_TOKEN": "Telegram notifications will be disabled",
    "HL_API_KEY": "Hyperliquid exchange connector will be unavailable",
    "NVIDIA_API_KEY": "NVIDIA NIM provider will be unavailable",
}

NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "nvidia")
AI_MODEL: str = os.getenv("AI_MODEL", "")
NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "")

for var in CRITICAL_VARS:
    if not os.getenv(var):
        msg = "%s not set. %s" % (var, CRITICAL_VARS[var])
        if API_ENV == "production":
            raise RuntimeError("FATAL: " + msg)
        logger.warning(msg)

for var, msg in RECOMMENDED_VARS.items():
    if not os.getenv(var):
        logger.warning("%s not set. %s", var, msg)

JWT_SECRET = os.getenv("JWT_SECRET", "")

ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
HL_API_KEY: str = os.getenv("HL_API_KEY", "")
HL_SECRET: str = os.getenv("HL_SECRET", "")
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    if not POSTGRES_HOST:
        if API_ENV == "production":
            raise RuntimeError("FATAL: DATABASE_URL or POSTGRES_HOST must be set in production")
        POSTGRES_HOST = "localhost"
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "decision_engine")
    DB_USER = POSTGRES_USER or "postgres"
    DB_PASSWORD = POSTGRES_PASSWORD or "postgres"
    DATABASE_URL = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}"
        f"@{POSTGRES_HOST}:{DB_PORT}/{DB_NAME}"
    )

DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", r"^https?://localhost(:\d+)?$")

# Scoring weights for the composite pipeline score (must sum to 1.0)
SCORE_WEIGHTS = {
    "trend": 0.30,
    "volume": 0.20,
    "btc": 0.20,
    "mtf": 0.20,
    "risk": 0.10,
}
assert abs(sum(SCORE_WEIGHTS.values()) - 1.0) < 1e-9, (
    f"SCORE_WEIGHTS must sum to 1.0, got {sum(SCORE_WEIGHTS.values())}"
)
# Confidence weights on a 0-100 scale (pre-multiplied by 100)
SCORE_WEIGHTS_PCT = {k: round(v * 100, 2) for k, v in SCORE_WEIGHTS.items()}

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "10"))
assert CHECK_INTERVAL > 0, f"CHECK_INTERVAL must be positive, got {CHECK_INTERVAL}"
MIN_SCORE = int(os.getenv("MIN_SCORE", "85"))
assert 0 <= MIN_SCORE <= 100, f"MIN_SCORE must be 0-100, got {MIN_SCORE}"
MAX_OPEN_TRADES = int(os.getenv("MAX_OPEN_TRADES", "3"))
assert MAX_OPEN_TRADES >= 0, f"MAX_OPEN_TRADES must be >= 0, got {MAX_OPEN_TRADES}"
MAX_EXPOSURE_PER_SYMBOL = float(os.getenv("MAX_EXPOSURE_PER_SYMBOL", "200000"))
assert MAX_EXPOSURE_PER_SYMBOL >= 0, f"MAX_EXPOSURE_PER_SYMBOL must be >= 0, got {MAX_EXPOSURE_PER_SYMBOL}"
MAX_PORTFOLIO_EXPOSURE = float(os.getenv("MAX_PORTFOLIO_EXPOSURE", "500000"))
assert MAX_PORTFOLIO_EXPOSURE >= 0, f"MAX_PORTFOLIO_EXPOSURE must be >= 0, got {MAX_PORTFOLIO_EXPOSURE}"
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "10000"))
assert MAX_DAILY_LOSS >= 0, f"MAX_DAILY_LOSS must be >= 0, got {MAX_DAILY_LOSS}"
MAX_POSITION_SIZE_USD = float(os.getenv("MAX_POSITION_SIZE_USD", "100000"))
assert MAX_POSITION_SIZE_USD >= 0, f"MAX_POSITION_SIZE_USD must be >= 0, got {MAX_POSITION_SIZE_USD}"
ACCOUNT_EQUITY = float(os.getenv("ACCOUNT_EQUITY", "10000"))
assert ACCOUNT_EQUITY > 0, f"ACCOUNT_EQUITY must be positive, got {ACCOUNT_EQUITY}"
RISK_PER_TRADE_PERCENT = float(os.getenv("RISK_PER_TRADE_PERCENT", "1.0"))
assert 0 < RISK_PER_TRADE_PERCENT <= 100, f"RISK_PER_TRADE_PERCENT must be 0-100, got {RISK_PER_TRADE_PERCENT}"
ATR_MULTIPLIER = float(os.getenv("ATR_MULTIPLIER", "1.5"))
assert ATR_MULTIPLIER > 0, f"ATR_MULTIPLIER must be positive, got {ATR_MULTIPLIER}"
MIN_POSITION_QUANTITY = float(os.getenv("MIN_POSITION_QUANTITY", "0.001"))
assert MIN_POSITION_QUANTITY > 0, f"MIN_POSITION_QUANTITY must be positive, got {MIN_POSITION_QUANTITY}"
