# core/process/resource_manifest.py
"""Resource Manifest representing limits and ceiling priorities."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResourceManifest:
    """Resource Manifest represents execution limits, requirements, and ceiling priorities."""

    cpu_ceiling: float = 1.0  # Normalized CPU requirement
    memory_limit_mb: int = 256
    ceiling_priority: int = 100  # Ceiling priority for immediate/critical tasks
    required_channels: list[str] = field(default_factory=list)
