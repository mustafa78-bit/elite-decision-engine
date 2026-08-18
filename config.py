import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("config")

API_ENV = os.getenv("API_ENV")
if API_ENV is None:
    # No silent default: API_ENV == "development" disables all auth in
    # api/middleware.py and api/websocket/manager.py. Silently defaulting to
    # "development" meant any deployment that simply forgot to set this var
    # (a hand-assembled .env, a PaaS without docker-compose.prod.yml's
    # explicit API_ENV: production) would run with zero authentication on
    # every non-public route and every websocket, with no warning at all.
    raise RuntimeError(
        "FATAL: API_ENV must be set explicitly to 'development' or 'production' "
        "-- there is no default, since silently defaulting to 'development' "
        "previously disabled all authentication whenever this var was merely "
        "forgotten. Set API_ENV=development for local dev or API_ENV=production "
        "for any real deployment."
    )
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
    "SENTRY_DSN": "Error tracking will be disabled",
}

NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_API_KEY_2: str = os.getenv("NVIDIA_API_KEY_2", "")
AI_PROVIDER: str = os.getenv("AI_PROVIDER", "nvidia")
AI_MODEL: str = os.getenv("AI_MODEL", "")
NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "")

# Observed live: bursts of concurrent AI calls (OLLO queries, per-symbol
# council/decision prompts across the 25-coin universe) routinely hit
# NVIDIA's real rate limit, burning the existing retry budget on 429s/
# timeouts instead of avoiding them. Each NVIDIAProvider instance (one per
# API key -- see MultiNVIDIAProvider) proactively throttles its own outbound
# requests to this rate instead of firing them all immediately and retrying
# after the fact. Conservative starting point, no documented NVIDIA NIM RPM
# limit to size this against precisely -- tune based on real 429 volume.
NVIDIA_MAX_REQUESTS_PER_SECOND: float = float(os.getenv("NVIDIA_MAX_REQUESTS_PER_SECOND", "1.0"))

for var in CRITICAL_VARS:
    if not os.getenv(var):
        msg = f"{var} not set. {CRITICAL_VARS[var]}"
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
SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_ALLOWED_CHAT_IDS: str = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")

# Market-moving crypto news bot -- separate bot/chat from the trades/health
# bot above, so news pushes don't mix with trade alerts.
TELEGRAM_NEWS_TOKEN: str = os.getenv("TELEGRAM_NEWS_TOKEN", "")
TELEGRAM_NEWS_CHAT_ID: str = os.getenv("TELEGRAM_NEWS_CHAT_ID", "")

# Institutional/VC project-funding news bot -- also separate from both bots
# above. New spot-listing announcements (services/listings_service.py) also
# route through this same bot, at the user's request -- no separate bot/
# token needed for those.
TELEGRAM_VC_TOKEN: str = os.getenv("TELEGRAM_VC_TOKEN", "")
TELEGRAM_VC_CHAT_ID: str = os.getenv("TELEGRAM_VC_CHAT_ID", "")

# Minimum classify_and_score() impact score (0-100) a market-moving headline
# needs to actually trigger a Telegram push -- the score was computed and
# shown in every alert's text but never gated whether one was sent at all,
# so routine/low-impact headlines fired exactly as readily as genuinely
# market-moving ones. The scoring prompt itself calibrates "most ordinary
# headlines should score well below 50" (market/intelligence/news.py), so
# 40 keeps real market-moving news while cutting the routine noise.
NEWS_MIN_IMPACT_SCORE: int = int(os.getenv("NEWS_MIN_IMPACT_SCORE", "40"))

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
HEALTH_CHECK_INTERVAL_SECONDS = int(os.getenv("HEALTH_CHECK_INTERVAL_SECONDS", "60"))
assert HEALTH_CHECK_INTERVAL_SECONDS > 0, (
    f"HEALTH_CHECK_INTERVAL_SECONDS must be positive, got {HEALTH_CHECK_INTERVAL_SECONDS}"
)
MIN_SCORE = int(os.getenv("MIN_SCORE", "85"))
assert 0 <= MIN_SCORE <= 100, f"MIN_SCORE must be 0-100, got {MIN_SCORE}"

