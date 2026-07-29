from __future__ import annotations

import pytest
from utils.error_intelligence import capture_exception


def test_capture_exception():
    try:
        raise ValueError("simulated test error")
    except ValueError as e:
        structured = capture_exception(e, "test_module", severity="HIGH", recoverable=True)
        assert structured["error_type"] == "ValueError"
        assert "simulated" in structured["message"]
        assert structured["module"] == "test_module"
        assert structured["severity"] == "HIGH"
        assert structured["recoverability"] == "RECOVERABLE"
        assert "ValueError: simulated test error" in structured["stack_trace"]
