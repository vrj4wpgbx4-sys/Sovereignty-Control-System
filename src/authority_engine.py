"""
Authority Resolution Engine

Implements the authority resolution flow defined in:
docs/AUTHORITY_RESOLUTION_AND_STATE_MODEL.md

This engine is intentionally minimal and deterministic.
"""

from enum import Enum
from typing import List


# ---------------------------------------------------------------------------
# Decision Outcomes
# ---------------------------------------------------------------------------

class AuthorityDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_ADDITIONAL_APPROVAL = "require_additional_approval"
    DEFER = "defer"


# ---------------------------------------------------------------------------
# Authority Engine
# ---------------------------------------------------------------------------

class AuthorityEngine:
    """
    Core authority resolution engine.

    This class does NOT:
    - Execute actions
    - Modify system state
    - Persist data

    It evaluates authority and returns a decision.
    """

    def resolve(
        self,
        *,
        identity,
        requested_permission_name: str,
        system_state,
        roles_by_name: dict,
        policies: List,
    ) -> AuthorityDecision:
        """
        Resolve whether an identity may perform a requested action.
        """

        # ------------------------------------------------------------------
        # Step 1 — Identity Validation
        # ------------------------------------------------------------------
        if not identity.is_active():
            return AuthorityDecision.DENY

        # ------------------------------------------------------------------
        # Step 2 — Credential Validation
        # ------------------------------------------------------------------
        valid_credentials = [
            c for c in identity.credentials if c.is_currently_valid()
        ]

        if not valid_credentials:
            return AuthorityDecision.DENY

        # ------------------------------------------------------------------
        # Step 3 — Role Resolution
        # ------------------------------------------------------------------
        resolved_roles = []

        for role_name in identity.role_names:
            role = roles_by_name.get(role_name)
            if not role:
                continue

            # Check credential requirements
            if role.required_credential_types:
                credential_types = {c.claim_value for c in valid_credentials}
                if not role.required_credential_types.issubset(credential_types):
                    continue

            resolved_roles.append(role)

        if not resolved_roles:
            return AuthorityDecision.DENY

        # ------------------------------------------------------------------
        # Step 4 — Permission Matching
        # ------------------------------------------------------------------
        roles_granting_permission = [
            role for role in resolved_roles
            if role.has_permission(requested_permission_name)
        ]

        if not roles_granting_permission:
            return AuthorityDecision.DENY

        # ------------------------------------------------------------------
        # Step 5 — Policy Evaluation
        # ------------------------------------------------------------------
        applicable_policies = [
            policy for policy in policies
            if any(policy.applies_to_role(role.name) for role in roles_granting_permission)
            and policy.allows_permission(requested_permission_name)
        ]

        if not applicable_policies:
            return AuthorityDecision.DENY

        for policy in applicable_policies:
            condition = policy.condition

            # Check system state requirement
            if condition.required_system_state:
                if system_state != condition.required_system_state:
                    continue

            # Check approval thresholds
            if condition.minimum_approvals > 1:
                return AuthorityDecision.REQUIRE_ADDITIONAL_APPROVAL

            return AuthorityDecision.ALLOW

        # ------------------------------------------------------------------
        # Step 6 — Fail Safe
        # ------------------------------------------------------------------
        return AuthorityDecision.DENY
