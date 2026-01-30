"""
Audit logger for the Sovereignty Control System.

- Writes one JSON object per line to an append-only log file.
- Keeps the core decision fields stable for reviewers and auditors.
- Adds optional delegation-related fields so decisions involving delegated
  authority remain fully traceable.
- v1.0: adds simple SHA-256 hash-chaining fields ('prev_hash', 'entry_hash')
  to support post-hoc integrity verification of the audit log.

This module is intentionally minimal and deterministic.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Log integrity helpers (v1.0)
# ---------------------------------------------------------------------------

DEFAULT_AUDIT_LOG_PATH = Path("data/audit_log.jsonl")


def _canonical_json(data: Dict[str, Any]) -> str:
    """
    Serialize JSON in a stable, deterministic way for hashing.

    - sort_keys=True ensures consistent key order
    - separators=(',', ':') removes insignificant whitespace

    This must remain stable across platforms and runs.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _load_last_entry_hash(log_path: Path) -> Optional[str]:
    """
    Read the last line of the audit log, if any, and return its 'entry_hash'
    field.

    If the file does not exist, is empty, or the last line has no 'entry_hash',
    returns None. This allows v1.0 hash-chaining to begin on top of existing
    legacy logs without breaking.
    """
    if not log_path.exists():
        return None

    try:
        with log_path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return None

            # Walk backwards to find the last non-empty line
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

            last_record = json.loads(line)
            return last_record.get("entry_hash")
    except Exception:
        # On any error, fail open: start a new chain from this point.
        # This avoids blocking audits due to partial corruption, while
        # still allowing a reviewer to detect anomalies later.
        return None


def _attach_hash_chain(record: Dict[str, Any], *, log_path: Path) -> Dict[str, Any]:
    """
    Return a new record with 'prev_hash' and 'entry_hash' added.

    - prev_hash: the entry_hash of the last log entry, or None if none
    - entry_hash: SHA-256 over canonicalized({**record, "prev_hash": prev_hash})

    The original record is not mutated; a shallow copy is returned.
    """
    prev_hash = _load_last_entry_hash(log_path)

    payload_for_hash = dict(record)
    payload_for_hash["prev_hash"] = prev_hash

    canonical = _canonical_json(payload_for_hash).encode("utf-8")
    entry_hash = hashlib.sha256(canonical).hexdigest()

    record_with_hash = dict(record)
    record_with_hash["prev_hash"] = prev_hash
    record_with_hash["entry_hash"] = entry_hash
    return record_with_hash


# ---------------------------------------------------------------------------
# Audit event model
# ---------------------------------------------------------------------------


