"""
Basic behavior checks for the AuthorityEngine.

These tests are intentionally simple and self-contained.
They exist to prove the authority resolution behavior defined
in the foundation documents.
"""

from enum import Enum
from authority_engine import AuthorityEngine, AuthorityDecision


# ---------------------------------------------------------------------------
# Minimal supporting types
# ---------------------------------------------------------------------------

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
    def __init__(self, active: bool = True):
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
    def __init__(self, applicable_role_names, permission_names, condition):
        self.applicable_role_names = applicable_role_names
        self.permission_names = permission_names
        self.condition = condition

    def applies_to_role(self, role_name: str):
        return role_name in self.applicable_role_names

    def allows_permission(self, permission_name: str):
        return permission_name in self.permission_names


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_allow_basic_case():
    engine = AuthorityEngine()

    identity = FakeIdentity(active=True)
    identity.add_credential(FakeCredential("SOVEREIGN_OWNER"))
    identity.assign_role("SOVEREIGN_OWNER")

    role = FakeRole("SOVEREIGN_OWNER", {"SOVEREIGN_OWNER"})
    role.add_permission(FakePermission("AUTHORIZE_EMERGENCY_LOCKDOWN"))

    roles_by_name = {"SOVEREIGN_OWNER": role}

    policy = FakePolicy(
        applicable_role_names={"SOVEREIGN_OWNER"},
        permission_names={"AUTHORIZE_EMERGENCY_LOCKDOWN"},
        condition=PolicyCondition(SystemState.CRISIS, minimum_approvals=1),
    )

    decision = engine.resolve(
        identity=identity,
        requested_permission_name="AUTHORIZE_EMERGENCY_LOCKDOWN",
        system_state=SystemState.CRISIS,
        roles_by_name=roles_by_name,
        policies=[policy],
    )

    assert decision == AuthorityDecision.ALLOW


def test_deny_wrong_state():
    engine = AuthorityEngine()

    identity = FakeIdentity(active=True)
    identity.add_credential(FakeCredential("SOVEREIGN_OWNER"))
    identity.assign_role("SOVEREIGN_OWNER")

    role = FakeRole("SOVEREIGN_OWNER", {"SOVEREIGN_OWNER"})
    role.add_permission(FakePermission("AUTHORIZE_EMERGENCY_LOCKDOWN"))

    roles_by_name = {"SOVEREIGN_OWNER": role}

    policy = FakePolicy(
        applicable_role_names={"SOVEREIGN_OWNER"},
        permission_names={"AUTHORIZE_EMERGENCY_LOCKDOWN"},
        condition=PolicyCondition(SystemState.CRISIS, minimum_approvals=1),
    )

    decision = engine.resolve(
        identity=identity,
        requested_permission_name="AUTHORIZE_EMERGENCY_LOCKDOWN",
        system_state=SystemState.NORMAL,
        roles_by_name=roles_by_name,
        policies=[policy],
    )

    assert decision == AuthorityDecision.DENY


def test_require_additional_approval():
    engine = AuthorityEngine()

    identity = FakeIdentity(active=True)
    identity.add_credential(FakeCredential("FAMILY_GUARDIAN"))
    identity.assign_role("FAMILY_GUARDIAN")

    role = FakeRole("FAMILY_GUARDIAN", {"FAMILY_GUARDIAN"})
    role.add_permission(FakePermission("AUTHORIZE_EMERGENCY_LOCKDOWN"))

    roles_by_name = {"FAMILY_GUARDIAN": role}

    policy = FakePolicy(
        applicable_role_names={"FAMILY_GUARDIAN"},
        permission_names={"AUTHORIZE_EMERGENCY_LOCKDOWN"},
        condition=PolicyCondition(SystemState.CRISIS, minimum_approvals=2),
    )

    decision = engine.resolve(
        identity=identity,
        requested_permission_name="AUTHORIZE_EMERGENCY_LOCKDOWN",
        system_state=SystemState.CRISIS,
        roles_by_name=roles_by_name,
        policies=[policy],
    )

    assert decision == AuthorityDecision.REQUIRE_ADDITIONAL_APPROVAL


if __name__ == "__main__":
    test_allow_basic_case()
    test_deny_wrong_state()
    test_require_additional_approval()
    print("All basic authority engine tests passed.")

