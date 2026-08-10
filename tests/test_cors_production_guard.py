"""Tests for api/main.py's CORS wildcard-with-credentials production guard.

CORSMiddleware is registered with allow_credentials=True (hardcoded, not
conditional). Combined with a wildcard allow_origins, Starlette reflects
back whatever Origin header the browser sent (rather than a literal "*"),
letting any website make authenticated cross-origin requests against the
API. startup.py's StartupValidator already had an equivalent check, but
the real uvicorn entrypoint (api/main.py) never calls it -- this guard
fails at import time instead of relying on a check that silently never
runs in the real deployed app.

Uses a real subprocess per case since API_ENV/CORS_ORIGINS are read at
module import time.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_import_api_main(env_overrides: dict[str, str], db_path: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("API_ENV", "CORS_ORIGINS")}
    env["PYTHONPATH"] = REPO_ROOT
    env["JWT_SECRET"] = "test-secret-not-for-production-32b"
    # A file path, not ":memory:" -- database.py's engine always passes
    # max_overflow (a QueuePool-only kwarg) even when _is_sqlite, which
    # SQLite's in-memory SingletonThreadPool rejects but its regular
    # NullPool (used for a real file path) accepts. Out of scope to fix
    # here; this test only needs api.main to *import*, never to actually
    # connect.
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "import api.main"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "cors_guard_test.db")


class TestCorsProductionGuard:
    def test_wildcard_origin_in_production_refuses_to_start(self, db_path):
        result = _run_import_api_main({"API_ENV": "production", "CORS_ORIGINS": "*"}, db_path)
        assert result.returncode != 0
        assert "CORS_ORIGINS must be an explicit, non-wildcard origin list" in result.stderr

    def test_empty_origins_in_production_refuses_to_start(self, db_path):
        result = _run_import_api_main({"API_ENV": "production", "CORS_ORIGINS": ""}, db_path)
        assert result.returncode != 0
        assert "CORS_ORIGINS must be an explicit, non-wildcard origin list" in result.stderr

    def test_explicit_origin_in_production_still_works(self, db_path):
        result = _run_import_api_main(
            {"API_ENV": "production", "CORS_ORIGINS": "https://app.example.com"}, db_path
        )
        assert result.returncode == 0, result.stderr

    def test_wildcard_origin_in_development_still_works(self, db_path):
        # The guard is production-only -- dev/test environments are allowed
        # to use a permissive CORS config.
        result = _run_import_api_main({"API_ENV": "development", "CORS_ORIGINS": "*"}, db_path)
        assert result.returncode == 0, result.stderr
