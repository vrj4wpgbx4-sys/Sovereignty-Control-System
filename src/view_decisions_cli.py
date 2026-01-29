"""
Decision Visibility CLI (v0.7)
Sovereignty Control System

Purpose:
    - Read and display governance decisions from data/audit_log.jsonl
    - For each decision, show:
        - identity
        - requested action
        - system state
        - decision outcome
        - policy IDs
        - human-readable reason
    - Additionally, overlay delegation information:
        - which delegations were active for this identity
          at the time of the decision
        - whether those delegations could have allowed the action
          in the given system state

This CLI is strictly read-only:
    - It does not modify audit logs.
    - It does not create, change, or revoke delegations.
    - It does not execute any governed action.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from delegation_registry import (
    Delegation,
    find_applicable_delegations,
)

AUDIT_LOG_PATH = os.path.join("data", "audit_log.jsonl")
DELEGATION_REGISTRY_PATH = os.path.join("data", "delegations.jsonl")


def _parse_timestamp(value: str) -> Optional[datetime]:
    """Parse an ISO 8601-like timestamp into a timezone-aware datetime."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except Exception:
        return None


def load_audit_events(path: str = AUDIT_LOG_PATH) -> List[Dict[str, Any]]:
    """
    Load all audit events from the append-only JSONL audit log.

    Each line must be a JSON object. Malformed lines are skipped.
    """
    events: List[Dict[str, Any]] = []

    if not os.path.exists(path):
        return events

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # Skip lines that are not valid JSON
                continue
            events.append(record)

    return events


def _print_delegation_overlay(
    *,
    identity_label: str,
    requested_action: str,
    system_state: str,
    decision_timestamp: Optional[str],
) -> None:
    """
    Print delegation information relevant to a specific decision.

    This is an overlay: it does not assert that delegation was *required*,
    only that delegations existed which could, in principle, allow this
    identity to act under the configured model.
    """
    decision_time = _parse_timestamp(decision_timestamp) if decision_timestamp else None

    applicable: List[Delegation] = find_applicable_delegations(
        delegate_identity_label=identity_label,
        requested_action=requested_action,
        system_state=system_state,
        now=decision_time,
        registry_path=DELEGATION_REGISTRY_PATH,
    )

    if not applicable:
        print("Delegation context : none (no matching active delegations)")
        return

    print("Delegation context : matching active delegation(s) found:")
    for d in applicable:
        print(f"  - Delegation ID : {d.delegation_id}")
        print(f"    Principal     : {d.principal_identity_label}")
        actions = d.delegation_scope.get("actions") or []
        states = d.delegation_scope.get("system_states") or []
        print(
            f"    Scope         : actions={actions if actions else ['*']} "
            f"states={states if states else ['*']}"
        )
    return


def _iter_events_with_timestamp_sorted(
    events: Iterable[Dict[str, Any]]
) -> Iterable[Dict[str, Any]]:
    """
    Yield events sorted by their parsed timestamp, newest first.

    Events that cannot be parsed for timestamp are placed at the end.
    """
    def sort_key(ev: Dict[str, Any]) -> Any:
        ts = ev.get("timestamp")
        dt = _parse_timestamp(ts) if ts else None
        # Sort by datetime descending; None goes last
        return (dt is None, dt if dt is not None else datetime.min.replace(tzinfo=timezone.utc))

    return sorted(events, key=sort_key, reverse=True)


def print_decision_event(event: Dict[str, Any]) -> None:
    """Pretty-print a single decision event with delegation overlay."""
    identity = event.get("identity_label", "-")
    requested = event.get("requested_permission_name", "-")
    system_state = event.get("system_state", "-")
    decision = event.get("decision", "-")
    policy_ids = event.get("policy_ids") or []
    timestamp = event.get("timestamp", "-")
    reason = event.get("reason", "-")

    print("============================================================")
    print(f"Timestamp        : {timestamp}")
    print(f"Identity         : {identity}")
    print(f"Requested action : {requested}")
    print(f"System state     : {system_state}")
    print(f"Decision outcome : {decision}")
    print(f"Policy IDs       : {', '.join(policy_ids) if policy_ids else '-'}")
    print(f"Reason           : {reason}")
    _print_delegation_overlay(
        identity_label=identity,
        requested_action=requested,
        system_state=system_state,
        decision_timestamp=timestamp,
    )
    print("============================================================")
    print()


def main(limit: Optional[int] = None) -> None:
    """
    Entry point for the decision visibility CLI.

    Args:
        limit: optional maximum number of events to display (newest first).
    """
    events = load_audit_events(AUDIT_LOG_PATH)
    if not events:
        print("No audit events found.")
        return

    sorted_events = list(_iter_events_with_timestamp_sorted(events))

    if limit is not None and limit > 0:
        sorted_events = sorted_events[:limit]

    print("== Sovereignty Control System — Decision Visibility (v0.7) ==\n")
    for ev in sorted_events:
        print_decision_event(ev)


if __name__ == "__main__":
    # Simple CLI runner: currently no argument parsing; extend as needed.
    main()
