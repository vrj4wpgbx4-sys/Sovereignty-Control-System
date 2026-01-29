"""
Delegation Context Resolver
Sovereignty Control System — v0.8 (Delegation Enforcement Preparation)

This module provides a small, focused hook that the authority/decision engine
can call to understand delegation context for a given decision:

    - Who is acting?
    - Are they acting as a delegate?
    - If so, for which principal(s)?
    - Under which delegation record(s)?
    - Does any active delegation *in principle* allow this action
      in the current system state at the given time?

This module does NOT:
    - change any decision outcomes by itself
    - execute or enforce any actions
    - modify or write delegation records

It is a pure, read-only helper that prepares v0.8 delegation-aware decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from delegation_registry import (
    Delegation,
    find_applicable_delegations,
)


@dataclass(frozen=True)
class DelegationContext:
    """
    Resolved delegation context for a single decision evaluation.

    Fields:
        identity_label:
            The identity that initiated the request (the actor).

        is_delegated:
            True if there is at least one active delegation that applies to
            this identity, requested action, and system state at the decision time.

        principal_identity_labels:
            The distinct set of principals from which authority is derived,
            if delegation is in effect. Empty when not delegated.

        applicable_delegations:
            The list of delegation records that match this identity, action,
            and system state at the decision time.

        decision_timestamp:
            The timestamp used to evaluate delegation validity.
    """

    identity_label: str
    is_delegated: bool
    principal_identity_labels: List[str]
    applicable_delegations: List[Delegation]
    decision_timestamp: datetime


def _parse_decision_timestamp(timestamp_str: Optional[str]) -> datetime:
    """
    Parse an ISO-8601-like decision timestamp into a timezone-aware datetime.

    If parsing fails or no timestamp is provided, falls back to "now" in UTC.
    """
    if not timestamp_str:
        return datetime.now(timezone.utc)

    try:
        value = timestamp_str
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def resolve_delegation_context(
    *,
    identity_label: str,
    requested_action: str,
    system_state: str,
    decision_timestamp: Optional[str] = None,
    registry_path: str = None,
) -> DelegationContext:
    """
    Resolve delegation context for a given decision.

    This function is intended to be called by the authority/decision engine
    as part of v0.8 delegation-aware evaluation.

    It is read-only and side-effect free.

    Args:
        identity_label:
            The identity initiating the request (e.g., "Guardian", "Ronald").

        requested_action:
            The action/permission being requested, such as
            "AUTHORIZE_EMERGENCY_LOCKDOWN".

        system_state:
            The current system state (e.g., "CRISIS", "NORMAL").

        decision_timestamp:
            The timestamp at which the decision is being evaluated, as a string
            (ISO-8601-like, e.g. "2026-01-24T00:00:00Z"). If omitted or invalid,
            the current UTC time is used.

        registry_path:
            Optional override path for the delegation registry file. If not
            provided, the default path from delegation_registry is used.

    Returns:
        DelegationContext describing whether this identity is acting under
        delegation and, if so, from which principals and under which records.
    """
    resolved_time = _parse_decision_timestamp(decision_timestamp)

    applicable: List[Delegation] = find_applicable_delegations(
        delegate_identity_label=identity_label,
        requested_action=requested_action,
        system_state=system_state,
        now=resolved_time,
        registry_path=registry_path if registry_path is not None else "",
    )

    # If registry_path is "", find_applicable_delegations will fall back to its
    # default path. This keeps the hook simple while still allowing overrides.

    principal_labels = sorted(
        {d.principal_identity_label for d in applicable if d.principal_identity_label}
    )

    return DelegationContext(
        identity_label=identity_label,
        is_delegated=len(applicable) > 0,
        principal_identity_labels=principal_labels,
        applicable_delegations=applicable,
        decision_timestamp=resolved_time,
    )


if __name__ == "__main__":
    # Simple local smoke test; safe to run manually.
    # This block does not affect production use.
    ctx = resolve_delegation_context(
        identity_label="Guardian",
        requested_action="AUTHORIZE_EMERGENCY_LOCKDOWN",
        system_state="CRISIS",
        decision_timestamp=None,
    )

    print("== Delegation Context Test ==")
    print(f"Identity          : {ctx.identity_label}")
    print(f"Is delegated      : {ctx.is_delegated}")
    print(f"Principals        : {ctx.principal_identity_labels}")
    print(f"Decision time (UTC): {ctx.decision_timestamp.isoformat()}")
    if ctx.applicable_delegations:
        print("Applicable delegations:")
        for d in ctx.applicable_delegations:
            print(f"  - {d.delegation_id} (Principal={d.principal_identity_label})")
    else:
        print("No applicable delegations for this context.")
