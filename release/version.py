from __future__ import annotations

import subprocess
import sys
from typing import Any


VERSION = "1.0.0"


def _get_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


class VersionService:

    def get_version(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "commit": _get_commit(),
        }
