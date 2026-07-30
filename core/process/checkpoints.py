# core/process/checkpoints.py
"""Process Checkpoints storing snapshots for crash resume and version validation."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProcessCheckpoint:
    """Snapshot representing a process state at a specific execution milestone."""

    process_id: str
    checkpoint_id: str
    version: int
    memory_snapshot: Dict[str, Any]
    milestone_name: str
    timestamp: float


class CheckpointRegistry:
    """Manages creation, storage, and retrieval of process checkpoints."""

    def __init__(self) -> None:
        self._checkpoints: Dict[str, ProcessCheckpoint] = {}

    def save_checkpoint(
        self,
        process_id: str,
        checkpoint_id: str,
        version: int,
        memory_snapshot: Dict[str, Any],
        milestone_name: str,
    ) -> ProcessCheckpoint:
        """Create and store a milestone checkpoint."""
        import time
        cp = ProcessCheckpoint(
            process_id=process_id,
            checkpoint_id=checkpoint_id,
            version=version,
            memory_snapshot=dict(memory_snapshot),
            milestone_name=milestone_name,
            timestamp=time.time(),
        )
        self._checkpoints[f"{process_id}:{checkpoint_id}"] = cp
        logger.info("Saved checkpoint for process %s, milestone '%s'", process_id, milestone_name)
        return cp

    def get_checkpoint(self, process_id: str, checkpoint_id: str) -> Optional[ProcessCheckpoint]:
        """Retrieve stored checkpoint."""
        return self._checkpoints.get(f"{process_id}:{checkpoint_id}")

    def clear(self) -> None:
        """Clear all registered checkpoints."""
        self._checkpoints.clear()
