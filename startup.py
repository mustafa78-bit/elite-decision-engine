"""Startup validation and environment checks.

Usage:
    validator = StartupValidator()
    if not validator.run():
        sys.exit(1)

    # Or use convenience functions:
    startup()    # run checks + create tables
    shutdown()   # cleanup
"""

from __future__ import annotations

import logging
import os
import sys

from sqlalchemy import text

from config import CHECK_INTERVAL, MAX_OPEN_TRADES, MIN_SCORE
from database import create_tables, engine, get_session

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


class StartupValidator:
    """Validate all runtime dependencies before the engine enters the main loop."""

    def run(self, fail_fast: bool = True) -> bool:
        logger.info("Starting startup validation")

        checks = [
            ("Environment variables", self._check_env_vars),
            ("PostgreSQL env vars", self._check_postgres_vars),
            ("Configuration sanity", self._check_config_sanity),
            ("Database connectivity", self._check_db_connectivity),
            ("Table accessibility", self._check_tables),
        ]

        all_pass = True
        for label, check in checks:
            try:
                check()
                logger.info("PASS  %s", label)
            except Exception as e:
                logger.error("FAIL  %s: %s", label, e)
                all_pass = False
                if fail_fast:
                    return False

        if all_pass:
            logger.info("All startup checks passed.")
        return all_pass

    def _check_env_vars(self) -> None:
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
        if errors:
            raise ValueError("; ".join(errors))

    def _check_postgres_vars(self) -> None:
        from config import DATABASE_URL, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_USER
        if DATABASE_URL.startswith("sqlite"):
            return
        missing = []
        if not POSTGRES_HOST:
            missing.append("POSTGRES_HOST")
        if not POSTGRES_USER:
            missing.append("POSTGRES_USER")
        if not POSTGRES_PASSWORD:
            missing.append("POSTGRES_PASSWORD")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    def _check_config_sanity(self) -> None:
        errors = []
        if not isinstance(CHECK_INTERVAL, (int, float)) or CHECK_INTERVAL < 1:
            errors.append(f"CHECK_INTERVAL ({CHECK_INTERVAL}) must be >= 1")
        if not isinstance(MIN_SCORE, (int, float)) or MIN_SCORE < 0 or MIN_SCORE > 100:
            errors.append(f"MIN_SCORE ({MIN_SCORE}) must be between 0 and 100")
        if not isinstance(MAX_OPEN_TRADES, int) or MAX_OPEN_TRADES < 0:
            errors.append(f"MAX_OPEN_TRADES ({MAX_OPEN_TRADES}) must be >= 0")
        if errors:
            raise ValueError("; ".join(errors))

    def _check_db_connectivity(self) -> None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            raise RuntimeError(f"Cannot connect to database: {e}")

    def _check_tables(self) -> None:
        session = get_session()
        try:
            for table_name in ("signals", "trades", "users", "notifications", "journal_entries", "user_settings"):
                try:
                    session.execute(text(f"SELECT 1 FROM {table_name} LIMIT 0"))
                    logger.debug("Table %s accessible", table_name)
                except Exception as e:
                    raise RuntimeError(f"Table {table_name} not accessible: {e}")
        finally:
            session.close()


def startup():
    validator = StartupValidator()
    if not validator.run():
        sys.exit(1)
    create_tables()
    logger.info("Tables verified")


def shutdown(timeout: float = 5.0):
    logger.info("Shutting down Elite Decision Engine")
    try:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                for task in asyncio.all_tasks(loop):
                    if task is not asyncio.current_task():
                        task.cancel()
        except RuntimeError:
            pass
    except Exception as e:
        logger.warning("Error during async cleanup: %s", e)
    try:
        engine.dispose()
        logger.info("Database engine disposed")
    except Exception as e:
        logger.warning("Error during engine dispose: %s", e)
    logging.shutdown()
    logger.info("Shutdown complete")
