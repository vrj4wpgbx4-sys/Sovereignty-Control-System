"""
Sovereignty Control System - Read-Only Decision Visibility (v0.6)

This CLI provides a safe, read-only view of recent governance decisions
and enforcement outcomes by reading the append-only audit log.

It does NOT:
- execute governed actions
- approve or deny requests
- modify policies, configs, or records

It is intended for trustees, auditors, and reviewers.
"""

import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, List


DEFAULT_AUDIT_LOG_PATH = os.path.join("data", "audit_log.jsonl")


def load_audit_events(audit_log_path: str) -> List[Dict[str, Any]]:
    """Load all events from the append-only JSONL audit log."""
    events: List[Dict[str, Any]] = []

    if not os.path.exists(audit_log_path):
        print(f"[INFO] No audit log found at: {audit_log_path}")
        return events

    with open(audit_log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                # Malformed lines are ignored but should not stop visibility
                continue

    return events


def format_timestamp(ts: str) -> str:
    """Format an ISO-like timestamp for display. Falls back to raw string."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.isoformat(timespec="seconds") + "Z"
    except Exception:
        return ts


def print_event(event: Dict[str, Any]) -> None:
    """Print a single audit event in a reviewer-friendly format."""

    decision_ts = format_timestamp(event.get("timestamp", ""))
    identity = event.get("identity_label", "?")
    requested = (
        event.get("requested_permission_name")
        or event.get("requested_action")
        or "?"
    )
    system_state = event.get("system_state", "?")
    decision = event.get("decision", event.get("decision_outcome", "?"))
    policy_ids = event.get("policy_ids", [])
    reason = event.get("reason", event.get("decision_reason", ""))

    # Optional enforcement linkage, if present
    enforcement_result = event.get("enforcement_result")
    enforcement_reason = event.get("enforcement_reason")
    correlation_id = event.get("decision_correlation_id")

    print("------------------------------------------------------------")
    print(f"Timestamp        : {decision_ts}")
    print(f"Identity         : {identity}")
    print(f"Requested action : {requested}")
    print(f"System state     : {system_state}")
    print(f"Decision outcome : {decision}")
    print(f"Policy IDs       : {', '.join(policy_ids) if policy_ids else '-'}")
    print(f"Reason           : {reason or '-'}")

    if correlation_id:
        print(f"Correlation ID   : {correlation_id}")

    if enforcement_result:
        print(f"Enforcement      : {enforcement_result}")
        if enforcement_reason:
            print(f"Enforcement note : {enforcement_reason}")

    print("------------------------------------------------------------")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only view of recent governance decisions and enforcement "
            "outcomes from the Sovereignty Control System audit log."
        )
    )
    parser.add_argument(
        "--audit-log",
        default=DEFAULT_AUDIT_LOG_PATH,
        help=f"Path to the audit log JSONL file (default: {DEFAULT_AUDIT_LOG_PATH})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of most recent events to display (default: 10)",
    )

    args = parser.parse_args()

    events = load_audit_events(args.audit_log)
    if not events:
        print("[INFO] No audit events to display.")
        return

    # Show newest first
    events_to_show = list(reversed(events))[: max(args.limit, 1)]

    print("== Sovereignty Control System - Recent Decisions ==")
    print(f"(showing {len(events_to_show)} most recent event(s))\n")

    for event in events_to_show:
        print_event(event)


if __name__ == "__main__":
    main()
