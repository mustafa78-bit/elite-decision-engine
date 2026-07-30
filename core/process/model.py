# core/process/model.py
"""Cognitive Process Model representing structured executable tasks."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.process.atomic import YieldPoint


class ProcessState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    YIELDED = "YIELDED"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class CognitiveProcess:
    """A Cognitive Process represents a unit of execution within the decision network."""

    name: str
    target_func: Callable[[CognitiveProcess], Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: ProcessState = ProcessState.PENDING
    channel: str = "default"
    priority: int = 10  # default base priority
    version: int = 1  # versioned optimistic concurrency tracking
    error: Optional[str] = None
    result: Any = None
    execution_count: int = 0
    yield_point: Optional[YieldPoint] = None

    def check_yield(self) -> None:
        """Cooperative check to enforce atomic duration limits during execution."""
        if self.yield_point:
            self.yield_point.check_and_enforce()

    def run(self) -> Any:
        """Run the cognitive process, incrementing execution count."""
        self.state = ProcessState.RUNNING
        self.execution_count += 1
        return self.target_func(self)
