import signal
import threading
import time
from typing import Any, Callable, List, Optional


class Scheduler:

    def __init__(self, interval: float = 10.0):
        self._interval = interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tasks: List[Callable] = []
        self._shutdown_event = threading.Event()

    def add_task(self, task: Callable) -> None:
        self._tasks.append(task)

    def _run_loop(self) -> None:
        while not self._shutdown_event.is_set():
            for task in self._tasks:
                if self._shutdown_event.is_set():
                    break
                try:
                    task()
                except Exception:
                    pass
            self._shutdown_event.wait(timeout=self._interval)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._shutdown_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._shutdown_event.set()
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

    @property
    def is_running(self) -> bool:
        return self._running


class GracefulShutdown:

    def __init__(self):
        self._handlers: List[Callable] = []
        self._shutdown_in_progress = False

    def add_handler(self, handler: Callable) -> None:
        self._handlers.append(handler)

    def shutdown(self) -> None:
        if self._shutdown_in_progress:
            return
        self._shutdown_in_progress = True
        for handler in self._handlers:
            try:
                handler()
            except Exception:
                pass

    def install_signal_handlers(self) -> None:
        signal.signal(signal.SIGINT, lambda sig, frame: self.shutdown())
        signal.signal(signal.SIGTERM, lambda sig, frame: self.shutdown())
