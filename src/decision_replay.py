"""
Sovereignty Control System — Decision Replay & Explanation CLI (v1.1)

Read-only tools for reviewing and explaining past governance decisions using the
hash-chained audit log.

Subcommands:
    list      - List decisions with basic fields and integrity status
    explain   - Show a full explanation for a specific decision by index

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
# Helpers for log reading and integrity checking
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

    Returns a list of (record, raw_line) tuples to preserve the original text
    for potential future use.

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
# Presentation helpers
# ---------------------------------------------------------------------------


def _get(record: Dict[str, Any], key: str, default: Any = "") -> Any:
    return record.get(key, default)


def _format_list_row(entry: Dict[str, Any]) -> str:
    record = entry["record"]
    idx = entry["index"]
    ts = _get(record, "timestamp", "")
    identity = _get(record, "identity_label", _get(record, "identity", ""))
    requested = _get(
        record,
        "requested_permission_name",
        _get(record, "requested_action", ""),
    )
    decision = _get(record, "decision", _get(record, "decision_outcome", ""))
    pvid = _get(record, "policy_version_id", "")
    status = entry["integrity_status"]

    return (
        f"{idx:4d}  {status:7s}  {ts:26s}  "
        f"{identity:10s}  {requested:30s}  {decision:8s}  {pvid}"
    )


def _print_list(entries: List[Dict[str, Any]]) -> None:
    if not entries:
        print("No entries found.")
        return

    print(
        f"{'Idx':4s}  {'Status':7s}  {'Timestamp':26s}  "
        f"{'Identity':10s}  {'Requested Action':30s}  {'Decision':8s}  Policy Version"
    )
    print("-" * 120)
    for entry in entries:
        print(_format_list_row(entry))


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
    identity = _get(record, "identity_label", _get(record, "identity", ""))
    requested = _get(
        record,
        "requested_permission_name",
        _get(record, "requested_action", ""),
    )
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


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> None:
    log_path = Path(args.log_path)
    entries = _load_log_entries(log_path)
    annotated = _verify_hash_chain(entries)
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
    _print_explanation(entry)


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

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    list_parser = subparsers.add_parser(
        "list",
        help="List decisions with basic fields and integrity status",
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
    explain_parser.set_defaults(func=cmd_explain)

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
