"""
Audit event structure for authority decisions.

This does NOT persist anything. It simply defines the shape of an
audit record that can be logged, stored, or transmitted by whatever
infrastructure you choose later.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class AuditEvent:
    """
    Represents a single authority decision at a point in time.
    """

    identity_label: str
    requested_permission_name: str
    system_state: str
    decision: str
    policy_ids: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert this audit event to a simple dictionary for logging,
        JSON serialization, or storage.
        """
        return {
            "identity_label": self.identity_label,
            "requested_permission_name": self.requested_permission_name,
            "system_state": self.system_state,
            "decision": self.decision,
            "policy_ids": list(self.policy_ids),
            "timestamp": self.timestamp.isoformat() + "Z",
            "reason": self.reason,
        }
