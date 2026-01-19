"""
Core domain models for the Sovereignty Control System.

These classes are intentionally simple "skeletons" that mirror the
conceptual model described in docs/IDENTITY_AUTHORITY_MODEL.md.

They define structure and types, but very little behavior for now.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Set


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IdentityStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class CredentialStatus(Enum):
    VALID = "valid"
    REVOKED = "revoked"
    EXPIRED = "expired"


class PermissionAction(Enum):
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


class PermissionDomain(Enum):
    IDENTITY = "identity"
    ASSETS = "assets"
    CONFIGURATION = "configuration"
    POLICIES = "policies"
    SYSTEM = "system"


class SystemState(Enum):
    NORMAL = "normal"
    ELEVATED_RISK = "elevated_risk"
    CRISIS = "crisis"
    INCAPACITATION = "incapacitation"
    SUCCESSION = "succession"


# ---------------------------------------------------------------------------
# Core Concepts
# ---------------------------------------------------------------------------

@dataclass
class Permission:
    """
    Smallest unit of authority: describes a single allowed action.
    """

    name: str
    domain: PermissionDomain
    action: PermissionAction
    scope: Optional[str] = None  # e.g. "family_assets", "entity:XYZ"

    def __str__(self) -> str:
        return f"{self.domain.value}:{self.action.value}:{self.name}"


@dataclass
class Role:
    """
    A named bundle of responsibilities.

    Identities are assigned to Roles. Roles carry permissions.
    """

    name: str  # e.g. "SOVEREIGN_OWNER", "FAMILY_GUARDIAN"
    description: str = ""
    required_credential_types: Set[str] = field(default_factory=set)
    permissions: Set[Permission] = field(default_factory=set)

    def add_permission(self, permission: Permission) -> None:
        self.permissions.add(permission)

    def has_permission(self, permission_name: str) -> bool:
        return any(p.name == permission_name for p in self.permissions)


@dataclass
class Credential:
    """
    A verifiable claim about an Identity, issued by some authority.
    """

    id: str  # internal id for this credential
    issuer_id: str  # identity id of issuer
    subject_id: str  # identity id of subject
    claim_type: str  # e.g. "SOVEREIGN_OWNER", "FAMILY_GUARDIAN"
    claim_value: str  # free-form description or code
    issued_at: datetime
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: CredentialStatus = CredentialStatus.VALID

    def is_currently_valid(self, at_time: Optional[datetime] = None) -> bool:
        """
        Basic validity check based on time and status.
        More advanced logic can be added later.
        """
        if self.status is not CredentialStatus.VALID:
            return False

        now = at_time or datetime.utcnow()

        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False

        return True


@dataclass
class Identity:
    """
    A person, entity, or system component recognized by the system.
    """

    id: str  # unique identifier (later could be a DID)
    display_name: str
    public_keys: List[str] = field(default_factory=list)
    status: IdentityStatus = IdentityStatus.ACTIVE
    credentials: List[Credential] = field(default_factory=list)
    role_names: Set[str] = field(default_factory=set)  # names of Roles

    def is_active(self) -> bool:
        return self.status is IdentityStatus.ACTIVE

    def add_credential(self, credential: Credential) -> None:
        self.credentials.append(credential)

    def assign_role(self, role_name: str) -> None:
        self.role_names.add(role_name)


@dataclass
class PolicyCondition:
    """
    A small helper structure for conditions inside a Policy.

    This is intentionally simple. Later you might expand it to support
    more complex logical rules or a dedicated policy language.
    """

    required_system_state: Optional[SystemState] = None
    minimum_approvals: int = 1  # for multi-party / multi-signature scenarios
    time_window_seconds: Optional[int] = None  # e.g. approvals within 24h


@dataclass
class Policy:
    """
    A rule that determines when a permission may be used.

    Policies connect:
    - roles
    - permissions
    - optional conditions (system state, thresholds, etc.)
    """

    id: str
    name: str
    description: str = ""
    applicable_role_names: Set[str] = field(default_factory=set)
    permission_names: Set[str] = field(default_factory=set)
    condition: PolicyCondition = field(default_factory=PolicyCondition)

    def applies_to_role(self, role_name: str) -> bool:
        return role_name in self.applicable_role_names

    def allows_permission(self, permission_name: str) -> bool:
        return permission_name in self.permission_names
