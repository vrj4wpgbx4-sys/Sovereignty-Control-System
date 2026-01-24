"""
End-to-end demo: authority decision + audit event.

This script:
- Builds a minimal in-memory scenario (identity, role, permission, policy, state)
- Calls AuthorityEngine.resolve_with_audit(...)
- Prints the decision and the audit record

This represents a thin integration layer ON TOP of the core.
"""

from enum import Enum

from audit_logger import AuditLogger


from authority_engine import AuthorityEngine
from audit_event import AuditEvent


class IdentityStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class SystemState(Enum):
    NORMAL = "normal"
    CRISIS = "crisis"


class FakeCredential:
    def __init__(self, claim_value: str, valid: bool = True):
        self.claim_value = claim_value
        self._valid = valid

    def is_currently_valid(self):
        return self._valid


class FakeIdentity:
    def __init__(self, display_name: str, active: bool = True):
        self.display_name = display_name
        self.status = IdentityStatus.ACTIVE if active else IdentityStatus.SUSPENDED
        self.credentials = []
        self.role_names = set()

    def is_active(self):
        return self.status == IdentityStatus.ACTIVE

    def add_credential(self, credential):
        self.credentials.append(credential)

    def assign_role(self, role_name: str):
        self.role_names.add(role_name)


class FakePermission:
    def __init__(self, name: str):
        self.name = name


class FakeRole:
    def __init__(self, name: str, required_credential_types=None):
        self.name = name
        self.required_credential_types = required_credential_types or set()
        self.permissions = set()

    def add_permission(self, permission):
        self.permissions.add(permission)

    def has_permission(self, permission_name: str):
        return any(p.name == permission_name for p in self.permissions)


class PolicyCondition:
    def __init__(self, required_system_state=None, minimum_approvals=1):
        self.required_system_state = required_system_state
        self.minimum_approvals = minimum_approvals


class FakePolicy:
    def __init__(self, applicable_role_names, permission_names, condition, policy_id: str):
        self.applicable_role_names = applicable_role_names
        self.permission_names = permission_names
        self.condition = condition
        self.id = policy_id

    def applies_to_role(self, role_name: str):
        return role_name in self.applicable_role_names

    def allows_permission(self, permission_name: str):
        return permission_name in self.permission_names


if __name__ == "__main__":
    engine = AuthorityEngine()

    # Identity with sovereign-level authority
    identity = FakeIdentity(display_name="Ronald", active=True)
    identity.add_credential(FakeCredential("SOVEREIGN_OWNER"))
    identity.assign_role("SOVEREIGN_OWNER")

    # Role + permission
    role = FakeRole("SOVEREIGN_OWNER", {"SOVEREIGN_OWNER"})
    perm_name = "AUTHORIZE_EMERGENCY_LOCKDOWN"
    perm = FakePermission(perm_name)
    role.add_permission(perm)
    roles_by_name = {"SOVEREIGN_OWNER": role}

    # Policy requiring CRISIS state, single approval
    condition = PolicyCondition(required_system_state=SystemState.CRISIS, minimum_approvals=1)
    policy = FakePolicy(
        applicable_role_names={"SOVEREIGN_OWNER"},
        permission_names={perm_name},
        condition=condition,
        policy_id="policy-001",
    )

    decision, event = engine.resolve_with_audit(
        identity=identity,
        requested_permission_name=perm_name,
        system_state=SystemState.CRISIS,
        roles_by_name=roles_by_name,
        policies=[policy],
        identity_label=identity.display_name,
        policy_ids=[policy.id],
        reason="Integration demo: sovereign owner authorizes emergency lockdown in crisis state",
    )

    print("Decision:", decision)
    print("Audit event:")
    print(event.to_dict())

     # Write to local audit log
    logger = AuditLogger(log_path="data/audit_log.jsonl")
    logger.append(event)
    print("Audit event written to data/audit_log.jsonl")
