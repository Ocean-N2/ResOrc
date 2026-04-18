"""
Append-only JSON-Lines audit logger.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import List

from config.models import AuditEntry


class AuditLogger:

    def __init__(self, log_path: str = "audit.jsonl") -> None:
        self.log_path = log_path
        self._lock = threading.Lock()
        if not os.path.exists(log_path):
            with open(log_path, "w") as _:
                pass

    def log(self, entry: AuditEntry) -> None:
        record = {
            "timestamp": entry.timestamp, "actor": entry.actor,
            "action": entry.action, "detail": entry.detail,
            "phase_id": entry.phase_id,
        }
        with self._lock:
            with open(self.log_path, "a") as fh:
                fh.write(json.dumps(record) + "\n")

    def log_action(self, actor: str, action: str, detail: str,
                   phase_id: str = "") -> None:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor, action=action, detail=detail, phase_id=phase_id,
        )
        self.log(entry)

    def get_entries(self) -> List[AuditEntry]:
        entries: List[AuditEntry] = []
        with self._lock:
            with open(self.log_path, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    entries.append(AuditEntry(**data))
        return entries
