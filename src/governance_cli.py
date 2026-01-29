"""
Sovereignty Control System — Governance Execution CLI (v0.9 mainline)

This CLI:

- Loads a decision scenario from a JSON file
- Runs the authority engine
- Optionally records the decision to the audit log
- Prints a human-readable summary

Usage examples:

    # Dry run (no audit log write)
    python -m src.governance_cli --scenario examples/owner_lockdown.json --dry-run

    # Execute and record to default audit log (data/audit_log.jsonl)
    python -m src.governance_cli --scenario examples/owner_lockdown.json

    # Execute and record to a custom audit log
    python -m src.governance_cli --scenario examples/owner_lockdown.json \
        --audit-log data/custom_audit_log.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .authority_engine import evaluate_decision, evaluate_and_record, AUDIT_LOG_PATH_DEFAULT


def load_scenario(path: Path | str) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def print_decision(decision: Dict[str, Any]) -> None:
    """
    Print a human-readable summary of the decision.
    Compatible with the existing view_decisions_cli output style.
    """
    timestamp = decision.get("timestamp", "")
    identity = decision.get("identity", "")
    requested_action = decision.get("requested_action", "")
    system_state = decision.get("system_state", "")
    decision_outcome = decision.get("decision_outcome", "")
    policy_ids = decision.get("policy_ids", [])
    reason = decision.get("reason", "")

    print("========================================")
    print(f"Timestamp       : {timestamp}")
    print(f"Identity        : {identity}")
    print(f"Requested action: {requested_action}")
    print(f"System state    : {system_state}")
    print(f"Decision outcome: {decision_outcome}")
    print(f"Policy IDs      : {', '.join(policy_ids) if policy_ids else '-'}")
    print(f"Reason          : {reason}")
    print("========================================")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute governance decisions and optionally record them to the audit log.",
    )
    parser.add_argument(
        "--scenario",
        required=True,
        help="Path to a JSON file describing the decision scenario.",
    )
    parser.add_argument(
        "--audit-log",
        default=str(AUDIT_LOG_PATH_DEFAULT),
        help=f"Path to the audit log JSONL file (default: {AUDIT_LOG_PATH_DEFAULT}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate the decision without writing to the audit log.",
    )

    args = parser.parse_args(argv)

    scenario = load_scenario(args.scenario)

    if args.dry_run:
        decision_record = evaluate_decision(scenario)
        decision_dict = {
            "timestamp": decision_record.timestamp,
            "identity": decision_record.identity,
            "requested_action": decision_record.requested_action,
            "system_state": decision_record.system_state,
            "decision_outcome": decision_record.decision_outcome,
            "policy_ids": decision_record.policy_ids,
            "reason": decision_record.reason,
        }
    else:
        decision_record = evaluate_and_record(scenario, audit_log_path=args.audit_log)
        decision_dict = {
            "timestamp": decision_record.timestamp,
            "identity": decision_record.identity,
            "requested_action": decision_record.requested_action,
            "system_state": decision_record.system_state,
            "decision_outcome": decision_record.decision_outcome,
            "policy_ids": decision_record.policy_ids,
            "reason": decision_record.reason,
        }

    print_decision(decision_dict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
