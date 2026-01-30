"""
Sovereignty Control System — Enforcement Logger (v0.9)

This module provides a centralized, append-only logger for enforcement events.

Responsibilities:

- Accept a fully evaluated EnforcementResult
- Convert it to a JSON-serializable dict via result.to_dict()
- Append it as a single JSON line to data/enforcement_log.jsonl
- Ensure the data directory exists
- Do not perform any enforcement or decision logic

Separation of concerns:

    decision         → authority engine
    enforcement      → dispatcher + effectors
    enforcement log  → this module

This mirrors the audit logging pattern, but is dedicated to enforcement
effects so that decision and enforcement trails remain distinguishable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .dispatcher import EnforcementResult

DATA_DIR = Path("data")
ENFORCEMENT_LOG_PATH = DATA_DIR / "enforcement_log.jsonl"


def _ensure_data_dir_exists() -> None:
    """
    Ensure that the base data directory exists.

    This is idempotent and safe to call on every log operation.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _serialize_log_record(
    result: EnforcementResult,
    additional_metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Build the final record to be written as a JSON line.

    The structure is:

        {
            "timestamp": "<ISO-8601 UTC>",
            "kind": "enforcement_event",
            "payload": <EnforcementResult.to_dict()>,
            "meta": { ... optional extra fields ... }
        }

    This keeps the enforcement payload stable while allowing future metadata
    (e.g., logger version, process info) without breaking consumers.
    """
    payload = result.to_dict()
    meta = dict(additional_metadata or {})

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kind": "enforcement_event",
        "payload": payload,
        "meta": meta,
    }


def append_enforcement_result(
    result: EnforcementResult,
    *,
    log_path: Path | None = None,
    additional_metadata: Dict[str, Any] | None = None,
) -> None:
    """
    Append an enforcement result to the enforcement log as a single JSON line.

    Parameters
    ----------
    result:
        The fully evaluated EnforcementResult returned by the dispatcher.

    log_path:
        Optional override for the log path (primarily for testing).
        Defaults to data/enforcement_log.jsonl.

    additional_metadata:
        Optional dictionary of extra metadata to include under the "meta" key.
        This must be JSON-serializable.

    Behavior
    --------
    - Ensures the data directory exists.
    - Opens the log file in append mode.
    - Writes exactly one line of JSON per call.
    - Does not perform any decision or enforcement logic.
    - Raises exceptions on I/O or serialization failure; it does not silently
      swallow errors. Callers can decide how to handle failures.
    """
    _ensure_data_dir_exists()
    path = log_path or ENFORCEMENT_LOG_PATH

    record = _serialize_log_record(result, additional_metadata=additional_metadata)

    # We keep this intentionally simple and explicit: one JSON object per line.
    with path.open("a", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
        f.write("\n")


__all__ = [
    "ENFORCEMENT_LOG_PATH",
    "append_enforcement_result",
]
