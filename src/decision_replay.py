"""
Sovereignty Control System — Decision Replay & Explanation CLI (v1.1)

Read-only tools for reviewing and explaining past governance decisions using the
hash-chained audit log and (optionally) correlating them with enforcement
events.

Subcommands:
    list       - List decisions with basic fields and integrity status
    explain    - Show a full explanation for a specific decision by index
    correlate  - Correlate a decision with enforcement events (if any)

This module does NOT:
    - Re-evaluate decisions
    - Perform any enforcement
    - Modify logs or system state
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Helpers for log reading and integrity checking (audit log)
# ---------------------------------------------------------------------------


def _canonical_json(data: Dict[str, Any]) -> str:
    """
    Canonical JSON serialization used for hashing.

    This mirrors the v1.0 log integrity model:
    - sort_keys=True for deterministic key order
    - separators=(',', ':') for stable, whitespace-minimal form
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _load_log_entries(log_path: Path) -> List[Tuple[Dict[str, Any], str]]:
    """
    Load all JSONL entries from the given log file.

    Returns a list of (record, raw_line) tuples to preserve the original text.

    Any line that fails JSON parsing is treated as a hard error.
    """
    if not log_path.is_file():
        print(f"ERROR: log file not found: {log_path}", file=sys.stderr)
        raise SystemExit(2)

    entries: List[Tuple[Dict[str, Any], str]] = []

    with log_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            raw = line.rstrip("\n")
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                print(
                    f"ERROR: failed to parse JSON on line {line_number}: {exc}",
                    file=sys.stderr,
                )
                raise SystemExit(2)
            entries.append((record, raw))

    return entries


def _compute_entry_hash(record: Dict[str, Any]) -> str:
    """
    Compute the expected entry_hash for a record using the v1.0 model.

    The algorithm:
      - Take a copy of the record
      - Ensure 'prev_hash' is present in the payload (as stored)
      - Remove 'entry_hash' from the payload if present
      - Canonicalize and hash with SHA-256
    """
    payload = dict(record)
    # entry_hash is not included in the hashing payload
    payload.pop("entry_hash", None)

    canonical = _canonical_json(payload).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _verify_hash_chain(
    entries: List[Tuple[Dict[str, Any], str]]
) -> List[Dict[str, Any]]:
    """
    Verify the hash chain for all entries and annotate each with integrity info.

    Returns a list of dictionaries with:
        {
            "record": <original dict>,
            "raw": <original line>,
            "index": <0-based index>,
            "integrity_status": "LEGACY" | "OK" | "FAILED",
            "integrity_error": Optional[str],
        }

    Rules:
      - Entries without 'entry_hash' are treated as LEGACY (not hashed)
      - For hashed entries:
          - prev_hash must match prior entry's entry_hash (or None at boundary)
          - entry_hash must match the recomputed value
    """
    annotated: List[Dict[str, Any]] = []

    previous_hash: Optional[str] = None

    for idx, (record, raw) in enumerate(entries):
        entry_hash = record.get("entry_hash")
        prev_hash = record.get("prev_hash")

        status = "LEGACY"
        error: Optional[str] = None

        if entry_hash is None:
            # Legacy or pre-v1.0 entry; we do not attempt to hash-verify it.
            status = "LEGACY"
        else:
            # This is a v1.0+ hashed entry
            expected_hash = _compute_entry_hash(record)

            # Check linkage first: prev_hash must match previous entry_hash
            if prev_hash != previous_hash:
                status = "FAILED"
                error = (
                    "prev_hash mismatch: chain broken "
                    f"(expected prev_hash={previous_hash!r}, got {prev_hash!r})"
                )
            elif entry_hash != expected_hash:
                status = "FAILED"
                error = (
                    "entry_hash mismatch: content altered "
                    f"(expected={expected_hash}, got={entry_hash})"
                )
            else:
                status = "OK"

            previous_hash = entry_hash

        annotated.append(
            {
                "record": record,
                "raw": raw,
                "index": idx,
                "integrity_status": status,
                "integrity_error": error,
            }
        )

        # For LEGACY entries, we do not update previous_hash; the chain is
        # defined only over v1.0+ hashed entries.
        if entry_hash is None:
            # Explicitly keep previous_hash unchanged.
            pass

    return annotated


# ---------------------------------------------------------------------------
# Enforcement log loading and correlation helpers
# ---------------------------------------------------------------------------


