import logging

from database import get_session
from config import API_ENV

logger = logging.getLogger(__name__)


def check_database() -> dict:
    try:
        session = get_session()
        session.execute(__import__("sqlalchemy").text("SELECT 1"))
        session.close()
        return {"status": "ok"}
    except Exception as e:
        logger.warning("DB health check failed: %s", e)
        return {"status": "error", "message": str(e)}


def get_system_health() -> dict:
    db = check_database()
    return {
        "status": "ok" if db["status"] == "ok" else "degraded",
        "environment": API_ENV,
        "database": db,
    }
