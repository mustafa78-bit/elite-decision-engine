# core/process/authority.py
"""Process Authority separating execution credentials from queue priorities."""
from __future__ import annotations

from enum import Enum


class ProcessAuthority(Enum):
    """Authority defines execution credentials completely separate from scheduling priority."""

    READ_ONLY = "READ_ONLY"
    EXECUTE_PAPER = "EXECUTE_SUPERVISED"
    GOVERNANCE_SIGN_OFF = "GOVERNANCE_SIGN_OFF"
    ROOT_SYSTEM_ADMIN = "ROOT_SYSTEM_ADMIN"
