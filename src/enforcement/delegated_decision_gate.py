"""
Delegated Decision Enforcement Gate
Sovereignty Control System v0.7

This module extends the core enforcement gate with delegation awareness,
using a JSONL-backed delegation store.

It does NOT change the core decision outcomes.
It enforces that ALLOW decisions coming from delegates are only executed
when there is a valid, in-scope, time-bounded delegation grant.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import os

from enforcement.decision_gate import (
    GovernanceDecision,
    EnforcementRecord,
    DecisionOutcome,
    EnforcementResult,
)


DEFAULT_DELEGATION_STORE_PATH = os.path.join("data", "delegations.jsonl")


class DelegationStatus(Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class DelegationGrant:
    delegation_id: str
    delegator_identity: str
    delegate_identity: str
    scope: List[str]  # list of allowed requested_action names
    constraints: Dict[str, Any]
    valid_from: Optional[str]
    valid_until: Optional[str]
    status: DelegationStatus
    policy_ids: List[str]


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def load_delegation_grants(
    store_path: str = DEFAULT_DELEGATION_STORE_PATH,
) -> List[DelegationGrant]:
    """
    Load delegation grants from a JSONL file.

    Each line should be a JSON object with at least:
      - delegation_id
      - delegator_identity
      - delegate_identity
      - scope (list of requested_action names)
      - constraints (object)
      - valid_from (ISO string or null)
      - valid_until (ISO string or null)
      - status ("ACTIVE", "REVOKED", "EXPIRED")
      - policy_ids (list of strings)
    """
    grants: List[DelegationGrant] = []

    if not os.path.exists(store_path):
        return grants

    with open(store_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue

            try:
                status = DelegationStatus(raw.get("status", "EXPIRED"))
            except ValueError:
                status = DelegationStatus.EXPIRED

            scope = raw.get("scope") or []
            if not isinstance(scope, list):
                scope = [str(scope)]

            policy_ids = raw.get("policy_ids") or []
            if not isinstance(policy_ids, list):
                policy_ids = [str(policy_ids)]

            grant = DelegationGrant(
                delegation_id=str(raw.get("delegation_id", "")),
                delegator_identity=str(raw.get("delegator_identity", "")),
                delegate_identity=str(raw.get("delegate_identity", "")),
                scope=[str(s) for s in scope],
                constraints=raw.get("constraints") or {},
                valid_from=raw.get("valid_from"),
                valid_until=raw.get("valid_until"),
                status=status,
                policy_ids=[str(p) for p in policy_ids],
            )
            grants.append(grant)

    return grants


def is_delegation_applicable(
    *,
    grant: DelegationGrant,
    identity_label: str,
    requested_action: str,
    now: Optional[datetime] = None,
) -> bool:
    """
    Determine whether a delegation grant applies to the given identity and action
    at the current time.
    """
    if grant.status is not DelegationStatus.ACTIVE:
        return False

    if grant.delegate_identity != identity_label:
        return False

    # Scope: simple exact match or wildcard "ANY"
    if "ANY" not in grant.scope and requested_action not in grant.scope:
        return False

    now = now or datetime.now(timezone.utc)

    start = _parse_iso(grant.valid_from)
    end = _parse_iso(grant.valid_until)

    if start and now < start:
        return False
    if end and now > end:
        return False

    # Constraints are reserved for future policy-aware checks.
    # At v0.7, we only enforce time and scope.
    return True


def has_valid_delegation_for(
    *,
    identity_label: str,
    requested_action: str,
    store_path: str = DEFAULT_DELEGATION_STORE_PATH,
    now: Optional[datetime] = None,
) -> bool:
    """
    Returns True if there exists at least one ACTIVE, in-scope, time-valid
    delegation grant for this identity and requested_action.
    """
    grants = load_delegation_grants(store_path)
    now = now or datetime.now(timezone.utc)

    for grant in grants:
        if is_delegation_applicable(
            grant=grant,
            identity_label=identity_label,
            requested_action=requested_action,
            now=now,
        ):
            return True

    return False


def enforce_action_with_delegation(
    *,
    decision: GovernanceDecision,
    action_identifier: str,
    execute_action_callable,
    delegation_store_path: str = DEFAULT_DELEGATION_STORE_PATH,
    primary_authorities: Optional[List[str]] = None,
) -> EnforcementRecord:
    """
    Delegation-aware enforcement wrapper.

    Behavior:

    - If decision outcome is DENY -> BLOCKED (unchanged).
    - If decision outcome is REQUIRE_ADDITIONAL_APPROVAL -> PAUSED (unchanged).
    - If decision outcome is ALLOW:
        - If identity_label is in primary_authorities (e.g. sovereign owner),
          execute as usual.
        - Otherwise, require a valid delegation grant for
          (identity_label, requested_action). If missing, BLOCKED.

    This is a defense-in-depth enforcement layer. Delegation should already be
    considered by the decision engine, but enforcement will refuse to execute
    ALLOW decisions that come from identities without valid delegation.
    """

    # Default: no explicitly configured primary authorities.
    primary_authorities = primary_authorities or []

    identity_label = decision.identity_label
    requested_action = decision.requested_action

    # Fast path: non-ALLOW decisions behave as in the core gate.
    if decision.decision_outcome == DecisionOutcome.DENY:
        now = datetime.utcnow().isoformat() + "Z"
        return EnforcementRecord(
            decision_correlation_id=decision.decision_correlation_id,
            timestamp=now,
            action_identifier=action_identifier,
            enforcement_result=EnforcementResult.BLOCKED,
            enforcement_reason="Action blocked by governance decision.",
            policy_ids=decision.policy_ids,
        )

    if decision.decision_outcome == DecisionOutcome.REQUIRE_ADDITIONAL_APPROVAL:
        now = datetime.utcnow().isoformat() + "Z"
        return EnforcementRecord(
            decision_correlation_id=decision.decision_correlation_id,
            timestamp=now,
            action_identifier=action_identifier,
            enforcement_result=EnforcementResult.PAUSED,
            enforcement_reason=(
                "Action paused pending additional policy-defined approval."
            ),
            policy_ids=decision.policy_ids,
        )

    # At this point: decision_outcome == ALLOW

    # If the identity is a primary authority, execute without delegation checks.
    if identity_label in primary_authorities:
        now = datetime.utcnow().isoformat() + "Z"
        execute_action_callable()
        return EnforcementRecord(
            decision_correlation_id=decision.decision_correlation_id,
            timestamp=now,
            action_identifier=action_identifier,
            enforcement_result=EnforcementResult.EXECUTED,
            enforcement_reason=(
                "Action executed under primary authority "
                "with explicit governance authorization."
            ),
            policy_ids=decision.policy_ids,
        )

    # Otherwise, require a valid delegation grant for this identity and action.
    if not has_valid_delegation_for(
        identity_label=identity_label,
        requested_action=requested_action,
        store_path=delegation_store_path,
    ):
        now = datetime.utcnow().isoformat() + "Z"
        return EnforcementRecord(
            decision_correlation_id=decision.decision_correlation_id,
            timestamp=now,
            action_identifier=action_identifier,
            enforcement_result=EnforcementResult.BLOCKED,
            enforcement_reason=(
                "Action blocked: no valid, in-scope delegation grant for "
                f"identity '{identity_label}' and action '{requested_action}'."
            ),
            policy_ids=decision.policy_ids,
        )

    # Delegate has a valid grant: execute.
    now = datetime.utcnow().isoformat() + "Z"
    execute_action_callable()
    return EnforcementRecord(
        decision_correlation_id=decision.decision_correlation_id,
        timestamp=now,
        action_identifier=action_identifier,
        enforcement_result=EnforcementResult.EXECUTED,
        enforcement_reason=(
            "Action executed under valid, in-scope delegation grant with "
            "explicit governance authorization."
        ),
        policy_ids=decision.policy_ids,
    )
