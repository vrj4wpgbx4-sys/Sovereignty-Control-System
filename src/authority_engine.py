"""
Authority / Decision Engine
Sovereignty Control System — v0.8 (Delegation-Aware Evaluation)

This module evaluates governance decisions based on:

- identity (who is acting),
- requested permission (what they are trying to do),
- system state (context),
- and, starting in v0.8, delegation context (are they acting as a delegate).

It returns a structured decision record that can be:

- shown in the CLI,
- logged to the audit log,
- correlated with enforcement and oversight systems.

Delegation in v0.8 is handled conservatively:

- If no applicable delegation exists where one is required, the decision
  fails closed (DENY or REQUIRE_ADDITIONAL_APPROVAL).
- Delegation never silently expands power beyond policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from delegation_context import resolve_delegation_context, DelegationContext


class DecisionOutcome(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_ADDITIONAL_APPROVAL = "REQUIRE_ADDITIONAL_APPROVAL"


@dataclass(frozen=True)
class DecisionRecord:
    identity_label: str
    requested_permission_name: str
    system_state: str
    decision: DecisionOutcome
    policy_ids: List[str]
    reason: str
    timestamp: str
    # Delegation-aware fields (v0.8)
    delegate_identity_label: Optional[str] = None
    principal_identity_labels: Optional[List[str]] = None
    delegation_ids: Optional[List[str]] = None


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _evaluate_core_policies(
    *,
    identity_label: str,
    requested_permission_name: str,
    system_state: str,
    delegation_ctx: DelegationContext,
) -> DecisionRecord:
    """
    Core policy evaluation, including delegation-aware rules.

    This is intentionally small and explicit for v0.8. As the policy surface
    grows, this can be refactored into a more generic rule engine.
    """
    ts = delegation_ctx.decision_timestamp.isoformat(timespec="seconds").replace("+00:00", "Z")

    # Defaults for delegation fields in the record.
    delegate_identity_label: Optional[str] = None
    principal_identity_labels: Optional[List[str]] = None
    delegation_ids: Optional[List[str]] = None

    if delegation_ctx.is_delegated:
        delegate_identity_label = identity_label
        principal_identity_labels = delegation_ctx.principal_identity_labels or []
        delegation_ids = [d.delegation_id for d in delegation_ctx.applicable_delegations]

    # --- Example policy set for emergency lockdown ---

    # 1. Sovereign Owner — Emergency Lockdown
    if identity_label == "SovereignOwner" and requested_permission_name == "AUTHORIZE_EMERGENCY_LOCKDOWN":
        if system_state == "CRISIS":
            return DecisionRecord(
                identity_label=identity_label,
                requested_permission_name=requested_permission_name,
                system_state=system_state,
                decision=DecisionOutcome.ALLOW,
                policy_ids=["policy-001"],
                reason="Sovereign owner authorizes emergency lockdown in CRISIS state.",
                timestamp=ts,
                delegate_identity_label=delegate_identity_label,
                principal_identity_labels=principal_identity_labels,
                delegation_ids=delegation_ids,
            )
        else:
            return DecisionRecord(
                identity_label=identity_label,
                requested_permission_name=requested_permission_name,
                system_state=system_state,
                decision=DecisionOutcome.DENY,
                policy_ids=["policy-001"],
                reason="Emergency lockdown is not permitted for Sovereign owner outside CRISIS state.",
                timestamp=ts,
                delegate_identity_label=delegate_identity_label,
                principal_identity_labels=principal_identity_labels,
                delegation_ids=delegation_ids,
            )

    # 2. Guardian — Emergency Lockdown (delegation-aware, conservative)
    #
    #    Business rule:
    #    - In NORMAL state: never allowed.
    #    - In CRISIS state:
    #        - If no valid delegation exists -> DENY (hard fail, no silent authority).
    #        - If valid delegation exists    -> REQUIRE_ADDITIONAL_APPROVAL
    #          (still requires multi-party confirmation under policy-002).
    #
    if identity_label == "Guardian" and requested_permission_name == "AUTHORIZE_EMERGENCY_LOCKDOWN":
        if system_state != "CRISIS":
            return DecisionRecord(
                identity_label=identity_label,
                requested_permission_name=requested_permission_name,
                system_state=system_state,
                decision=DecisionOutcome.DENY,
                policy_ids=["policy-002"],
                reason="Guardian cannot request emergency lockdown outside CRISIS state.",
                timestamp=ts,
                delegate_identity_label=delegate_identity_label,
                principal_identity_labels=principal_identity_labels,
                delegation_ids=delegation_ids,
            )

        # CRISIS state
        if not delegation_ctx.is_delegated:
            return DecisionRecord(
                identity_label=identity_label,
                requested_permission_name=requested_permission_name,
                system_state=system_state,
                decision=DecisionOutcome.DENY,
                policy_ids=["policy-002-no-delegation"],
                reason=(
                    "Guardian attempted emergency lockdown in CRISIS state "
                    "without an active delegation record from the Sovereign owner."
                ),
                timestamp=ts,
                delegate_identity_label=delegate_identity_label,
                principal_identity_labels=principal_identity_labels,
                delegation_ids=delegation_ids,
            )

        # Has valid delegation in CRISIS
        return DecisionRecord(
            identity_label=identity_label,
            requested_permission_name=requested_permission_name,
            system_state=system_state,
            decision=DecisionOutcome.REQUIRE_ADDITIONAL_APPROVAL,
            policy_ids=["policy-002"],
            reason=(
                "Guardian attempts emergency lockdown in CRISIS state under valid delegation; "
                "policy requires additional approval before execution."
            ),
            timestamp=ts,
            delegate_identity_label=delegate_identity_label,
            principal_identity_labels=principal_identity_labels,
            delegation_ids=delegation_ids,
        )

    # 3. Default rule — Unknown or unsupported actions/identities
    return DecisionRecord(
        identity_label=identity_label,
        requested_permission_name=requested_permission_name,
        system_state=system_state,
        decision=DecisionOutcome.DENY,
        policy_ids=["policy-000-unknown"],
        reason="Requested action is not permitted under the current governance policies.",
        timestamp=ts,
        delegate_identity_label=delegate_identity_label,
        principal_identity_labels=principal_identity_labels,
        delegation_ids=delegation_ids,
    )


def evaluate_decision(
    identity_label: str,
    requested_permission_name: str,
    system_state: str,
    decision_timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point: evaluate a governance decision for the given identity,
    requested permission, and system state.

    This is the function the CLI and audit layers should call.

    Returns:
        A dictionary representing the decision record, suitable for:
        - printing in the CLI,
        - logging to the audit log,
        - correlation with enforcement and oversight.
    """
    # Resolve delegation context (read-only, no side effects).
    delegation_ctx = resolve_delegation_context(
        identity_label=identity_label,
        requested_action=requested_permission_name,
        system_state=system_state,
        decision_timestamp=decision_timestamp,
    )

    decision_record = _evaluate_core_policies(
        identity_label=identity_label,
        requested_permission_name=requested_permission_name,
        system_state=system_state,
        delegation_ctx=delegation_ctx,
    )

    # Convert dataclass to a simple dict for external consumers.
    result: Dict[str, Any] = {
        "identity_label": decision_record.identity_label,
        "requested_permission_name": decision_record.requested_permission_name,
        "system_state": decision_record.system_state,
        "decision": decision_record.decision.value,
        "policy_ids": decision_record.policy_ids,
        "reason": decision_record.reason,
        "timestamp": decision_record.timestamp,
    }

    if decision_record.delegate_identity_label is not None:
        result["delegate_identity_label"] = decision_record.delegate_identity_label
    if decision_record.principal_identity_labels:
        result["principal_identity_labels"] = decision_record.principal_identity_labels
    if decision_record.delegation_ids:
        result["delegation_ids"] = decision_record.delegation_ids

    return result


