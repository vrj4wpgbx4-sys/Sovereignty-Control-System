"""
Audit logger for the Sovereignty Control System.

- Writes one JSON object per line to an append-only log file.
- Keeps the core decision fields stable for reviewers and auditors.
- Adds optional delegation-related fields so decisions involving delegated
  authority remain fully traceable.

This module is intentionally minimal and deterministic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class AuditEvent:
    """
    Canonical audit event schema for governance decisions.

    Required core fields (stable for v0.x):

    - identity_label: human-readable identity initiating the request
    - requested_permission_name: governance action / permission name
    - system_state: system state at decision time (e.g., "NORMAL", "CRISIS")
    - decision: decision outcome ("ALLOW", "DENY", "REQUIRE_ADDITIONAL_APPROVAL")
    - policy_ids: list of policy identifiers responsible for the outcome
    - reason: human-readable reason / narrative explanation
    - timestamp: ISO 8601 timestamp when the decision was recorded (UTC)

    Optional correlation / delegation fields (added in later versions):

    - decision_correlation_id: unique ID linking this decision to enforcement
    - delegate_identity_label: identity actually acting under delegated authority
    - principal_identity_labels: identities on whose behalf the delegate acts
    - delegation_ids: IDs of delegation records used to justify authority
    """

    identity_label: str
    requested_permission_name: str
    system_state: str
    decision: str
    policy_ids: Sequence[str]
    reason: str
    timestamp: str

    # Correlation and delegation metadata (optional)
    decision_correlation_id: Optional[str] = None
    delegate_identity_label: Optional[str] = None
    principal_identity_labels: Sequence[str] = field(default_factory=list)
    delegation_ids: Sequence[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a JSON-serializable dict.

        Optional fields are only included if they are present / non-empty,
        so existing logs and tools that expect the older schema remain valid.
        """
        data: Dict[str, Any] = {
            "identity_label": self.identity_label,
            "requested_permission_name": self.requested_permission_name,
            "system_state": self.system_state,
            "decision": self.decision,
            "policy_ids": list(self.policy_ids),
            "reason": self.reason,
            "timestamp": self.timestamp,
        }

        if self.decision_correlation_id:
            data["decision_correlation_id"] = self.decision_correlation_id

        if self.delegate_identity_label:
            data["delegate_identity_label"] = self.delegate_identity_label

        if self.principal_identity_labels:
            data["principal_identity_labels"] = list(self.principal_identity_labels)

        if self.delegation_ids:
            data["delegation_ids"] = list(self.delegation_ids)

        return data

    @classmethod
    def now(
        cls,
        *,
        identity_label: str,
        requested_permission_name: str,
        system_state: str,
        decision: str,
        policy_ids: Sequence[str],
        reason: str,
        decision_correlation_id: Optional[str] = None,
        delegate_identity_label: Optional[str] = None,
        principal_identity_labels: Optional[Sequence[str]] = None,
        delegation_ids: Optional[Sequence[str]] = None,
    ) -> "AuditEvent":
        """
        Convenience constructor that stamps the current UTC time.

        This is optional; the authority engine can still construct AuditEvent
        directly if it prefers to control timestamps itself.
        """
        return cls(
            identity_label=identity_label,
            requested_permission_name=requested_permission_name,
            system_state=system_state,
            decision=decision,
            policy_ids=list(policy_ids),
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_correlation_id=decision_correlation_id,
            delegate_identity_label=delegate_identity_label,
            principal_identity_labels=list(principal_identity_labels or []),
            delegation_ids=list(delegation_ids or []),
        )


class AuditLogger:
    """
    Append-only JSONL audit logger.

    Each call to `append` writes exactly one line to the configured file.
    The file is created if it does not exist; parent directories are also created.
    """

    def __init__(self, log_path: str = "data/audit_log.jsonl") -> None:
        self._path = Path(log_path)
        # Ensure the directory exists without affecting file contents
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def append(self, event: AuditEvent) -> None:
        """
        Persist a single audit event as one JSON object per line.

        This method is intentionally simple:
        - No buffering
        - No rotation
        - No mutation of the event object

        Those concerns, if needed, should be handled by a separate layer.
        """
        line = json.dumps(event.to_dict(), sort_keys=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

def log_decision_dict(decision: Dict[str, Any], decision_correlation_id: Optional[str] = None) -> None:
    """
    Convenience helper: take a decision dict (as returned by the authority
    engine) and append it to the audit log as an AuditEvent.

    This keeps all audit writing logic in one place.
    """
    logger = AuditLogger()

    event = AuditEvent(
        identity_label=decision["identity_label"],
        requested_permission_name=decision["requested_permission_name"],
        system_state=decision["system_state"],
        decision=decision["decision"],
        policy_ids=decision.get("policy_ids", []),
        reason=decision.get("reason", ""),
        timestamp=decision.get("timestamp", ""),
        decision_correlation_id=decision_correlation_id,
        delegate_identity_label=decision.get("delegate_identity_label"),
        principal_identity_labels=decision.get("principal_identity_labels", []),
        delegation_ids=decision.get("delegation_ids", []),
    )

    logger.append(event)
