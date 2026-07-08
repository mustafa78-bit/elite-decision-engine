"""Startup validation and environment checks."""

import logging
import os
import sys

from database import Base, create_tables, get_session

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = [
    "DATABASE_URL",
]

OPTIONAL_ENV_VARS = {
    "API_ENV": "development",
    "DEBUG": "false",
    "CORS_ORIGINS": "*",
    "JWT_SECRET": "dev-secret-change-in-production",
}

VALID_ENVS = {"development", "staging", "production"}


def validate_env() -> list[str]:
    errors: list[str] = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            errors.append(f"Missing required env var: {var}")
    env = os.getenv("API_ENV", "development")
    if env not in VALID_ENVS:
        errors.append(f"API_ENV must be one of {VALID_ENVS}, got: {env}")
    if env == "production":
        if not os.getenv("JWT_SECRET"):
            errors.append("JWT_SECRET is required when API_ENV=production")
        if os.getenv("CORS_ORIGINS", "").strip() in ("", "*"):
            errors.append("CORS_ORIGINS must be explicitly set (not '*') when API_ENV=production")
    return errors


def check_database() -> list[str]:
    errors: list[str] = []
    try:
        session = get_session()
        session.execute(__import__("sqlalchemy").text("SELECT 1"))
        session.close()
        logger.info("Database connection OK")
    except Exception as e:
        errors.append(f"Database connection failed: {e}")
        return errors

    try:
        session = get_session()
        for table_name in ("signals", "trades", "users", "notifications", "journal_entries", "user_settings"):
            try:
                session.execute(
                    __import__("sqlalchemy").text(f"SELECT 1 FROM {table_name} LIMIT 0")
                )
                logger.debug("Table %s accessible", table_name)
            except Exception as e:
                errors.append(f"Table {table_name} not accessible: {e}")
        session.close()
    except Exception as e:
        errors.append(f"Table verification failed: {e}")

    return errors


def run_startup_checks() -> bool:
    logger.info("Running startup checks...")

    env_errors = validate_env()
    for err in env_errors:
        logger.error("ENV: %s", err)

    db_errors = check_database()
    for err in db_errors:
        logger.error("DB: %s", err)

    all_errors = env_errors + db_errors
    if all_errors:
        logger.critical("Startup checks failed: %d error(s)", len(all_errors))
        return False

    logger.info("All startup checks passed")
    return True


def startup():
    if not run_startup_checks():
        sys.exit(1)
    create_tables()
    logger.info("Tables verified")


def shutdown():
    logger.info("Shutting down Elite Decision Engine")
    try:
        from database import engine
        engine.dispose()
        logger.info("Database engine disposed")
    except Exception as e:
        logger.warning("Error during engine dispose: %s", e)
    logger.info("Shutdown complete")
