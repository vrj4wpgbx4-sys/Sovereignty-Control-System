"""
Authority Resolution Engine

Implements the authority resolution flow defined in:
docs/AUTHORITY_RESOLUTION_AND_STATE_MODEL.md

This engine is intentionally minimal and deterministic.

- resolve(...) returns only the AuthorityDecision
- resolve_with_audit(...) returns (AuthorityDecision, AuditEvent)
"""

from enum import Enum
from typing import List, Dict, Tuple, Optional, Any

from audit_event import AuditEvent


class AuthorityDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_ADDITIONAL_APPROVAL = "require_additional_approval"
    DEFER = "defer"


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
        identity: Any,
        requested_permission_name: str,
        system_state: Any,
        roles_by_name: Dict[str, Any],
        policies: List[Any],
    ) -> AuthorityDecision:
        """
        Resolve whether an identity may perform a requested action.

        This method follows the flow defined in:
        docs/AUTHORITY_RESOLUTION_AND_STATE_MODEL.md
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
            c for c in getattr(identity, "credentials", []) if c.is_currently_valid()
        ]

        if not valid_credentials:
            return AuthorityDecision.DENY

        # ------------------------------------------------------------------
        # Step 3 — Role Resolution
        # ------------------------------------------------------------------
        resolved_roles = []

        for role_name in getattr(identity, "role_names", []):
            role = roles_by_name.get(role_name)
            if not role:
                continue

            # Check credential requirements
            required_types = getattr(role, "required_credential_types", set())
            if required_types:
                credential_types = {c.claim_value for c in valid_credentials}
                if not required_types.issubset(credential_types):
                    continue

            resolved_roles.append(role)

        if not resolved_roles:
            return AuthorityDecision.DENY

        # ------------------------------------------------------------------
        # Step 4 — Permission Matching
        # ------------------------------------------------------------------
        roles_granting_permission = [
            role
            for role in resolved_roles
            if role.has_permission(requested_permission_name)
        ]

        if not roles_granting_permission:
            return AuthorityDecision.DENY

        # ------------------------------------------------------------------
        # Step 5 — Policy Evaluation
        # ------------------------------------------------------------------
        applicable_policies = []
        for policy in policies:
            # Policy must apply to at least one of the roles
            if not any(policy.applies_to_role(role.name) for role in roles_granting_permission):
                continue
            # And must explicitly allow this permission
            if not policy.allows_permission(requested_permission_name):
                continue
            applicable_policies.append(policy)

        if not applicable_policies:
            return AuthorityDecision.DENY

        for policy in applicable_policies:
            condition = policy.condition

            # Check system state requirement
            required_state = getattr(condition, "required_system_state", None)
            if required_state is not None and system_state != required_state:
                # Policy does not apply in this state
                continue

            # Check approval thresholds
            minimum_approvals = getattr(condition, "minimum_approvals", 1)
            if minimum_approvals > 1:
                return AuthorityDecision.REQUIRE_ADDITIONAL_APPROVAL

            # If we reach here, this policy allows the action
            return AuthorityDecision.ALLOW

        # ------------------------------------------------------------------
        # Step 6 — Fail Safe
        # ------------------------------------------------------------------
        return AuthorityDecision.DENY

    # ----------------------------------------------------------------------
    # New: resolve_with_audit
    # ----------------------------------------------------------------------
    def resolve_with_audit(
        self,
        *,
        identity: Any,
        requested_permission_name: str,
        system_state: Any,
        roles_by_name: Dict[str, Any],
        policies: List[Any],
        identity_label: Optional[str] = None,
        policy_ids: Optional[List[str]] = None,
        reason: Optional[str] = None,
    ) -> Tuple[AuthorityDecision, AuditEvent]:
        """
        Resolve authority AND construct an AuditEvent for the decision.

        This does not persist or log the event; it only creates the structure
        so the caller can decide where and how to store it.

        Parameters:
        - identity: the identity object being evaluated
        - requested_permission_name: name of the requested permission
        - system_state: current system state (Enum or string-like)
        - roles_by_name: mapping of role name -> role object
        - policies: list of policy objects considered for this decision
        - identity_label: optional human-readable label for audit
        - policy_ids: optional list of policy identifiers used in evaluation
        - reason: optional human-readable reason or context

        Returns:
        - (AuthorityDecision, AuditEvent)
        """

        decision = self.resolve(
            identity=identity,
            requested_permission_name=requested_permission_name,
            system_state=system_state,
            roles_by_name=roles_by_name,
            policies=policies,
        )

        # Normalize system_state for audit
        if hasattr(system_state, "name"):
            system_state_value = system_state.name
        else:
            system_state_value = str(system_state)

        # Normalize decision for audit
        decision_value = decision.name

        # Default identity label
        if identity_label is None:
            identity_label = getattr(identity, "display_name", "unknown")

        # Default policy IDs
        policy_ids = policy_ids or []

        event = AuditEvent(
            identity_label=identity_label,
            requested_permission_name=requested_permission_name,
            system_state=system_state_value,
            decision=decision_value,
            policy_ids=policy_ids,
            reason=reason,
        )

        return decision, event
