"""Tests for the Sentry error-tracking integration in api/main.py.

sentry_sdk.init() is called at module import time (before the FastAPI(...)
instance is constructed, so Sentry's FastAPI/Starlette auto-instrumentation
actually attaches) -- uses a real subprocess per case, matching this repo's
existing tests/test_cors_production_guard.py convention for import-time,
env-driven behavior.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _base_env(db_path: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("API_ENV", "CORS_ORIGINS", "SENTRY_DSN")}
    env["PYTHONPATH"] = REPO_ROOT
    env["JWT_SECRET"] = "test-secret-not-for-production-32b"
    env["API_ENV"] = "development"
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    return env


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "sentry_integration_test.db")


class TestSentryDisabledWhenUnset:
    def test_app_starts_cleanly_with_sentry_dsn_unset(self, db_path):
        env = _base_env(db_path)
        result = subprocess.run(
            [sys.executable, "-c", "import api.main"],
            cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, result.stderr
        assert "SENTRY_DSN not set. Error tracking will be disabled" in result.stderr


class TestSentryInitializedWhenSet:
    def test_sentry_sdk_init_is_called_with_a_real_dsn(self, db_path):
        env = _base_env(db_path)
        env["SENTRY_DSN"] = "https://examplepublickey@o0.ingest.sentry.io/0"
        probe_script = (
            "import sentry_sdk\n"
            "calls = []\n"
            "_orig_init = sentry_sdk.init\n"
            "def _spy_init(*args, **kwargs):\n"
            "    calls.append(kwargs)\n"
            "    return _orig_init(*args, **kwargs)\n"
            "sentry_sdk.init = _spy_init\n"
            "import api.main\n"
            "print('SENTRY_INIT_CALLED' if calls else 'SENTRY_INIT_NOT_CALLED')\n"
            "print(calls[0].get('dsn') if calls else '')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe_script],
            cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, result.stderr
        assert "SENTRY_INIT_CALLED" in result.stdout
        assert "o0.ingest.sentry.io" in result.stdout