def _load_enforcement_entries(
    log_path: Path,
) -> List[Tuple[Dict[str, Any], str]]:
    """
    Load enforcement entries from the enforcement log JSONL file.

    The expected shape of each record (as written by enforcement_logger) is:

        {
            "timestamp": "<ISO-8601 UTC>",
            "kind": "enforcement_event",
            "payload": {
                "decision_reference": {...},
                "context": {...},
                "dry_run": bool,
                "action_results": [...]
            },
            "meta": {...}
        }

    This function is tolerant of extra fields and focuses on those needed for
    correlation.
    """
    if not log_path.is_file():
        # For correlation, absence of an enforcement log is not a hard error.
        return []

    entries: List[Tuple[Dict[str, Any], str]] = []

    with log_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            raw = line.rstrip("\n")
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                print(
                    f"WARNING: failed to parse JSON in enforcement log on "
                    f"line {line_number}: {exc}",
                    file=sys.stderr,
                )
                continue
            entries.append((record, raw))

    return entries


def _get(record: Dict[str, Any], key: str, default: Any = "") -> Any:
    return record.get(key, default)


def _extract_identity(record: Dict[str, Any]) -> str:
    return _get(record, "identity_label", _get(record, "identity", ""))


def _extract_requested_action(record: Dict[str, Any]) -> str:
    return _get(
        record,
        "requested_permission_name",
        _get(record, "requested_action", ""),
    )


def _build_decision_correlation_key(
    decision_record: Dict[str, Any],
) -> Tuple[str, Any]:
    """
    Build a correlation key for an audit decision record.

    Primary:
        ("id", <decision_correlation_id>) if present

    Fallback (best-effort):
        ("fallback", (timestamp, identity, requested_action, policy_version_id))
    """
    corr_id = decision_record.get("decision_correlation_id")
    if corr_id:
        return ("id", corr_id)

    ts = _get(decision_record, "timestamp", "")
    identity = _extract_identity(decision_record)
    requested = _extract_requested_action(decision_record)
    pvid = decision_record.get("policy_version_id")

    return ("fallback", (ts, identity, requested, pvid))


def _build_enforcement_correlation_key(
    enforcement_record: Dict[str, Any],
) -> Tuple[str, Any]:
    """
    Build a correlation key for an enforcement log record.

    Primary:
        ("id", <decision_correlation_id>) if present in payload.decision_reference

    Fallback:
        ("fallback", (timestamp, identity, requested_action, policy_version_id))
    """
    payload = enforcement_record.get("payload") or {}
    decision_ref = payload.get("decision_reference") or {}

    corr_id = decision_ref.get("decision_correlation_id")
    if corr_id:
        return ("id", corr_id)

    ts = decision_ref.get("timestamp", "")
    identity = _extract_identity(decision_ref)
    requested = _extract_requested_action(decision_ref)
    pvid = decision_ref.get("policy_version_id")

    return ("fallback", (ts, identity, requested, pvid))


# ---------------------------------------------------------------------------
# Presentation helpers
# ---------------------------------------------------------------------------


def _format_list_row(entry: Dict[str, Any]) -> str:
    record = entry["record"]
    idx = entry["index"]
    ts = _get(record, "timestamp", "")
    identity = _extract_identity(record)
    requested = _extract_requested_action(record)
    decision = _get(record, "decision", _get(record, "decision_outcome", ""))
    pvid = _get(record, "policy_version_id", "")
    status = entry["integrity_status"]

    return (
        f"{idx:4d}  {status:7s}  {ts:26s}  "
        f"{identity:12s}  {requested:30s}  {decision:8s}  {pvid}"
    )


def _print_list(entries: List[Dict[str, Any]]) -> None:
    if not entries:
        print("No entries found.")
        return

    print(
        f"{'Idx':4s}  {'Status':7s}  {'Timestamp':26s}  "
        f"{'Identity':12s}  {'Requested Action':30s}  {'Decision':8s}  Policy Version"
    )
    print("-" * 130)
    for entry in entries:
        print(_format_list_row(entry))