# Backward-compatible aliases, in case existing code uses older names.
def evaluate_permission(
    identity_label: str,
    requested_permission_name: str,
    system_state: str,
    decision_timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    return evaluate_decision(identity_label, requested_permission_name, system_state, decision_timestamp)


def evaluate_governance_decision(
    identity_label: str,
    requested_permission_name: str,
    system_state: str,
    decision_timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    return evaluate_decision(identity_label, requested_permission_name, system_state, decision_timestamp)


if __name__ == "__main__":
    # Simple smoke test for local runs
    examples = [
        ("SovereignOwner", "AUTHORIZE_EMERGENCY_LOCKDOWN", "CRISIS"),
        ("SovereignOwner", "AUTHORIZE_EMERGENCY_LOCKDOWN", "NORMAL"),
        ("Guardian", "AUTHORIZE_EMERGENCY_LOCKDOWN", "CRISIS"),
        ("Guardian", "AUTHORIZE_EMERGENCY_LOCKDOWN", "NORMAL"),
        ("UnknownUser", "AUTHORIZE_EMERGENCY_LOCKDOWN", "CRISIS"),
    ]

    for identity, perm, state in examples:
        decision = evaluate_decision(identity, perm, state, _now_iso_utc())
        print("------------------------------------------------------------")
        print(f"Identity   : {decision['identity_label']}")
        print(f"Permission : {decision['requested_permission_name']}")
        print(f"State      : {decision['system_state']}")
        print(f"Decision   : {decision['decision']}")
        print(f"Policies   : {', '.join(decision['policy_ids'])}")
        print(f"Reason     : {decision['reason']}")
        if "principal_identity_labels" in decision:
            print(f"Principals : {decision['principal_identity_labels']}")
        if "delegation_ids" in decision:
            print(f"Delegations: {decision['delegation_ids']}")
        print("------------------------------------------------------------\n")