MAX_SIGNAL_RETRIES = int(os.getenv("MAX_SIGNAL_RETRIES", "3"))
assert MAX_SIGNAL_RETRIES >= 0, f"MAX_SIGNAL_RETRIES must be >= 0, got {MAX_SIGNAL_RETRIES}"
# Backoff delays (seconds) for signal-processing retry attempts 1/2/3+ -- a
# transient failure (network blip, momentary DB error) in
# DecisionEngine.process_signal() gets these increasing delays before
# reprocessing, rather than an immediate retry on the next CHECK_INTERVAL
# tick. Deliberately much larger than CHECK_INTERVAL's default 10s so a
# retry is a real wait, not effectively instant. The last entry is reused
# for any attempt beyond the list's length.
SIGNAL_RETRY_BACKOFF_SECONDS = [30, 120, 300]
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
# TP1 distance in ATR multiples -- was a hardcoded 2.0 in execution/tp_sl.py,
# giving a real (non-simulator) risk:reward of only 2.0/1.5 = 1.33:1 (TP1 vs
# the stop above). At a 1.33:1 payoff the breakeven win rate is ~43% -- a
# 40% win rate, which a real system can plausibly land on, is a real loss.
# Raised to 3.0 for a clean 2:1 minimum (founder decision, 2026-08-17,
# "1 2 minimum değil mi") -- breakeven drops to a much more forgiving ~33%.
TP1_ATR_MULTIPLIER = float(os.getenv("TP1_ATR_MULTIPLIER", "3.0"))
assert TP1_ATR_MULTIPLIER > 0, f"TP1_ATR_MULTIPLIER must be positive, got {TP1_ATR_MULTIPLIER}"
MIN_POSITION_QUANTITY = float(os.getenv("MIN_POSITION_QUANTITY", "0.001"))
assert MIN_POSITION_QUANTITY > 0, f"MIN_POSITION_QUANTITY must be positive, got {MIN_POSITION_QUANTITY}"

COIN_UNIVERSE_SIZE = int(os.getenv("COIN_UNIVERSE_SIZE", "100"))

# Fixed, permanent scan universe -- replaces the dynamic top-N-by-volume
# universe. Founder's actual chosen 25 symbols, decided 2026-08-07 to cut
# real external-call volume (funding/OI/whale/news fetched per symbol per
# scan cycle). "XUSDT" format is normalized to Hyperliquid's bare-ticker
# convention by market/provider/hyperliquid.py's get_ohlcv() already.
FIXED_COIN_UNIVERSE: list[str] = [
    # Majors
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    # Large L1s
    "ADAUSDT", "AVAXUSDT", "DOTUSDT", "TONUSDT", "TRXUSDT", "SUIUSDT",
    # L2 / infrastructure
    "ARBUSDT", "OPUSDT", "LINKUSDT", "POLUSDT",
    # DeFi
    "UNIUSDT", "AAVEUSDT", "MKRUSDT", "LDOUSDT",
    # Established alts
    "LTCUSDT", "BCHUSDT", "ATOMUSDT", "NEARUSDT",
    # AI / diversification picks
    "TAOUSDT", "APTUSDT",
]

# Splits FIXED_COIN_UNIVERSE's 25 symbols roughly evenly across Hyperliquid and
# Binance (13/12) so a single provider doesn't carry the full symbol load alone.
# Alternates through the list in its existing declared order (majors/L1s/L2s/
# DeFi/alts groupings preserved) rather than clustering by category, so no
# single provider ends up disproportionately loaded with one asset class.
# BTC (index 0, the most-tested path) stays on Hyperliquid; symbols not in this
# table (temp-watch additions, free-text AssetDetail lookups) always resolve to
# Hyperliquid -- see market/provider/multi.py::MultiProvider.
SYMBOL_PROVIDER_ASSIGNMENT: dict[str, str] = {
    symbol: ("hyperliquid" if i % 2 == 0 else "binance")
    for i, symbol in enumerate(FIXED_COIN_UNIVERSE)
}

AUTO_TRADING_ENABLED = os.getenv("AUTO_TRADING_ENABLED", "false").lower() == "true"

# Gates a real (paper) trade behind council/fundamental_gate.py's News/Whale/
# Macro majority-veto check -- see that module's docstring for the full
# design rationale (majority quorum, veto-only/never-approve, fails open).
# Defaults on: it's a pure safety net (can only block a trade
# ScoringEngine/ConfidenceEngine already approved, never approve one they
# didn't), so unlike AUTO_TRADING_ENABLED there's no reason to default it
# off once it exists.
FUNDAMENTAL_VETO_ENABLED = os.getenv("FUNDAMENTAL_VETO_ENABLED", "true").lower() == "true"

# Was 300s (5 min) scanning against 1h candles -- a mismatch founder caught
# live (2026-08-18): an hourly candle is still forming for up to 59 of every
# 60 minutes, so 11 of every 12 scans re-evaluated nearly the same data as
# the previous scan, wasting real API calls for almost no new information
# ("bu da sistemi yoruyor" / "sürekli hata almamızın sebebi bu olabilir").
# Scan cadence now matches the candle timeframe it evaluates -- every scan
# sees genuinely fresh, closed price action instead of a still-forming
# candle. 15m chosen over 1h for faster reaction to real setups while still
# being a real closed candle each time, not scanner/core.py's previous
# default 1h timeframe scanned 12x too often.
SCANNER_TIMEFRAME = os.getenv("SCANNER_TIMEFRAME", "15m")
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "900"))
assert SCAN_INTERVAL_SECONDS > 0, f"SCAN_INTERVAL_SECONDS must be positive, got {SCAN_INTERVAL_SECONDS}"
