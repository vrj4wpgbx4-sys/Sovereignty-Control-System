"""
Sovereignty Control System — Lockdown State Effector (v0.9)

This effector implements a local-only, file-backed "lockdown state" control.

Design goals:

- Safe and bounded:
  - No external integrations
  - Only writes to a local JSON file under ./data/
- Explicit behavior:
  - action_type: "lockdown_state"
  - parameters:
      {
          "operation": "SET" | "CLEAR" | "TOGGLE",
          "reason": "<optional human-readable explanation>",
          "requested_by": "<optional identity label>",
      }
- Dry-run aware:
  - When dry_run=True, no file is modified; the effector only reports
    what WOULD have happened.

State file:

- Path: data/lockdown_state.json
- Shape:
    {
        "locked": bool,
        "updated_at": "<ISO-8601 string>",
        "reason": "<last change reason or empty>",
        "requested_by": "<last requester or empty>"
    }

Logging:

- This effector does NOT log to audit or enforcement logs.
  It only returns structured details via EffectorResult; a separate
  enforcement logger is responsible for persistence of those results.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .dispatcher import (
    Effector,
    EnforcementAction,
    EnforcementContext,
    EnforcementOutcome,
    EffectorResult,
)


DATA_DIR = Path("data")
LOCKDOWN_STATE_PATH = DATA_DIR / "lockdown_state.json"


@dataclass
class LockdownState:
    locked: bool
    updated_at: str
    reason: str
    requested_by: str

    @classmethod
    def default(cls) -> "LockdownState":
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            locked=False,
            updated_at=now,
            reason="",
            requested_by="",
        )

    @classmethod
    def from_file(cls, path: Path) -> "LockdownState":
        if not path.exists():
            return cls.default()
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            # Defensive: if the file is corrupted, treat as unlocked but do not
            # silently ignore the problem; surface it through the effector result.
            base = cls.default()
            base.reason = "Recovered from invalid lockdown_state.json"
            return base

        now = datetime.now(timezone.utc).isoformat()
        return cls(
            locked=bool(data.get("locked", False)),
            updated_at=str(data.get("updated_at", now)),
            reason=str(data.get("reason", "")),
            requested_by=str(data.get("requested_by", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def write_to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class LockdownStateEffector(Effector):
    """
    Effector for action_type="lockdown_state".

    Supported operations (action.parameters["operation"]):

      - "SET"    → locked = True
      - "CLEAR"  → locked = False
      - "TOGGLE" → locked = not locked

    Optional parameters:

      - "reason": str
      - "requested_by": str

    Behavior summary:

      - Reads current state from data/lockdown_state.json (or default unlocked).
      - Computes new state based on operation.
      - If dry_run=True:
          - Does NOT modify the file.
          - Returns outcome=NOOP if no change, or SUCCESS if change WOULD occur.
      - If dry_run=False:
          - Writes updated state to the file when a change occurs.
          - Returns outcome=NOOP if nothing changed, SUCCESS otherwise.
    """

    @property
    def action_type(self) -> str:
        return "lockdown_state"

    def execute(
        self,
        action: EnforcementAction,
        context: EnforcementContext,
        dry_run: bool = False,
    ) -> EffectorResult:
        params = action.parameters or {}
        operation = str(params.get("operation", "")).upper().strip()

        if operation not in {"SET", "CLEAR", "TOGGLE"}:
            return EffectorResult(
                outcome=EnforcementOutcome.NOT_APPLICABLE,
                action=action,
                details={
                    "reason": "Unsupported or missing operation",
                    "supported_operations": ["SET", "CLEAR", "TOGGLE"],
                    "provided_operation": operation or None,
                },
            )

        try:
            current_state = LockdownState.from_file(LOCKDOWN_STATE_PATH)
        except Exception as exc:  # noqa: BLE001
            # If we cannot even read the current state, fail fast for safety.
            return EffectorResult(
                outcome=EnforcementOutcome.FAILED,
                action=action,
                details={
                    "reason": "Failed to read current lockdown state",
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                },
            )

        new_locked = current_state.locked
        if operation == "SET":
            new_locked = True
        elif operation == "CLEAR":
            new_locked = False
        elif operation == "TOGGLE":
            new_locked = not current_state.locked

        # If nothing would change, report NOOP
        if new_locked == current_state.locked:
            return EffectorResult(
                outcome=EnforcementOutcome.NOOP,
                action=action,
                details={
                    "previous_state": current_state.to_dict(),
                    "new_state": current_state.to_dict(),
                    "operation": operation,
                    "dry_run": dry_run,
                    "note": "Lockdown state unchanged",
                },
            )

        # Construct updated state
        now = datetime.now(timezone.utc).isoformat()
        reason = str(params.get("reason", current_state.reason or "") or "")
        requested_by = str(
            params.get("requested_by", current_state.requested_by or "") or ""
        )

        updated_state = LockdownState(
            locked=new_locked,
            updated_at=now,
            reason=reason,
            requested_by=requested_by,
        )

        if not dry_run:
            try:
                updated_state.write_to_file(LOCKDOWN_STATE_PATH)
            except Exception as exc:  # noqa: BLE001
                return EffectorResult(
                    outcome=EnforcementOutcome.FAILED,
                    action=action,
                    details={
                        "reason": "Failed to write updated lockdown state",
                        "operation": operation,
                        "previous_state": current_state.to_dict(),
                        "intended_new_state": updated_state.to_dict(),
                        "exception_type": type(exc).__name__,
                        "exception_message": str(exc),
                    },
                )

        return EffectorResult(
            outcome=EnforcementOutcome.SUCCESS,
            action=action,
            details={
                "operation": operation,
                "previous_state": current_state.to_dict(),
                "new_state": updated_state.to_dict(),
                "dry_run": dry_run,
            },
        )