@dataclass
class AuditEvent:
    """
    Represents a single governance decision as recorded in the audit log.

    Fields are intentionally stable and reviewer-oriented. Additional fields
    should be added conservatively and only when they are clearly useful for
    downstream review or accountability.
    """

    # Core decision context
    identity_label: str
    requested_permission_name: str
    system_state: str
    decision: str  # e.g. ALLOW, DENY, REQUIRE_ADDITIONAL_APPROVAL

    # Policy basis
    policy_ids: Sequence[str] = field(default_factory=list)

    # Explanation
    reason: str = ""

    # Timestamp in ISO 8601 with timezone (UTC), e.g. 2026-01-30T17:00:23.356613+00:00
    timestamp: str = ""

    # Correlation identifiers
    decision_correlation_id: Optional[str] = None

    # Delegation metadata (optional)
    delegate_identity_label: Optional[str] = None
    principal_identity_labels: Sequence[str] = field(default_factory=list)
    delegation_ids: Sequence[str] = field(default_factory=list)

    @classmethod
    def now(
        cls,
        *,
        identity_label: str,
        requested_permission_name: str,
        system_state: str,
        decision: str,
        policy_ids: Optional[Sequence[str]] = None,
        reason: str = "",
        decision_correlation_id: Optional[str] = None,
        delegate_identity_label: Optional[str] = None,
        principal_identity_labels: Optional[Sequence[str]] = None,
        delegation_ids: Optional[Sequence[str]] = None,
    ) -> "AuditEvent":
        """
        Convenience constructor that stamps the current UTC time.

        The authority engine may still construct AuditEvent directly if it wants
        full control over timestamps.
        """
        if policy_ids is None:
            policy_ids = []
        if principal_identity_labels is None:
            principal_identity_labels = []
        if delegation_ids is None:
            delegation_ids = []

        ts = datetime.now(timezone.utc).isoformat()

        return cls(
            identity_label=identity_label,
            requested_permission_name=requested_permission_name,
            system_state=system_state,
            decision=decision,
            policy_ids=list(policy_ids),
            reason=reason,
            timestamp=ts,
            decision_correlation_id=decision_correlation_id,
            delegate_identity_label=delegate_identity_label,
            principal_identity_labels=list(principal_identity_labels),
            delegation_ids=list(delegation_ids),
        )

    @classmethod
    def from_decision(
        cls,
        decision: Any,
        *,
        decision_correlation_id: Optional[str] = None,
    ) -> "AuditEvent":
        """
        Construct an AuditEvent from a decision produced by the authority engine.

        Supports both:
        - dict-like decisions (e.g. decision["identity_label"])
        - object-like decisions (e.g. decision.identity_label)

        Expected logical fields:
        - identity_label or identity
        - requested_permission_name or requested_action
        - system_state
        - decision or decision_outcome
        - policy_ids (optional)
        - reason (optional)
        - timestamp (optional)
        - delegate_identity_label (optional)
        - principal_identity_labels (optional)
        - delegation_ids (optional)
        """

        def get(key: str, default: Any = None) -> Any:
            if isinstance(decision, dict):
                return decision.get(key, default)
            return getattr(decision, key, default)

        identity_label = get("identity_label") or get("identity", "")
        requested_permission_name = (
            get("requested_permission_name") or get("requested_action", "")
        )
        system_state = get("system_state", "")
        decision_value = get("decision") or get("decision_outcome", "")
        policy_ids = get("policy_ids", []) or []
        reason = get("reason", "")
        timestamp = get("timestamp", "")

        delegate_identity_label = get("delegate_identity_label")
        principal_identity_labels = get("principal_identity_labels", []) or []
        delegation_ids = get("delegation_ids", []) or []

        return cls(
            identity_label=identity_label,
            requested_permission_name=requested_permission_name,
            system_state=system_state,
            decision=decision_value,
            policy_ids=policy_ids,
            reason=reason,
            timestamp=timestamp,
            decision_correlation_id=decision_correlation_id,
            delegate_identity_label=delegate_identity_label,
            principal_identity_labels=principal_identity_labels,
            delegation_ids=delegation_ids,
        )

    def to_record(self) -> Dict[str, Any]:
        """
        Convert this AuditEvent into a plain dict suitable for JSON serialization.

        This does not include integrity fields; those are attached at write time.
        """
        return {
            "identity_label": self.identity_label,
            "requested_permission_name": self.requested_permission_name,
            "system_state": self.system_state,
            "decision": self.decision,
            "policy_ids": list(self.policy_ids),
            "reason": self.reason,
            "timestamp": self.timestamp,
            "decision_correlation_id": self.decision_correlation_id,
            "delegate_identity_label": self.delegate_identity_label,
            "principal_identity_labels": list(self.principal_identity_labels),
            "delegation_ids": list(self.delegation_ids),
        }


# ---------------------------------------------------------------------------
# Audit logger
# ---------------------------------------------------------------------------


class AuditLogger:
    """
    Append-only JSONL logger for governance decisions.

    v1.0 adds hash-chaining on write via 'prev_hash' and 'entry_hash' fields.
    """

    def __init__(self, log_path: Path = DEFAULT_AUDIT_LOG_PATH) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: AuditEvent) -> None:
        """
        Append a single AuditEvent to the audit log as one JSON line.

        The event is first converted to a plain record, then extended with
        'prev_hash' and 'entry_hash' before being written.
        """
        record = event.to_record()
        record_with_hash = _attach_hash_chain(record, log_path=self.log_path)

        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record_with_hash, ensure_ascii=False))
            f.write("\n")


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def log_decision(
    decision: Any,
    *,
    audit_log_path: Path = DEFAULT_AUDIT_LOG_PATH,
    decision_correlation_id: Optional[str] = None,
) -> None:
    """
    Convenience helper to log a decision produced by the authority engine.

    This preserves existing behavior while adding v1.0 integrity fields.

    - Builds an AuditEvent from the decision (dict or object)
    - Uses AuditLogger to append it with hash-chaining
    """
    logger = AuditLogger(audit_log_path)
    event = AuditEvent.from_decision(
        decision,
        decision_correlation_id=decision_correlation_id,
    )
    logger.append(event)
