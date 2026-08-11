from __future__ import annotations

import logging
import threading
from typing import Any

from services.ai.provider import AIProvider, GenerationResult, HealthStatus
from services.ai.nvidia_provider import NVIDIAProvider

logger = logging.getLogger(__name__)


class MultiNVIDIAProvider(AIProvider):
    """A wrapper implementing the AIProvider interface that proactively load-splits

    requests across 2 NVIDIAProvider instances in a round-robin fashion,
    and falls back to the other provider if one fails.
    """

    def __init__(self, provider1: NVIDIAProvider, provider2: NVIDIAProvider) -> None:
        self._providers = [provider1, provider2]
        self._index = 0
        self._lock = threading.Lock()

    @property
    def model(self) -> str:
        return self._providers[0].model

    def _get_next_provider(self) -> tuple[NVIDIAProvider, NVIDIAProvider]:
        with self._lock:
            p1 = self._providers[self._index]
            self._index = (self._index + 1) % 2
            p2 = self._providers[self._index]
            return p1, p2

    def generate(self, prompt: str, **kwargs: Any) -> GenerationResult:
        p1, p2 = self._get_next_provider()
        res = p1.generate(prompt, **kwargs)
        if res.error:
            logger.warning("Primary NVIDIA provider failed (error: %s). Trying secondary provider...", res.error)
            return p2.generate(prompt, **kwargs)
        return res

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> GenerationResult:
        p1, p2 = self._get_next_provider()
        res = p1.chat(messages, **kwargs)
        if res.error:
            logger.warning("Primary NVIDIA provider failed (error: %s). Trying secondary provider...", res.error)
            return p2.chat(messages, **kwargs)
        return res

    def health(self) -> HealthStatus:
        h1 = self._providers[0].health()
        h2 = self._providers[1].health()

        connected = h1.connected and h2.connected
        errors = []
        if h1.error:
            errors.append(f"Key 1: {h1.error}")
        if h2.error:
            errors.append(f"Key 2: {h2.error}")

        combined_error = " | ".join(errors) if errors else None
        latency = max(h1.latency_ms, h2.latency_ms)

        return HealthStatus(
            connected=connected,
            model=self.model,
            latency_ms=round(latency, 2),
            provider="nvidia-multi",
            error=combined_error,
        )

    def close(self) -> None:
        for p in self._providers:
            try:
                p.close()
            except Exception as e:
                logger.error("Failed to close NVIDIAProvider: %s", e)
