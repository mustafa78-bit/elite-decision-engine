# core/process/process_table.py
"""Channel-scoped Process Table managing all process identities."""
from __future__ import annotations

from typing import Dict, List, Optional
from core.process.model import CognitiveProcess


class ChannelScopedProcessTable:
    """Manages tracking, registration, and lookup of processes grouped by logical channels."""

    def __init__(self) -> None:
        self._table: Dict[str, Dict[str, CognitiveProcess]] = {}

    def register_process(self, process: CognitiveProcess) -> None:
        """Register process into its defined logical channel scope."""
        channel = process.channel or "default"
        if channel not in self._table:
            self._table[channel] = {}
        self._table[channel][process.id] = process

    def get_process(self, process_id: str, channel: Optional[str] = None) -> Optional[CognitiveProcess]:
        """Lookup a process within a given channel, or across all channels if not specified."""
        if channel:
            return self._table.get(channel, {}).get(process_id)
        # Search across all channels
        for ch in self._table.values():
            if process_id in ch:
                return ch[process_id]
        return None

    def get_all_in_channel(self, channel: str) -> List[CognitiveProcess]:
        """Get all processes registered in a specific channel."""
        return list(self._table.get(channel, {}).values())

    def get_all_processes(self) -> List[CognitiveProcess]:
        """Get a flat list of all registered processes across all channels."""
        all_procs = []
        for ch_dict in self._table.values():
            all_procs.extend(ch_dict.values())
        return all_procs

    def remove_process(self, process_id: str, channel: Optional[str] = None) -> None:
        """Remove process from process table."""
        if channel:
            if channel in self._table and process_id in self._table[channel]:
                del self._table[channel][process_id]
        else:
            for ch in self._table.values():
                if process_id in ch:
                    del ch[process_id]
