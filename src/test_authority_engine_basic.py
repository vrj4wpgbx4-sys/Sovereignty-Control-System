"""
Basic behavior checks for the AuthorityEngine.

These tests use minimal "fake" classes defined in this file so that they do not
depend on any other modules. They are here to document and verify the core
behavior described in the foundation documents.
"""

from enum import Enum
from datetime import datetime, timedelta

from authority_engine import AuthorityEngine, AuthorityDecision


# ---------------------------------------------------------------------------
# Minimal fakes to satisfy the engine's expectations
# ---------------------------------------------------------------------------

class IdentityStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class SystemState(Enum):
    NORMAL = "normal"
    CRISIS = "crisis"


class FakeCredential:
    def __init__(self, claim_value: str, valid: bool = True):
        self.claim_value = claim_value
        self._valid = valid

    def is_currently_valid(self, at_time: datetime | None = None) -> bool:
        return self._valid


class FakeIdentity:
    def __init__(self, display_name: str, active: bool = True):
        self.display_name = display_name
        self._active = active
        self.status = IdentityStatus.ACTIVE if active else IdentityStatus.SUSPENDED
        self.credentials: list[FakeCredential] = []
        self.role_names: set[str] = set()

    def is_active(self) -> bool:
        return self._active

    def add_credential(self, cred: FakeCredential) -> None:
        self.credentials.append(cred)

    def assign_role(self, role_name: str) -> None:
        self.role_names.add(role_name)


class FakePermission:
    def __init__(self, name: str):
        self.name = name


class FakeRole:
    def __init__(self, name: str, required_credential_types: set[str] | None = None):
        self.name = name
        self.required_credential_types = required_credential_types or set()
        self.permissions: set[FakePermission] = set()

    def add_permission(self, perm: FakePermission) -> None:
        self.permissions.add(perm)

    def has_permission(self, permission_name: str) -> bool:
        return any(p.name == permission_name for p in self.permissions)


class PolicyCondition:
    def __init__(
        self,
        required_system_state: SystemState | None = None,
        minimum_approvals: int = 1,
    ):
        self.required_system_state = required_system_state
        self.minimum_approvals = minimum_approvals
        self.time_window_seconds: int | None = None


class FakePolicy:
    def __init__(
        self,
        policy_id: str,
        name: str,
        applicable_role_names: set[str],
        permission_names: set[str],
        condition: PolicyCondition,
    ):
        self.id = policy_id
        self.name = name
        self.applicable_role_names = applicable_role_names
        self.permission_names = permission_names
        self.condition = condition

    def applies_to_role(self, role_name: str) -> bool:
        return role_name in self.applicable_role_names

    def allows_permission(self, permission_name: str) -> bool:
        return permission_name in self.permission_names


# ---------------------------------------------------------------------------
# Test Scenarios
# ---------------------------------------------------------------------------

def test_allow_basic_case():
    """
    Active identity, valid credential, role grants permission,
    policy allows in current system state => ALLOW.
    """
    engine = AuthorityEngine()

    identity = FakeIdentity("Ronald", active=True)
    identity.add_credential(FakeCredential(claim_value="SOVEREIGN_OWNER", valid=True))
    identity.assign_role("SOVEREIGN_OWNER")

    role = FakeRole("SOVEREIGN_OWNER", required_credential_types={"SOVEREIGN_OWNER"})
    perm = FakePermission("AUTHORIZE_EMERGENCY_LOCKDOWN")
    role.add_permission(perm)

    roles_by_name = {"SOVEREIGN_OWNER": role}

    condition = PolicyCondition(required_system_state=SystemState.CRISIS, minimum_approvals=1)
    policy = FakePolicy(
        policy_id="policy-001",
        name="Emergency Lockdown Policy",
        applicable_role_names={"SOVEREIGN_OWNER"},
        permission_names={"AUTHORIZE_EMERGENCY_LOCKDOWN"},
        condition=condition,
    )

    decision = engine.resolve(
        identity=identity,
        requested_permission_name="AUTHORIZE_EMERGENCY_LOCKDOWN",
        system_state=SystemState.CRISIS,
        roles_by_name=roles_by_name,
        policies=[policy],
    )

    assert decision == AuthorityDecision.ALLOW, f"Expected ALLOW, got {decision}"


def test_deny_wrong_state():
    """
    Same setup as above, but system state is NORMAL while policy
    requires CRISIS => DENY.
    """
    engine = AuthorityEngine()

    identity = FakeIdentity("Ronald", active=True)
    identity.add_credential(FakeCredential(claim_value="SOVEREIGN_OWNER", valid=True))
    identity.assign_role("SOVEREIGN_OWNER")

    role = FakeRole("SOVEREIGN_OWNER", required_credential_types={"SOVEREIGN_OWNER"})
    perm = FakePermission("AUTHORIZE_EMERGENCY_LOCKDOWN")
    role.add_permission(perm)

    roles_by_name = {"SOVEREIGN_OWNER": role}

    condition = PolicyCondition(required_system_state=SystemState.CRISIS, minimum_approvals=1)
    policy = FakePolicy(
        policy_id="policy-001",
        name="Emergency Lockdown Policy",
        applicable_role_names={"SOVEREIGN_OWNER"},
        permission_names={"AUTHORIZE_EMERGENCY_LOCKDOWN"},
        condition=condition,
    )

    decision = engine.resolve(
        identity=identity,
        requested_permission_name="AUTHORIZE_EMERGENCY_LOCKDOWN",
        system_state=SystemState.NORMAL,
        roles_by_name=roles_by_name,
        policies=[policy],
    )

    # Engine will walk policies but none will match the required state, so it DENIES.
    assert decision == AuthorityDecision.DENY, f"Expected DENY, got {decision}"


def test_require_additional_approval():
    """
    Policy requires more than one approval => REQUIRE_ADDITIONAL_APPROVAL.
    """
    engine = AuthorityEngine()

    identity = FakeIdentity("Guardian", active=True)
    identity.add_credential(FakeCredential(claim_value="FAMILY_GUARDIAN", valid=True))
    identity.assign_role("FAMILY_GUARDIAN")

    role = FakeRole("FAMILY_GUARDIAN", required_credential_types={"FAMILY_GUARDIAN"})
    perm = FakePermission("AUTHORIZE_EMERGENCY_LOCKDOWN")
    role.add_permission(perm)

    roles_by_name = {"FAMILY_GUARDIAN": role}

    condition = PolicyCondition(required_system_state=SystemState.CRISIS, minimum_approvals=2)
    policy = FakePolicy(
        policy_id="policy-002",
        name="Guardian Emergency Lockdown Policy",
        applicable_role_names={"FAMILY_GUARDIAN"},
        permission_names={"AUTHORIZE_EMERGENCY_LOCKDOWN"},
        condition=condition,
    )

    decision = engine.resolve(
        identity=identity,
        requested_permission_name="AUTHORIZE_EMERGENCY_LOCKDOWN",
        system_state=SystemState.CRISIS,
        roles_by_name=roles_by_name,
        policies=[policy],
    )

    assert decision == AuthorityDecision.REQUIRE_ADDITIONAL_APPROVAL, (
        f"Expected REQUIRE_ADDITIONAL_APPROVAL, got {decision}"
    )


if __name__ == "__main__":
    # Simple manual runner that will raise errors if any test fails.
    test_allow_basic_case()
    test_deny_wrong_state()
    test_require_additional_approval()
    print("All basic authority engine tests passed.")

Add basic behavior tests for authority engine

