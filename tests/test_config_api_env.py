"""Tests for config.py's API_ENV fail-closed behavior.

API_ENV == "development" disables all authentication in api/middleware.py
and api/websocket/manager.py -- previously, an unset API_ENV silently
defaulted to "development", meaning any deployment that forgot to set it
(a hand-assembled .env, a PaaS without docker-compose.prod.yml's explicit
API_ENV) ran with zero authentication and no warning. config.py must now
refuse to start at all rather than guess.

Uses a real subprocess per case since API_ENV is read at module import
time -- re-importing config.py in-process (via importlib.reload) would
leave its cached module state polluted for every other test that imports
it afterward.
"""

from __future__ import annotations

import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_import_config(env: dict[str, str], cwd: str = REPO_ROOT) -> subprocess.CompletedProcess:
    env = dict(env)
    env["PYTHONPATH"] = REPO_ROOT
    return subprocess.run(
        [sys.executable, "-c", "import config"],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestApiEnvFailsClosed:
    def test_unset_api_env_refuses_to_start(self, tmp_path):
        # Run from a directory with no .env file -- config.py's load_dotenv()
        # would otherwise pick up this repo's real .env (which sets
        # API_ENV=production for the trial deployment) and mask the "truly
        # unset" scenario this test needs to exercise.
        env = {k: v for k, v in os.environ.items() if k != "API_ENV"}
        result = _run_import_config(env, cwd=str(tmp_path))
        assert result.returncode != 0
        assert "API_ENV must be set explicitly" in result.stderr

    def test_explicit_development_still_works(self):
        env = dict(os.environ)
        env["API_ENV"] = "development"
        result = _run_import_config(env)
        assert result.returncode == 0, result.stderr

    def test_explicit_test_still_works(self):
        env = dict(os.environ)
        env["API_ENV"] = "test"
        result = _run_import_config(env)
        assert result.returncode == 0, result.stderr
