"""
Sovereignty Control System — Governance CLI (v0.9-ready, v1.0-log-integrity-ready)

Primary execution surface for governance decisions.

Modes:
1) Decision-only (v0.8 default behavior)
2) Decision + Enforcement (v0.9, opt-in via --enforce)

Key guarantees:
- No enforcement without a decision
- Enforcement is explicit
- Enforcement does not override authority
- Decision, enforcement, and logging remain separated

v1.0 extension:
- Decisions are recorded via AuditLogger, which now attaches hash-chain
  integrity fields ('prev_hash', 'entry_hash') to the audit log entries.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, List

from .authority_engine import evaluate_decision
from .audit_logger import log_decision, DEFAULT_AUDIT_LOG_PATH
from .enforcement.dispatcher import (
    EnforcementAction,
    EnforcementContext,
    EnforcementDispatcher,
    EnforcementRequest,
    summarize_enforcement_result,
)
from .enforcement.lockdown_state_effector import LockdownStateEffector
from .enforcement.enforcement_logger import append_enforcement_result


# ---------------------------------------------------------------------------
# Decision helpers
# ---------------------------------------------------------------------------


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Safely extract an attribute or key from a decision-like object."""
    if obj is None:
        return default
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _format_policy_ids(policy_ids: Any) -> str:
    if not policy_ids:
        return ""
    if isinstance(policy_ids, (list, tuple, set)):
        return ", ".join(str(p) for p in policy_ids)
    return str(policy_ids)


def print_decision_summary(decision: Any) -> None:
    """Human-readable decision summary, stable for reviewers."""
    print("=" * 50)
    print(f"Timestamp       : {_get(decision, 'timestamp', '')}")
    print(f"Identity        : {_get(decision, 'identity', _get(decision, 'identity_label', ''))}")
    print(f"Requested action: {_get(decision, 'requested_action', _get(decision, 'requested_permission_name', ''))}")
    print(f"System state    : {_get(decision, 'system_state', '')}")
    print(f"Decision outcome: {_get(decision, 'decision_outcome', _get(decision, 'decision', ''))}")
    print(f"Policy IDs      : {_format_policy_ids(_get(decision, 'policy_ids', []))}")
    print(f"Reason          : {_get(decision, 'reason', '')}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Enforcement wiring
# ---------------------------------------------------------------------------


def build_enforcement_request_from_decision(
    decision: Any,
    *,
    dry_run: bool,
) -> Optional[EnforcementRequest]:
    """
    Build an EnforcementRequest from a successful decision.

    v0.9 rule: we only enforce when:
      - decision outcome == ALLOW
      - requested action == AUTHORIZE_EMERGENCY_LOCKDOWN
    """
    outcome = str(
        _get(decision, "decision_outcome", _get(decision, "decision", ""))
    ).upper()
    requested_action = str(
        _get(decision, "requested_action", _get(decision, "requested_permission_name", ""))
    ).upper()

    if outcome != "ALLOW":
        return None

    if requested_action != "AUTHORIZE_EMERGENCY_LOCKDOWN":
        return None

    identity = _get(decision, "identity", _get(decision, "identity_label", ""))
    reason = _get(decision, "reason", "Lockdown authorized by governance decision")
    timestamp = _get(decision, "timestamp", "")
    policy_ids = _get(decision, "policy_ids", [])

    decision_reference: Dict[str, Any] = {
        "timestamp": timestamp,
        "requested_action": requested_action,
        "identity": identity,
        "policy_ids": policy_ids,
        "decision_outcome": outcome,
    }

    context = EnforcementContext(
        data={
            "decision_outcome": outcome,
            "identity": identity,
            "requested_action": requested_action,
            "policy_ids": policy_ids,
            "timestamp": timestamp,
            "reason": reason,
        }
    )

    actions: List[EnforcementAction] = [
        EnforcementAction(
            action_type="lockdown_state",
            target="system",
            parameters={
                "operation": "SET",
                "reason": reason,
                "requested_by": identity or "unknown",
            },
        )
    ]

    return EnforcementRequest(
        decision_reference=decision_reference,
        context=context,
        actions=actions,
        dry_run=dry_run,
    )


def execute_enforcement(
    decision: Any,
    *,
    dry_run: bool,
    additional_metadata: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Execute enforcement downstream of a decision, if applicable.

    - Builds an EnforcementRequest from the decision
    - Dispatches via EnforcementDispatcher
    - Logs the result to enforcement_log.jsonl
    - Returns a summarized dict for CLI rendering
    """
    request = build_enforcement_request_from_decision(decision, dry_run=dry_run)
    if request is None:
        return None

    dispatcher = EnforcementDispatcher(effectors=[LockdownStateEffector()])
    result = dispatcher.dispatch(request)

    append_enforcement_result(result, additional_metadata=additional_metadata)
    return summarize_enforcement_result(result)


def print_enforcement_summary(summary: Optional[Dict[str, Any]]) -> None:
    """Human-readable enforcement summary for the CLI."""
    if not summary:
        print("No enforcement was performed.")
        return

    print("\nEnforcement Summary")
    print("-" * 20)
    print(f"Dry run : {summary.get('dry_run', False)}")

    decision_ref = summary.get("decision_reference", {}) or {}
    print(f"Outcome : {decision_ref.get('decision_outcome', 'UNKNOWN')}")

    for idx, action in enumerate(summary.get("actions", []), start=1):
        print(f"\nAction #{idx}")
        print(f"  Type    : {action.get('action_type')}")
        print(f"  Target  : {action.get('target')}")
        print(f"  Outcome : {action.get('outcome')}")
        for k, v in (action.get("details") or {}).items():
            print(f"    - {k}: {v}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sovereignty Control System — Governance CLI"
    )

    parser.add_argument(
        "--scenario",
        required=True,
        help="Path to a JSON file describing the decision scenario.",
    )
    parser.add_argument(
        "--audit-log",
        default=str(DEFAULT_AUDIT_LOG_PATH),
        help="Audit log JSONL path (default: data/audit_log.jsonl).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate without performing real enforcement side effects or audit writes.",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Opt-in: attempt enforcement after an ALLOW decision.",
    )

    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)

    scenario_path = Path(args.scenario)
    if not scenario_path.is_file():
        raise SystemExit(f"Scenario file not found: {scenario_path}")

    with scenario_path.open("r", encoding="utf-8") as f:
        scenario_data = json.load(f)

    # v0.8-pure decision evaluation: authority engine sees only scenario data.
    decision = evaluate_decision(scenario_data)

    # Human-readable decision summary to stdout
    print_decision_summary(decision)

    # v1.0: write to audit log in non-dry-run mode, with hash-chaining
    if not args.dry_run:
        log_decision(decision, audit_log_path=Path(args.audit_log))

    # v0.9 enforcement path: explicit, downstream, and optional.
    if args.enforce:
        metadata = {
            "invoked_by": "governance_cli",
            "scenario_path": str(scenario_path),
        }
        summary = execute_enforcement(
            decision,
            dry_run=args.dry_run,
            additional_metadata=metadata,
        )
        print_enforcement_summary(summary)


if __name__ == "__main__":
    main()
