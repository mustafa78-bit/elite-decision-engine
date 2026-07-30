# core/process/interrupts.py
"""Local Real-Time Interrupt path definitions for pre-emptive execution."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class InterruptSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class LocalInterrupt:
    """Represents a localized Real-Time interrupt triggered in the process subsystem."""

    id: str
    target_process_id: str
    severity: InterruptSeverity
    payload: Dict[str, Any]
    handled: bool = False
