from __future__ import annotations

from typing import Any, Optional

from release.startup import StartupValidator


class ReadinessService:

    def __init__(
        self,
        startup_validator: Optional[StartupValidator] = None,
    ) -> None:
        self._startup_validator = startup_validator

    def is_ready(self) -> dict[str, Any]:
        if self._startup_validator is not None:
            result = self._startup_validator.validate()
            return {"ready": result.get("all_pass", False)}
        return {"ready": True}
