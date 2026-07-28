from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Optional


class DecisionLedger:
    """A thread-safe, persistent, append-only Decision Ledger."""

    _file_lock = threading.Lock()

    def __init__(self, filepath: str = "decision_ledger.json") -> None:
        self.filepath = filepath
        self.lock = self._file_lock
        self.records: dict[str, dict[str, Any]] = {}
        self._load_ledger()

    def _load_ledger(self) -> None:
        with self.lock:
            if os.path.exists(self.filepath):
                try:
                    with open(self.filepath, "r") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            self.records = data
                except Exception:
                    pass

    def _save_ledger(self) -> None:
        with self.lock:
            try:
                with open(self.filepath, "w") as f:
                    json.dump(self.records, f, indent=2)
            except Exception:
                pass

    def append(self, decision_id: str, record: dict[str, Any]) -> None:
        """Append a new decision record to the ledger."""
        record["created_at"] = datetime.now(timezone.utc).isoformat()
        record["execution_status"] = "PENDING"
        record["outcome"] = None
        record["evaluation"] = None
        self.records[decision_id] = record
        self._save_ledger()

    def update_execution_status(self, decision_id: str, status: str) -> bool:
        """Update the execution status of an existing decision."""
        if decision_id in self.records:
            self.records[decision_id]["execution_status"] = status
            self._save_ledger()
            return True
        return False

    def attach_outcome(self, decision_id: str, outcome: dict[str, Any]) -> bool:
        """Attach trade execution outcomes (PnL, success, drawdown, exit reason) to a decision."""
        if decision_id in self.records:
            self.records[decision_id]["outcome"] = outcome
            self._save_ledger()
            return True
        return False

    def attach_evaluation(self, decision_id: str, evaluation: dict[str, Any]) -> bool:
        """Attach a quality evaluation score/metrics to a decision."""
        if decision_id in self.records:
            self.records[decision_id]["evaluation"] = evaluation
            self._save_ledger()
            return True
        return False

    def get_record(self, decision_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a single decision record by ID."""
        return self.records.get(decision_id)

    def get_all_records(self) -> list[dict[str, Any]]:
        """Retrieve all decision records ordered by created timestamp."""
        recs = list(self.records.values())
        recs.sort(key=lambda x: x.get("created_at", ""))
        return recs
