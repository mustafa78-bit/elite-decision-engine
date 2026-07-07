from __future__ import annotations

import logging
from enum import Enum
from typing import Optional


logger = logging.getLogger(__name__)


class EngineState(Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class KillSwitch:

    def __init__(self, initial_state: EngineState = EngineState.RUNNING) -> None:
        self._state = initial_state

    def enable(self) -> None:
        self._state = EngineState.RUNNING
        logger.info("KillSwitch: engine ENABLED — state=RUNNING")

    def disable(self) -> None:
        self._state = EngineState.STOPPED
        logger.info("KillSwitch: engine DISABLED — state=STOPPED")

    def pause(self) -> None:
        self._state = EngineState.PAUSED
        logger.info("KillSwitch: engine PAUSED")

    def resume(self) -> None:
        self._state = EngineState.RUNNING
        logger.info("KillSwitch: engine RESUMED — state=RUNNING")

    def panic_shutdown(self) -> None:
        self._state = EngineState.STOPPING
        logger.critical("KillSwitch: PANIC SHUTDOWN initiated — state=STOPPING")
        self._state = EngineState.STOPPED
        logger.critical("KillSwitch: engine STOPPED — no new trades accepted")

    def state(self) -> EngineState:
        return self._state

    def is_running(self) -> bool:
        return self._state == EngineState.RUNNING
