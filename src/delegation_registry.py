"""
Delegation Registry
Sovereignty Control System v0.7

Read-only registry for delegated authority.

- Loads delegation records from an append-only JSONL file.
- Provides helpers to:
  - list active delegations
  - resolve whether a delegate is allowed to request a given action
    under a given system state at a given time.

This module does NOT:
- execute any governed actions
- modify or write delegation records
- change policies or system state
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import json
import os

DEFAULT_DELEGATION_LOG_PATH = os.path.join("data", "delegations.jsonl")


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601-like timestamp into a timezone-aware datetime."""
    if not value:
        return None
    try:
        # Accept both "...Z" and "+00:00" styles
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except Exception:
        return None


@dataclass(frozen=True)
class Delegation:
    delegation_id: str
    principal_identity_label: str
    delegate_identity_label: str
    delegation_scope: Dict[str, Any]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    policy_ids: List[str]
    created_timestamp: Optional[datetime]
    created_reason: str
    revoked_timestamp: Optional[datetime] = None
    revoked_reason: Optional[str] = None

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if this delegation is currently active."""
        if now is None:
            now = datetime.now(timezone.utc)

        # Revoked delegations are not active
        if self.revoked_timestamp is not None and self.revoked_timestamp <= now:
            return False

        if self.valid_from is not None and now < self.valid_from:
            return False

        if self.valid_until is not None and now > self.valid_until:
            return False

        return True

    def allows(
        self,
        *,
        requested_action: str,
        system_state: str,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        Return True if this delegation, in principle, allows the delegate
        to request the given action in the given system state at the given time.
        """
        if not self.is_active(now=now):
            return False

        actions = self.delegation_scope.get("actions") or []
        states = self.delegation_scope.get("system_states") or []

        # If scope lists actions, the requested action must be included.
        if actions and requested_action not in actions:
            return False

        # If scope lists system_states, the current state must be included.
        if states and system_state not in states:
            return False

        # Thresholds and more complex conditions can be added here in later versions.
        return True


def load_delegations(
    path: str = DEFAULT_DELEGATION_LOG_PATH,
) -> List[Delegation]:
    """
    Load all delegation records from the JSONL registry.

    Each line must be a JSON object matching the Delegation schema.
    Malformed lines are skipped but do not stop processing.
    """
    delegations: List[Delegation] = []

    if not os.path.exists(path):
        # No registry yet is treated as 'no delegations'
        return delegations

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # Ignore malformed lines rather than failing hard
                continue

            delegations.append(
                Delegation(
                    delegation_id=record.get("delegation_id", ""),
                    principal_identity_label=record.get(
                        "principal_identity_label", ""
                    ),
                    delegate_identity_label=record.get(
                        "delegate_identity_label", ""
                    ),
                    delegation_scope=record.get("delegation_scope") or {},
                    valid_from=_parse_timestamp(record.get("valid_from")),
                    valid_until=_parse_timestamp(record.get("valid_until")),
                    policy_ids=list(record.get("policy_ids") or []),
                    created_timestamp=_parse_timestamp(
                        record.get("created_timestamp")
                    ),
                    created_reason=record.get("created_reason", ""),
                    revoked_timestamp=_parse_timestamp(
                        record.get("revoked_timestamp")
                    ),
                    revoked_reason=record.get("revoked_reason"),
                )
            )

    return delegations


def find_applicable_delegations(
    *,
    delegate_identity_label: str,
    requested_action: str,
    system_state: str,
    now: Optional[datetime] = None,
    registry_path: str = DEFAULT_DELEGATION_LOG_PATH,
) -> List[Delegation]:
    """
    Return all active delegations for this delegate that would allow
    the requested action under the given system state.
    """
    all_delegations = load_delegations(registry_path)
    applicable: List[Delegation] = []

    for delegation in all_delegations:
        if delegation.delegate_identity_label != delegate_identity_label:
            continue
        if delegation.allows(
            requested_action=requested_action,
            system_state=system_state,
            now=now,
        ):
            applicable.append(delegation)

    return applicable


def list_active_delegations(
    *,
    now: Optional[datetime] = None,
    registry_path: str = DEFAULT_DELEGATION_LOG_PATH,
) -> List[Delegation]:
    """
    Return all currently active delegations, regardless of scope.
    """
    all_delegations = load_delegations(registry_path)
    return [d for d in all_delegations if d.is_active(now=now)]


def _print_delegation(d: Delegation) -> None:
    """Utility: pretty-print a delegation for CLI inspection."""
    print("------------------------------------------------------------")
    print(f"Delegation ID   : {d.delegation_id}")
    print(f"Principal       : {d.principal_identity_label}")
    print(f"Delegate        : {d.delegate_identity_label}")
    actions = d.delegation_scope.get("actions") or []
    states = d.delegation_scope.get("system_states") or []
    print(f"Actions         : {', '.join(actions) if actions else '-'}")
    print(f"System states   : {', '.join(states) if states else '-'}")
    print(f"Policy IDs      : {', '.join(d.policy_ids) if d.policy_ids else '-'}")
    vf = d.valid_from.isoformat() if d.valid_from else "-"
    vu = d.valid_until.isoformat() if d.valid_until else "-"
    print(f"Valid from      : {vf}")
    print(f"Valid until     : {vu}")
    if d.revoked_timestamp:
        print(f"Revoked at      : {d.revoked_timestamp.isoformat()}")
        print(f"Revoked reason  : {d.revoked_reason or '-'}")
    print(f"Created reason  : {d.created_reason}")
    print("------------------------------------------------------------")
    print()


if __name__ == "__main__":
    # Simple read-only CLI for testing and oversight.
    now = datetime.now(timezone.utc)
    active = list_active_delegations(now=now)

    if not active:
        print("No active delegations found.")
    else:
        print("== Active Delegations ==")
        for d in active:
            _print_delegation(d)
