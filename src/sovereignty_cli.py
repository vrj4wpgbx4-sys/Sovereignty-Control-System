"""
Sovereignty Control System - CLI Demo

This CLI runs on top of the integration layer:

- Uses AuthorityEngine to make decisions
- Uses AuditLogger to write audit events to data/audit_log.jsonl
- Lets you trigger a few predefined scenarios from the command line

Core remains untouched. This is integration / UX only.
"""

from enum import Enum

from authority_engine import AuthorityEngine
from audit_logger import AuditLogger
from audit_event import AuditEvent


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
    def __init__(self, required_system_state=None, minimum_approvals: int = 1):
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


# ---------------------------------------------------------------------------
# Scenario builders
# ---------------------------------------------------------------------------

def build_scenario_sov_executive_lockdown(system_state: SystemState):
    """
    Scenario 1 / 2:
    Sovereign Owner tries to authorize emergency lockdown.
    Outcome depends on system_state.
    """
    identity = FakeIdentity(display_name="Ronald", active=True)
    identity.add_credential(FakeCredential("SOVEREIGN_OWNER"))
    identity.assign_role("SOVEREIGN_OWNER")

    perm_name = "AUTHORIZE_EMERGENCY_LOCKDOWN"

    role = FakeRole("SOVEREIGN_OWNER", {"SOVEREIGN_OWNER"})
    role.add_permission(FakePermission(perm_name))
    roles_by_name = {"SOVEREIGN_OWNER": role}

    condition = PolicyCondition(required_system_state=SystemState.CRISIS, minimum_approvals=1)
    policy = FakePolicy(
        applicable_role_names={"SOVEREIGN_OWNER"},
        permission_names={perm_name},
        condition=condition,
        policy_id="policy-001",
    )

    reason = f"Sovereign owner attempts emergency lockdown in {system_state.name} state"

    return identity, roles_by_name, [policy], perm_name, [policy.id], reason


def build_scenario_guardian_lockdown(system_state: SystemState):
    """
    Scenario 3:
    Family Guardian attempts emergency lockdown, but policy
    requires two approvals. Engine should respond with
    REQUIRE_ADDITIONAL_APPROVAL in CRISIS state.
    """
    identity = FakeIdentity(display_name="Guardian", active=True)
    identity.add_credential(FakeCredential("FAMILY_GUARDIAN"))
    identity.assign_role("FAMILY_GUARDIAN")

    perm_name = "AUTHORIZE_EMERGENCY_LOCKDOWN"

    role = FakeRole("FAMILY_GUARDIAN", {"FAMILY_GUARDIAN"})
    role.add_permission(FakePermission(perm_name))
    roles_by_name = {"FAMILY_GUARDIAN": role}

    condition = PolicyCondition(required_system_state=SystemState.CRISIS, minimum_approvals=2)
    policy = FakePolicy(
        applicable_role_names={"FAMILY_GUARDIAN"},
        permission_names={perm_name},
        condition=condition,
        policy_id="policy-002",
    )

    reason = "Family guardian attempts emergency lockdown (policy requires two approvals)"

    return identity, roles_by_name, [policy], perm_name, [policy.id], reason


# ---------------------------------------------------------------------------
# CLI core
# ---------------------------------------------------------------------------

def run_scenario(
    engine: AuthorityEngine,
    logger: AuditLogger,
    identity: FakeIdentity,
    roles_by_name,
    policies,
    perm_name: str,
    system_state: SystemState,
    policy_ids,
    reason: str,
):
    decision, event = engine.resolve_with_audit(
        identity=identity,
        requested_permission_name=perm_name,
        system_state=system_state,
        roles_by_name=roles_by_name,
        policies=policies,
        identity_label=identity.display_name,
        policy_ids=policy_ids,
        reason=reason,
    )

    print("\n=== Decision Result ===")
    print("Identity:", identity.display_name)
    print("System state:", system_state.name)
    print("Requested permission:", perm_name)
    print("Decision:", decision.name)
    print("Audit event:")
    print(event.to_dict())

    logger.append(event)
    print("Audit event written to data/audit_log.jsonl\n")


def print_menu():
    print("=== Sovereignty Control System CLI ===")
    print("1) Sovereign owner – emergency lockdown in CRISIS state (expected: ALLOW)")
    print("2) Sovereign owner – emergency lockdown in NORMAL state (expected: DENY)")
    print("3) Family guardian – emergency lockdown in CRISIS (expected: REQUIRE_ADDITIONAL_APPROVAL)")
    print("q) Quit")
    print()


def main():
    engine = AuthorityEngine()
    logger = AuditLogger(log_path="data/audit_log.jsonl")

    while True:
        print_menu()
        choice = input("Select an option: ").strip().lower()

        if choice == "q":
            print("Exiting CLI.")
            break

        elif choice == "1":
            identity, roles_by_name, policies, perm_name, policy_ids, reason = \
                build_scenario_sov_executive_lockdown(SystemState.CRISIS)
            run_scenario(
                engine,
                logger,
                identity,
                roles_by_name,
                policies,
                perm_name,
                SystemState.CRISIS,
                policy_ids,
                reason,
            )

        elif choice == "2":
            identity, roles_by_name, policies, perm_name, policy_ids, reason = \
                build_scenario_sov_executive_lockdown(SystemState.NORMAL)
            run_scenario(
                engine,
                logger,
                identity,
                roles_by_name,
                policies,
                perm_name,
                SystemState.NORMAL,
                policy_ids,
                reason,
            )

        elif choice == "3":
            identity, roles_by_name, policies, perm_name, policy_ids, reason = \
                build_scenario_guardian_lockdown(SystemState.CRISIS)
            run_scenario(
                engine,
                logger,
                identity,
                roles_by_name,
                policies,
                perm_name,
                SystemState.CRISIS,
                policy_ids,
                reason,
            )

        else:
            print("Unrecognized option. Please choose 1, 2, 3, or q.\n")


if __name__ == "__main__":
    main()
