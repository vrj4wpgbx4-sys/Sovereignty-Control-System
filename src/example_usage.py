from datetime import datetime

from models import (
    Identity,
    Credential,
    Role,
    Permission,
    Policy,
    PolicyCondition,
    IdentityStatus,
    CredentialStatus,
    PermissionAction,
    PermissionDomain,
    SystemState,
)


def main():
    # ------------------------------------------------------------------
    # Define permissions
    # ------------------------------------------------------------------
    view_assets = Permission(
        name="VIEW_ASSET_SUMMARY",
        domain=PermissionDomain.ASSETS,
        action=PermissionAction.VIEW,
    )

    emergency_lockdown = Permission(
        name="AUTHORIZE_EMERGENCY_LOCKDOWN",
        domain=PermissionDomain.SYSTEM,
        action=PermissionAction.EXECUTE,
    )

    # ------------------------------------------------------------------
    # Define roles
    # ------------------------------------------------------------------
    sovereign_owner = Role(
        name="SOVEREIGN_OWNER",
        description="Primary authority over the system."
    )
    sovereign_owner.add_permission(view_assets)
    sovereign_owner.add_permission(emergency_lockdown)

    family_guardian = Role(
        name="FAMILY_GUARDIAN",
        description="Trusted individual with limited emergency authority."
    )
    family_guardian.add_permission(view_assets)

    # ------------------------------------------------------------------
    # Create identities
    # ------------------------------------------------------------------
    ronald = Identity(
        id="id-ronald-001",
        display_name="Ronald Fenlon",
        status=IdentityStatus.ACTIVE,
    )

    guardian = Identity(
        id="id-guardian-001",
        display_name="Family Guardian",
        status=IdentityStatus.ACTIVE,
    )

    # ------------------------------------------------------------------
    # Issue credentials
    # ------------------------------------------------------------------
    owner_credential = Credential(
        id="cred-001",
        issuer_id="system",
        subject_id=ronald.id,
        claim_type="ROLE_ASSERTION",
        claim_value="SOVEREIGN_OWNER",
        issued_at=datetime.utcnow(),
        status=CredentialStatus.VALID,
    )

    guardian_credential = Credential(
        id="cred-002",
        issuer_id="system",
        subject_id=guardian.id,
        claim_type="ROLE_ASSERTION",
        claim_value="FAMILY_GUARDIAN",
        issued_at=datetime.utcnow(),
        status=CredentialStatus.VALID,
    )

    ronald.add_credential(owner_credential)
    guardian.add_credential(guardian_credential)

    ronald.assign_role("SOVEREIGN_OWNER")
    guardian.assign_role("FAMILY_GUARDIAN")

    # ------------------------------------------------------------------
    # Define a policy
    # ------------------------------------------------------------------
    emergency_policy = Policy(
        id="policy-001",
        name="Emergency Lockdown Policy",
        description="Allows emergency lockdown during crisis state.",
        applicable_role_names={"SOVEREIGN_OWNER", "FAMILY_GUARDIAN"},
        permission_names={"AUTHORIZE_EMERGENCY_LOCKDOWN"},
        condition=PolicyCondition(
            required_system_state=SystemState.CRISIS,
            minimum_approvals=2,
        ),
    )

    # ------------------------------------------------------------------
    # Demonstrate behavior
    # ------------------------------------------------------------------
    print("=== Identity Overview ===")
    print(f"{ronald.display_name} roles: {ronald.role_names}")
    print(f"{guardian.display_name} roles: {guardian.role_names}")

    print("\n=== Role Permissions ===")
    print("SOVEREIGN_OWNER permissions:")
    for p in sovereign_owner.permissions:
        print("  ", p)

    print("\n=== Policy Check ===")
    print(f"Policy '{emergency_policy.name}' applies to FAMILY_GUARDIAN:",
          emergency_policy.applies_to_role("FAMILY_GUARDIAN"))
    print(f"Policy allows emergency lockdown:",
          emergency_policy.allows_permission("AUTHORIZE_EMERGENCY_LOCKDOWN"))


if __name__ == "__main__":
    main()
