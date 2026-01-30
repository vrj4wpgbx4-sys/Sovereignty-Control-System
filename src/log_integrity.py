"""
Log integrity helpers for v1.0.

Provides:
- Writer-side hash chaining helpers
- Reader-side verification of hash-chained JSONL logs
- A minimal, read-only CLI for verification
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Canonical JSON
# ---------------------------------------------------------------------------


def _canonical_json(data: Dict[str, Any]) -> str:
    """
    Serialize JSON in a stable, deterministic way for hashing.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Writer-side helpers
# ---------------------------------------------------------------------------


def load_last_entry_hash(log_path: Path) -> Optional[str]:
    """
    Return the entry_hash of the last log entry, or None.
    """
    if not log_path.exists():
        return None

    try:
        with log_path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return None

            buf = bytearray()
            i = size - 1
            while i >= 0:
                f.seek(i)
                ch = f.read(1)
                if ch == b"\n" and buf:
                    break
                buf.extend(ch)
                i -= 1

            line = bytes(reversed(buf)).decode("utf-8").strip()
            if not line:
                return None

            record = json.loads(line)
            return record.get("entry_hash")

    except Exception:
        return None


def attach_hash_chain(
    record: Dict[str, Any],
    *,
    log_path: Path,
) -> Dict[str, Any]:
    """
    Attach prev_hash and entry_hash to a record.
    """
    prev_hash = load_last_entry_hash(log_path)

    payload = dict(record)
    payload["prev_hash"] = prev_hash

    canonical = _canonical_json(payload).encode("utf-8")
    entry_hash = hashlib.sha256(canonical).hexdigest()

    out = dict(record)
    out["prev_hash"] = prev_hash
    out["entry_hash"] = entry_hash
    return out


# ---------------------------------------------------------------------------
# Reader-side verification
# ---------------------------------------------------------------------------


def verify_log_chain(log_path: Path) -> Dict[str, Any]:
    """
    Verify hash-chain integrity of a JSONL log.

    Returns a dict:
    {
        "ok": bool,
        "total_entries": int,
        "hashed_entries": int,
        "errors": [
            {"line_number": int, "message": str}
        ]
    }
    """
    result: Dict[str, Any] = {
        "ok": True,
        "total_entries": 0,
        "hashed_entries": 0,
        "errors": [],
    }

    if not log_path.exists():
        return result

    previous_entry_hash: Optional[str] = None

    try:
        with log_path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue

                result["total_entries"] += 1

                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    result["ok"] = False
                    result["errors"].append(
                        {
                            "line_number": line_number,
                            "message": f"Invalid JSON: {exc}",
                        }
                    )
                    continue

                if "entry_hash" not in record:
                    continue

                result["hashed_entries"] += 1

                stored_prev = record.get("prev_hash")
                stored_hash = record.get("entry_hash")

                # Check chain continuity
                if stored_prev != previous_entry_hash:
                    result["ok"] = False
                    result["errors"].append(
                        {
                            "line_number": line_number,
                            "message": (
                                f"prev_hash mismatch "
                                f"(expected {previous_entry_hash!r}, "
                                f"found {stored_prev!r})"
                            ),
                        }
                    )

                # Recompute expected hash
                payload = {
                    k: v
                    for k, v in record.items()
                    if k not in ("prev_hash", "entry_hash")
                }
                payload["prev_hash"] = stored_prev

                canonical = _canonical_json(payload).encode("utf-8")
                expected_hash = hashlib.sha256(canonical).hexdigest()

                if stored_hash != expected_hash:
                    result["ok"] = False
                    result["errors"].append(
                        {
                            "line_number": line_number,
                            "message": "entry_hash mismatch (content altered)",
                        }
                    )

                previous_entry_hash = stored_hash

    except OSError as exc:
        result["ok"] = False
        result["errors"].append(
            {
                "line_number": 0,
                "message": f"I/O error: {exc}",
            }
        )

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify hash-chain integrity of audit logs."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify a JSONL audit log for hash-chain integrity.",
    )
    verify_parser.add_argument(
        "--log-path",
        type=Path,
        default=Path("data/audit_log.jsonl"),
        help="Path to audit log (default: data/audit_log.jsonl)",
    )

    args = parser.parse_args(argv)

    if args.command == "verify":
        result = verify_log_chain(args.log_path)

        print(f"Log file: {args.log_path}")
        print(f"Total entries: {result['total_entries']}")
        print(f"Hashed entries: {result['hashed_entries']}")

        if result["ok"] and not result["errors"]:
            print("Integrity check: OK")
            return 0

        print("Integrity check: FAILED")
        for err in result["errors"]:
            print(f"- Line {err['line_number']}: {err['message']}")
        return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
