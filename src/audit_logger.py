"""
Simple local audit logger.

This module does NOT enforce any storage backend or format long-term.
It just appends audit events as JSON lines to a file on disk so we can
see a concrete audit trail.

This belongs to the integration layer, not the core.
"""

import json
from pathlib import Path
from typing import Iterable

from audit_event import AuditEvent


class AuditLogger:
    """
    Appends AuditEvent records to a JSON lines file.

    Each line in the file is a single JSON object produced by
    AuditEvent.to_dict().
    """

    def __init__(self, log_path: str = "data/audit_log.jsonl"):
        self.log_path = Path(log_path)
        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: AuditEvent) -> None:
        """
        Append a single AuditEvent to the log file.
        """
        record = event.to_dict()
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def append_many(self, events: Iterable[AuditEvent]) -> None:
        """
        Append multiple AuditEvents in one go.
        """
        with self.log_path.open("a", encoding="utf-8") as f:
            for event in events:
                record = event.to_dict()
                f.write(json.dumps(record) + "\n")
