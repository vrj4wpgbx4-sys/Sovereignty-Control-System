"""
Decision Enforcement Gate
Sovereignty Control System v0.5

This module enforces governance decisions at runtime.
It must not be bypassed.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import uuid


class DecisionOutcome(Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_ADDITIONAL_APPROVAL = "REQUIRE_ADDITIONAL_APPROVAL"


class EnforcementResult(Enum):
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    PAUSED = "PAUSED"


@dataclass(frozen=True)
class GovernanceDecision:
    decision_correlation_id: str
    timestamp: str
    identity_label: str
    requested_action: str
    system_state: str
    decision_outcome: DecisionOutcome
    policy_ids: list[str]
    decision_reason: str


@dataclass(frozen=True)
class EnforcementRecord:
    decision_correlation_id: str
    timestamp: str
    action_identifier: str
    enforcement_result: EnforcementResult
    enforcement_reason: str
    policy_ids: list[str]


def generate_decision_correlation_id() -> str:
    return str(uuid.uuid4())


def enforce_action(
    *,
    decision: GovernanceDecision,
    action_identifier: str,
    execute_action_callable,
) -> EnforcementRecord:
    """
    Enforce a governed action based on a governance decision.

    - No decision -> no execution
    - ALLOW -> execute
    - DENY -> block
    - REQUIRE_ADDITIONAL_APPROVAL -> pause
    """

    if not decision or not decision.decision_correlation_id:
        raise RuntimeError("Governance decision with valid correlation ID is required.")

    now = datetime.utcnow().isoformat() + "Z"

    if decision.decision_outcome == DecisionOutcome.ALLOW:
        execute_action_callable()
        return EnforcementRecord(
            decision_correlation_id=decision.decision_correlation_id,
            timestamp=now,
            action_identifier=action_identifier,
            enforcement_result=EnforcementResult.EXECUTED,
            enforcement_reason="Action executed under explicit governance authorization.",
            policy_ids=decision.policy_ids,
        )

    if decision.decision_outcome == DecisionOutcome.DENY:
        return EnforcementRecord(
            decision_correlation_id=decision.decision_correlation_id,
            timestamp=now,
            action_identifier=action_identifier,
            enforcement_result=EnforcementResult.BLOCKED,
            enforcement_reason="Action blocked by governance decision.",
            policy_ids=decision.policy_ids,
        )

    if decision.decision_outcome == DecisionOutcome.REQUIRE_ADDITIONAL_APPROVAL:
        return EnforcementRecord(
            decision_correlation_id=decision.decision_correlation_id,
            timestamp=now,
            action_identifier=action_identifier,
            enforcement_result=EnforcementResult.PAUSED,
            enforcement_reason="Action paused pending additional policy-defined approval.",
            policy_ids=decision.policy_ids,
        )

    raise RuntimeError("Invalid governance decision outcome.")
