"""
Basic smoke test for the AuditEvent structure.

This test verifies that an AuditEvent can be created and serialized
without errors.
"""

from audit_event import AuditEvent


def test_audit_event_creation():
    event = AuditEvent(
        identity_label="Ronald",
        requested_permission_name="AUTHORIZE_EMERGENCY_LOCKDOWN",
        system_state="CRISIS",
        decision="ALLOW",
        policy_ids=["policy-001"],
        reason="Emergency authority exercised",
    )

    event_dict = event.to_dict()

    assert event_dict["identity_label"] == "Ronald"
    assert event_dict["decision"] == "ALLOW"
    assert event_dict["system_state"] == "CRISIS"
    assert "timestamp" in event_dict


if __name__ == "__main__":
    test_audit_event_creation()
    print("AuditEvent test passed.")
