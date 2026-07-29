from __future__ import annotations

import logging
from typing import Dict, List, Optional, Type, Any
from services.intelligence.bus import IntelligenceServiceContract

logger = logging.getLogger(__name__)


class IntelligenceRegistry:
    """The dynamic service discovery, DI, versioning, and health reporting container

    for NEXUS intelligence subsystems. Decouples service creation from execution.
    """

    def __init__(self):
        self._services: Dict[str, IntelligenceServiceContract] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._health: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        service: IntelligenceServiceContract,
        version: str = "1.0.0",
        enabled: bool = True,
        dependencies: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Registers an active intelligence service instance into the registry."""
        name = service.get_service_name()
        self._services[name] = service
        self._configs[name] = {
            "version": version,
            "enabled": enabled,
            "dependencies": dependencies or {},
        }
        self._health[name] = {
            "invocations": 0,
            "successes": 0,
            "failures": 0,
            "circuit_broken": 0,
        }
        logger.info("Service '%s' (v%s) registered successfully (enabled=%s)", name, version, enabled)

    def is_enabled(self, name: str) -> bool:
        """Returns True if the service is registered and currently enabled."""
        if name not in self._configs:
            return False
        return self._configs[name]["enabled"]

    def set_enabled(self, name: str, enabled: bool) -> None:
        """Toggles the enabled/disabled configuration of a service."""
        if name in self._configs:
            self._configs[name]["enabled"] = enabled
            logger.info("Service '%s' configured to enabled=%s", name, enabled)

    def get_service(self, name: str) -> Optional[IntelligenceServiceContract]:
        """Fetches a registered service by name, if registered."""
        return self._services.get(name)

    def get_active_services(self) -> List[IntelligenceServiceContract]:
        """Returns all registered services that are enabled."""
        return [
            self._services[name]
            for name in self._services
            if self.is_enabled(name)
        ]

    def report_health(self, name: str, state: str) -> None:
        """Updates health statistics for a specific service execution."""
        if name not in self._health:
            return
        h = self._health[name]
        h["invocations"] += 1
        if state == "SUCCESS":
            h["successes"] += 1
        elif state == "DEGRADED":
            h["failures"] += 1
        elif state == "CIRCUIT_BROKEN":
            h["circuit_broken"] += 1

    def get_health_report(self) -> Dict[str, Any]:
        """Returns a snapshot of the health and execution statuses of all services."""
        report = {}
        for name in self._services:
            report[name] = {
                "version": self._configs[name]["version"],
                "enabled": self._configs[name]["enabled"],
                "health": self._health[name],
            }
        return report
