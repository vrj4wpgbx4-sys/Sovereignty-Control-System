
"""
Sovereignty Control System - Config-Driven CLI with Explainability

This CLI:
- Loads scenario definitions from config/governance_scenarios.json
- Loads policy definitions from config/governance_policies.json
- Builds identities, roles, permissions, and policies from config
- Uses AuthorityEngine + AuditLogger to decide and record outcomes
- Prints which policies were applied and why
"""

from enum import Enum

from authority_engine import AuthorityEngine
from audit_logger import AuditLogger
from scenario_config_loader import load_scenarios
from policy_config_loader import load_policies


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


def build_scenario_from_config(scenario_cfg: dict, policy_cfg: dict):
    """
    Build identity, roles, policies, and metadata from scenario + policy config.
    """
    identity = FakeIdentity(display_name=scenario_cfg["identity_display_name"], active=True)
    identity.add_credential(FakeCredential(scenario_cfg["credential"]))
    identity.assign_role(scenario_cfg["role_name"])

    role = FakeRole(scenario_cfg["role_name"], {scenario_cfg["credential"]})
    perm_name = scenario_cfg["permission_name"]
    perm = FakePermission(perm_name)
    role.add_permission(perm)
    roles_by_name = {scenario_cfg["role_name"]: role}

    cond_cfg = policy_cfg.get("conditions", {})
    required_state_name = (
        cond_cfg.get("required_system_state")
        or cond_cfg.get("system_state")
        or scenario_cfg["system_state"]
    )
    minimum_approvals = int(
        cond_cfg.get("minimum_approvals", scenario_cfg.get("minimum_approvals", 1))
    )

    required_state = SystemState[required_state_name]

    condition = PolicyCondition(
        required_system_state=required_state,
        minimum_approvals=minimum_approvals,
    )

    policy = FakePolicy(
        applicable_role_names={scenario_cfg["role_name"]},
        permission_names={perm_name},
        condition=condition,
        policy_id=policy_cfg["id"],
    )

    system_state = SystemState[scenario_cfg["system_state"]]
    policy_ids = [policy_cfg["id"]]
    reason = scenario_cfg.get("reason") or policy_cfg.get("reason", "No reason provided")

    return identity, roles_by_name, [policy], perm_name, system_state, policy_ids, reason


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
    active_policies: list,
):
    """
    Run a single scenario, print decision and explain which policies were applied.
    """
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

    # Explainability block: which policies applied, in human terms
    print("\nApplied policies:")
    if not active_policies:
        print("  (none – check configuration)")
    else:
        for p in active_policies:
            pid = p.get("id", "(no id)")
            name = p.get("name", "(no name)")
            preason = p.get("reason", "").strip()
            if preason:
                print(f"  - {pid}: {name} – {preason}")
            else:
                print(f"  - {pid}: {name}")

    print("\nAudit event:")
    print(event.to_dict())

    logger.append(event)
    print("Audit event written to data/audit_log.jsonl\n")


def print_menu(scenarios: dict):
    print("=== Sovereignty Control System CLI ===")
    for key in sorted(scenarios.keys(), key=lambda x: int(x) if x.isdigit() else x):
        cfg = scenarios[key]
        label = cfg.get("label", f"Scenario {key}")
        expected = cfg.get("expected_decision", "?")
        print(f"{key}) {label} (expected: {expected})")
    print("q) Quit")
    print()


def main():
    engine = AuthorityEngine()
    logger = AuditLogger(log_path="data/audit_log.jsonl")

    scenarios = load_scenarios()
    policies_by_id = load_policies()

    while True:
        print_menu(scenarios)
        choice = input("Select an option: ").strip().lower()

        if choice == "q":
            print("Exiting CLI.")
            break

        scenario_cfg = scenarios.get(choice)
        if not scenario_cfg:
            print("Unrecognized option. Please choose a listed number or 'q' to quit.\n")
            continue

        policy_id = scenario_cfg.get("policy_id")
        if not policy_id or policy_id not in policies_by_id:
            print(f"No policy found for scenario (policy_id={policy_id!r}). Check configuration.\n")
            continue

        policy_cfg = policies_by_id[policy_id]

        (
            identity,
            roles_by_name,
            policies,
            perm_name,
            system_state,
            policy_ids,
            reason,
        ) = build_scenario_from_config(scenario_cfg, policy_cfg)

        run_scenario(
            engine,
            logger,
            identity,
            roles_by_name,
            policies,
            perm_name,
            system_state,
            policy_ids,
            reason,
            active_policies=[policy_cfg],
        )


if __name__ == "__main__":
    main()
