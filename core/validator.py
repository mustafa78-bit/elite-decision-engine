"""Production startup validation for the Elite Decision Engine.

Usage:
    validator = StartupValidator()
    if not validator.run():
        sys.exit(1)
"""

from sqlalchemy import text

from config import (
    CHECK_INTERVAL,
    MAX_OPEN_TRADES,
    MIN_SCORE,
    POSTGRES_HOST,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)
from database import engine


class StartupValidator:
    """Validate all runtime dependencies before the engine enters the main loop."""

    def run(self, fail_fast=True):
        print("=" * 50)
        print("STARTUP VALIDATION")
        print("=" * 50)

        checks = [
            ("Environment variables", self._check_env_vars),
            ("Database connectivity", self._check_db_connectivity),
            ("Configuration sanity", self._check_config_sanity),
        ]

        all_pass = True
        for label, check in checks:
            try:
                check()
                print(f"  [{'V'}] {label}")
            except Exception as e:
                print(f"  [X] {label}: {e}")
                all_pass = False
                if fail_fast:
                    return False

        if all_pass:
            print()
            print("All checks passed.")
        return all_pass

    def _check_env_vars(self):
        missing = []
        if not POSTGRES_HOST:
            missing.append("POSTGRES_HOST")
        if not POSTGRES_USER:
            missing.append("POSTGRES_USER")
        if not POSTGRES_PASSWORD:
            missing.append("POSTGRES_PASSWORD")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    def _check_db_connectivity(self):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            raise RuntimeError(f"Cannot connect to database: {e}")

    def _check_config_sanity(self):
        errors = []
        if not isinstance(CHECK_INTERVAL, (int, float)) or CHECK_INTERVAL < 1:
            errors.append(f"CHECK_INTERVAL ({CHECK_INTERVAL}) must be >= 1")
        if not isinstance(MIN_SCORE, (int, float)) or MIN_SCORE < 0 or MIN_SCORE > 100:
            errors.append(f"MIN_SCORE ({MIN_SCORE}) must be between 0 and 100")
        if not isinstance(MAX_OPEN_TRADES, int) or MAX_OPEN_TRADES < 0:
            errors.append(f"MAX_OPEN_TRADES ({MAX_OPEN_TRADES}) must be >= 0")
        if errors:
            raise ValueError("; ".join(errors))
