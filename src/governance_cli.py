"""
Governance Scenario CLI (v0.8)
Sovereignty Control System

This CLI:
- Calls the authority engine to evaluate a governance decision.
- Prints the decision in a human-readable form.
- Writes the decision to the audit log using the centralized audit logger,
  including delegation-related fields when present.

It does NOT:
- Change the authority engine's logic.
- Bypass existing CLIs.
- Modify or read the audit log directly.
"""

from __future__ import annotations

from typing import Tuple

from authority_engine import evaluate_decision
from audit_logger import log_decision_dict


def _print_decision(decision: dict) -> None:
    """Pretty-print a decision record."""
    print("============================================================")
    print(f"Identity         : {decision.get('identity_label', '-')}")
    print(f"Requested action : {decision.get('requested_permission_name', '-')}")
    print(f"System state     : {decision.get('system_state', '-')}")
    print(f"Decision outcome : {decision.get('decision', '-')}")
    print(f"Policy IDs       : {', '.join(decision.get('policy_ids', []))}")
    print(f"Reason           : {decision.get('reason', '-')}")
    print(f"Timestamp        : {decision.get('timestamp', '-')}")
    # Delegation-related context (v0.8)
    delegate = decision.get("delegate_identity_label")
    principals = decision.get("principal_identity_labels")
    delegation_ids = decision.get("delegation_ids")

    if delegate or principals or delegation_ids:
        print("\nDelegation context:")
        if delegate:
            print(f"  Delegate identity   : {delegate}")
        if principals:
            print(f"  Principal identities: {principals}")
        if delegation_ids:
            print(f"  Delegation IDs      : {delegation_ids}")
    else:
        print("\nDelegation context: none (no applicable delegation)")

    print("============================================================")
    print()


def _scenario_menu() -> Tuple[str, str, str]:
    """
    Present a simple menu of fixed scenarios.

    This keeps behavior deterministic and easy for reviewers
    and testers to follow.
    """
    print("== Sovereignty Control System – Governance Scenarios (v0.8) ==")
    print("Select a scenario:")
    print("  1) Sovereign owner – emergency lockdown in CRISIS state")
    print("  2) Sovereign owner – emergency lockdown in NORMAL state")
    print("  3) Guardian – emergency lockdown in CRISIS state")
    print("  4) Guardian – emergency lockdown in NORMAL state")
    print("  0) Exit")
    choice = input("Enter choice: ").strip()

    if choice == "1":
        return "SovereignOwner", "AUTHORIZE_EMERGENCY_LOCKDOWN", "CRISIS"
    elif choice == "2":
        return "SovereignOwner", "AUTHORIZE_EMERGENCY_LOCKDOWN", "NORMAL"
    elif choice == "3":
        return "Guardian", "AUTHORIZE_EMERGENCY_LOCKDOWN", "CRISIS"
    elif choice == "4":
        return "Guardian", "AUTHORIZE_EMERGENCY_LOCKDOWN", "NORMAL"
    elif choice == "0":
        raise SystemExit(0)
    else:
        print("Invalid choice, please try again.\n")
        return _scenario_menu()


def main() -> None:
    """
    Main entry point for the governance CLI.

    For each chosen scenario:
    - Evaluate the decision via the authority engine (delegation-aware).
    - Print the result to the console.
    - Append the decision to the audit log using the centralized audit logger.
    """
    while True:
        identity_label, permission_name, system_state = _scenario_menu()

        # Evaluate the decision using the authority engine (v0.8, delegation-aware).
        decision = evaluate_decision(
            identity_label=identity_label,
            requested_permission_name=permission_name,
            system_state=system_state,
        )

        # Print the decision for the operator / reviewer.
        _print_decision(decision)

        # Persist the decision to the audit log (JSONL), including delegation fields if present.
        log_decision_dict(decision)

        print("Decision has been recorded in data/audit_log.jsonl.\n")


if __name__ == "__main__":
    main()
