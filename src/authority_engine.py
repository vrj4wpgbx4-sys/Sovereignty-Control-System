"""
Sovereignty Control System — Authority Engine (simplified v0.9 mainline)

This module provides:

- evaluate_decision(scenario: dict) -> dict
    Pure, deterministic decision logic.

- evaluate_and_record(scenario: dict, audit_log_path: str) -> dict
    Runs the decision logic and appends a JSONL record to the audit log.

The audit log format is compatible with the existing view_decisions_cli, i.e.
each line is a JSON object with keys:

    timestamp, identity, requested_action, system_state,
    decision_outcome, policy_ids, reason, scenario

This keeps the engine self-contained and avoids fragile cross-module imports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


AUDIT_LOG_PATH_DEFAULT = Path("data") / "audit_log.jsonl"


@dataclass
class DecisionRecord:
    timestamp: str
    identity: str
    requested_action: str
    system_state: str
    decision_outcome: str
    policy_ids: List[str]
    reason: str
    scenario: Dict[str, Any]

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def evaluate_decision(scenario: Dict[str, Any]) -> DecisionRecord:
    """
    Deterministic decision logic for emergency lockdown scenarios.

    This is intentionally conservative and explicit. It covers the core
    demo path you have been using:

      - Ronald (sovereign owner) may authorize emergency lockdown in CRISIS.
      - Guardian may authorize emergency lockdown in CRISIS only when at
        least two approvals are present.
      - Everything else is DENY by default.

    If the scenario does not match these patterns, the engine will
    fail-closed with a DENY outcome and a clear reason.
    """
    identity = str(scenario.get("identity", "") or "")
    requested_action = str(scenario.get("requested_action", "") or "")
    system_state = str(scenario.get("system_state", "") or "")

    decision_outcome = "DENY"
    policy_ids: List[str] = []
    reason = "Default deny: no matching policy"

    # Emergency lockdown path
    if requested_action == "AUTHORIZE_EMERGENCY_LOCKDOWN" and system_state == "CRISIS":
        if identity == "Ronald":
            decision_outcome = "ALLOW"
            policy_ids = ["policy-001"]
            reason = "Sovereign owner attempts emergency lockdown in crisis state"
        elif identity == "Guardian":
            approvals = int(scenario.get("approvals", 0) or 0)
            policy_ids = ["policy-002"]
            if approvals >= 2:
                decision_outcome = "ALLOW"
                reason = (
                    "Family guardian attempts emergency lockdown; "
                    "policy requires two approvals"
                )
            else:
                decision_outcome = "REQUIRE_ADDITIONAL_APPROVAL"
                reason = (
                    "Family guardian attempts emergency lockdown; "
                    "policy requires two approvals"
                )

    return DecisionRecord(
        timestamp=_now_utc_iso(),
        identity=identity,
        requested_action=requested_action,
        system_state=system_state,
        decision_outcome=decision_outcome,
        policy_ids=policy_ids,
        reason=reason,
        scenario=scenario,
    )


def _ensure_data_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def record_decision(decision: DecisionRecord, audit_log_path: Path | str) -> None:
    """
    Append a single decision record to the JSONL audit log.
    """
    path = Path(audit_log_path)
    _ensure_data_dir(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(decision.to_json_line())
        f.write("\n")


def evaluate_and_record(
    scenario: Dict[str, Any],
    audit_log_path: Path | str = AUDIT_LOG_PATH_DEFAULT,
) -> DecisionRecord:
    """
    Run evaluate_decision and append the result to the audit log.

    Returns the DecisionRecord for immediate display.
    """
    decision = evaluate_decision(scenario)
    record_decision(decision, audit_log_path=audit_log_path)
    return decision