def _entry_to_summary_dict(entry: Dict[str, Any]) -> Dict[str, Any]:
    record = entry["record"]
    return {
        "index": entry["index"],
        "integrity_status": entry["integrity_status"],
        "integrity_error": entry["integrity_error"],
        "timestamp": _get(record, "timestamp", ""),
        "identity": _extract_identity(record),
        "requested_action": _extract_requested_action(record),
        "decision": _get(record, "decision", _get(record, "decision_outcome", "")),
        "policy_version_id": _get(record, "policy_version_id", None),
        "policy_ids": _get(record, "policy_ids", []),
    }


def _print_explanation(entry: Dict[str, Any]) -> None:
    record = entry["record"]
    idx = entry["index"]
    status = entry["integrity_status"]
    error = entry["integrity_error"]

    print("=" * 72)
    print(f"Decision Index      : {idx}")
    print(f"Integrity Status    : {status}")
    if error:
        print(f"Integrity Detail    : {error}")
    print("-" * 72)

    # Key fields
    identity = _extract_identity(record)
    requested = _extract_requested_action(record)
    decision = _get(record, "decision", _get(record, "decision_outcome", ""))
    ts = _get(record, "timestamp", "")
    reason = _get(record, "reason", "")
    policy_ids = _get(record, "policy_ids", [])
    pvid = _get(record, "policy_version_id", None)

    print(f"Timestamp           : {ts}")
    print(f"Identity            : {identity}")
    print(f"Requested Action    : {requested}")
    print(f"Decision Outcome    : {decision}")
    print(f"Policy IDs          : {policy_ids}")
    print(f"Policy Version ID   : {pvid}")
    print(f"Reason              : {reason}")
    print("-" * 72)

    print("Full Record (JSON):")
    print(json.dumps(record, indent=2, default=str))
    print("=" * 72)


def _print_correlation_summary(
    decision_entry: Dict[str, Any],
    enforcement_matches: List[Dict[str, Any]],
) -> None:
    """
    Text-mode correlation summary: shows the decision, then any matching
    enforcement events.
    """
    record = decision_entry["record"]
    idx = decision_entry["index"]
    status = decision_entry["integrity_status"]
    error = decision_entry["integrity_error"]

    print("=" * 80)
    print(f"Decision Index      : {idx}")
    print(f"Integrity Status    : {status}")
    if error:
        print(f"Integrity Detail    : {error}")
    print("-" * 80)

    identity = _extract_identity(record)
    requested = _extract_requested_action(record)
    decision = _get(record, "decision", _get(record, "decision_outcome", ""))
    ts = _get(record, "timestamp", "")
    pvid = _get(record, "policy_version_id", None)
    reason = _get(record, "reason", "")

    print(f"Timestamp           : {ts}")
    print(f"Identity            : {identity}")
    print(f"Requested Action    : {requested}")
    print(f"Decision Outcome    : {decision}")
    print(f"Policy Version ID   : {pvid}")
    print(f"Reason              : {reason}")
    print("-" * 80)

    if not enforcement_matches:
        print("No correlated enforcement events were found.")
        print("=" * 80)
        return

    print(f"Correlated enforcement events: {len(enforcement_matches)}")
    print("-" * 80)

    for idx, em in enumerate(enforcement_matches, start=1):
        er = em["record"]
        ets = er.get("timestamp", "")
        payload = er.get("payload") or {}
        meta = er.get("meta") or {}
        decision_ref = payload.get("decision_reference") or {}
        dry_run = payload.get("dry_run", False)
        action_results = payload.get("action_results") or []

        print(f"Enforcement #{idx}")
        print(f"  Log Timestamp     : {ets}")
        print(f"  dry_run           : {dry_run}")
        if meta:
            print(f"  meta              : {meta}")
        print(f"  decision_reference: {json.dumps(decision_ref, indent=2, default=str)}")

        if not action_results:
            print("  action_results    : []")
        else:
            print("  action_results:")
            for ar_idx, ar in enumerate(action_results, start=1):
                outcome = ar.get("outcome")
                action = ar.get("action") or {}
                details = ar.get("details") or {}
                atype = action.get("action_type")
                target = action.get("target")

                print(f"    - Action #{ar_idx}")
                print(f"        outcome : {outcome}")
                print(f"        type    : {atype}")
                print(f"        target  : {target}")
                if details:
                    print(f"        details : {json.dumps(details, indent=8, default=str)}")

        print("-" * 80)

    print("=" * 80)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> None:
    log_path = Path(args.log_path)
    entries = _load_log_entries(log_path)
    annotated = _verify_hash_chain(entries)

    if args.json:
        # JSON mode: emit a JSON array of summarized entries
        summaries = [_entry_to_summary_dict(e) for e in annotated]
        json.dump(summaries, sys.stdout, indent=2, default=str)
        print()
    else:
        _print_list(annotated)


