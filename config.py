import os
from dotenv import load_dotenv

load_dotenv(override=False)

POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HL_API_KEY = os.getenv("HL_API_KEY")
HL_SECRET = os.getenv("HL_SECRET")

CHECK_INTERVAL = 10
MIN_SCORE = 85
MAX_OPEN_TRADES = 3

WHALE_ENABLED = os.getenv("WHALE_ENABLED", "true").lower() == "true"
LARGE_TRANSFER_THRESHOLD = float(os.getenv("LARGE_TRANSFER_THRESHOLD", "100000"))

LIQUIDITY_ENABLED = os.getenv("LIQUIDITY_ENABLED", "true").lower() == "true"
ORDERFLOW_ENABLED = os.getenv("ORDERFLOW_ENABLED", "true").lower() == "true"
MARKET_STRUCTURE_ENABLED = os.getenv("MARKET_STRUCTURE_ENABLED", "true").lower() == "true"
