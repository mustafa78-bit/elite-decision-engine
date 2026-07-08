import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    DB_HOST = POSTGRES_HOST or "localhost"
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "decision_engine")
    DB_USER = POSTGRES_USER or "postgres"
    DB_PASSWORD = POSTGRES_PASSWORD or "postgres"
    DATABASE_URL = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

API_ENV = os.getenv("API_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

CHECK_INTERVAL = 10
MIN_SCORE = 85
MAX_OPEN_TRADES = 3
MAX_EXPOSURE_PER_SYMBOL = 200000
MAX_PORTFOLIO_EXPOSURE = 500000
MAX_DAILY_LOSS = 10000
MAX_POSITION_SIZE_USD = 100000
ACCOUNT_EQUITY = 10000
RISK_PER_TRADE_PERCENT = 1.0
ATR_MULTIPLIER = 1.5
MIN_POSITION_QUANTITY = 0.001