def cmd_explain(args: argparse.Namespace) -> None:
    log_path = Path(args.log_path)
    entries = _load_log_entries(log_path)
    annotated = _verify_hash_chain(entries)

    if not annotated:
        print("No entries in log.", file=sys.stderr)
        raise SystemExit(1)

    index = args.index
    if index < 0 or index >= len(annotated):
        print(
            f"ERROR: index {index} is out of range (0..{len(annotated) - 1})",
            file=sys.stderr,
        )
        raise SystemExit(2)

    entry = annotated[index]

    if args.json:
        # JSON mode: emit full record plus integrity metadata
        output = {
            "index": entry["index"],
            "integrity_status": entry["integrity_status"],
            "integrity_error": entry["integrity_error"],
            "record": entry["record"],
        }
        json.dump(output, sys.stdout, indent=2, default=str)
        print()
    else:
        _print_explanation(entry)


def cmd_correlate(args: argparse.Namespace) -> None:
    audit_log_path = Path(args.log_path)
    enforcement_log_path = Path(args.enforcement_log_path)

    # Load and verify audit log
    audit_entries = _load_log_entries(audit_log_path)
    annotated = _verify_hash_chain(audit_entries)

    if not annotated:
        print("No entries in audit log.", file=sys.stderr)
        raise SystemExit(1)

    index = args.index
    if index < 0 or index >= len(annotated):
        print(
            f"ERROR: index {index} is out of range (0..{len(annotated) - 1})",
            file=sys.stderr,
        )
        raise SystemExit(2)

    decision_entry = annotated[index]
    decision_record = decision_entry["record"]
    decision_key = _build_decision_correlation_key(decision_record)

    # Load enforcement log (if present)
    enforcement_entries = _load_enforcement_entries(enforcement_log_path)
    matches: List[Dict[str, Any]] = []

    for er, raw in enforcement_entries:
        key = _build_enforcement_correlation_key(er)
        if key == decision_key:
            matches.append({"record": er, "raw": raw})

    if args.json:
        # JSON mode: emit a structured correlation result
        output = {
            "decision": {
                "index": decision_entry["index"],
                "integrity_status": decision_entry["integrity_status"],
                "integrity_error": decision_entry["integrity_error"],
                "record": decision_entry["record"],
            },
            "enforcement_matches": [m["record"] for m in matches],
        }
        json.dump(output, sys.stdout, indent=2, default=str)
        print()
    else:
        _print_correlation_summary(decision_entry, matches)


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sovereignty Control System — Decision Replay & Explanation CLI (v1.1)"
    )

    parser.add_argument(
        "--log-path",
        default="data/audit_log.jsonl",
        help="Path to the audit log JSONL file (default: data/audit_log.jsonl)",
    )
    parser.add_argument(
        "--enforcement-log-path",
        default="data/enforcement_log.jsonl",
        help="Path to the enforcement log JSONL file (default: data/enforcement_log.jsonl)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    list_parser = subparsers.add_parser(
        "list",
        help="List decisions with basic fields and integrity status",
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output list as JSON instead of text table",
    )
    list_parser.set_defaults(func=cmd_list)

    # explain
    explain_parser = subparsers.add_parser(
        "explain",
        help="Explain a specific decision by index",
    )
    explain_parser.add_argument(
        "--index",
        type=int,
        required=True,
        help="0-based index of the decision to explain (as shown by 'list')",
    )
    explain_parser.add_argument(
        "--json",
        action="store_true",
        help="Output explanation as JSON instead of text",
    )
    explain_parser.set_defaults(func=cmd_explain)

    # correlate
    correlate_parser = subparsers.add_parser(
        "correlate",
        help="Correlate a decision with enforcement events (if any)",
    )
    correlate_parser.add_argument(
        "--index",
        type=int,
        required=True,
        help="0-based index of the decision to correlate (as shown by 'list')",
    )
    correlate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output correlation result as JSON instead of text",
    )
    correlate_parser.set_defaults(func=cmd_correlate)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        raise SystemExit(2)

    func(args)


if __name__ == "__main__":
    main()
