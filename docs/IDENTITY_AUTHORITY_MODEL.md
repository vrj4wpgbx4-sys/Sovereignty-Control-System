# Identity and Authority Model

This document defines the initial conceptual model for identity, credentials, roles, permissions, and policies in the Sovereignty Control System. The goal is to describe, in a clear and auditable way, who is allowed to do what, and under which conditions.

---

## 1. Design Goals

- Separate **who someone is** from **what they can do**.
- Make all authority **explicit, traceable, and revocable**.
- Support **normal**, **elevated risk**, **crisis**, and **incapacitation** states.
- Allow **delegation** and **succession** without losing control.
- Be simple enough to implement in a first prototype, but structured enough to extend later.

---

## 2. Core Concepts

### 2.1 Identity

An **Identity** is any person or entity the system recognizes.

Examples:
- A human user (e.g., owner, family member, advisor)
- A legal entity (e.g., LLC, trust, foundation)
- A system component (e.g., automated agent or service)

Each Identity has:
- A unique identifier
- One or more public keys (for signing and encryption)
- A set of associated credentials
- A status: active, suspended, or revoked

In later stages, these identifiers will be mapped to decentralized identifiers (DIDs).

---

### 2.2 Credential

A **Credential** is a verifiable claim about an Identity, issued by some authority.

Examples:
- “This person is the Sovereign Owner.”
- “This individual is a designated Family Guardian.”
- “This account is an authorized Trust Advisor.”

Each Credential includes:
- **Issuer** – who issued the claim
- **Subject** – which Identity the claim is about
- **Claim** – the content of the assertion
- **Validity period** – from/until timestamps
- **Status** – valid, revoked, or expired

In later stages, credentials may be implemented as verifiable credentials according to open standards.

---

### 2.3 Role

A **Role** represents a position or function within the system with defined responsibilities.

Examples:
- `SOVEREIGN_OWNER`
- `FAMILY_GUARDIAN`
- `TRUST_ADVISOR`
- `TECHNICAL_ADMIN`
- `VIEW_ONLY_AUDITOR`

Each Role:
- Specifies what types of **credentials** are required to hold it.
- Is linked to a set of **permissions**.
- May be restricted by **scope** (e.g., which assets or which entities it applies to).

Identities are assigned to Roles. Roles carry authority; individual identities do not hard-code permissions directly.

---

### 2.4 Permission

A **Permission** is the smallest unit of authority, describing a single allowed action.

Examples:
- `VIEW_ASSET_SUMMARY`
- `EXECUTE_TRANSFER`
- `AUTHORIZE_EMERGENCY_LOCKDOWN`
- `MANAGE_IDENTITIES`
- `CONFIGURE_POLICIES`

Each Permission includes:
- A unique name
- A domain (identity, assets, configuration, etc.)
- An action type (view, create, update, delete, execute)
- An optional scope (which assets, which identities, which jurisdictions)

Roles are defined as groups of permissions.

---

### 2.5 Policy

A **Policy** determines when and how permissions can actually be used.

A Policy answers the question:

> Under what conditions does Identity X, in Role Y, with Credentials Z, get to use Permission P?

Examples:
- Under normal operation, a `TRUST_ADVISOR` may `VIEW_ASSET_SUMMARY` for designated entities.
- In a crisis state, a `FAMILY_GUARDIAN` may `AUTHORIZE_EMERGENCY_LOCKDOWN` only if:
  - The Sovereign Owner is marked incapacitated, or
  - The system state is `CRISIS` and
  - At least two guardians approve within a defined time window.

Policies may reference:
- Roles
- Permissions
- System state
- Time-based conditions
- Multi-party thresholds (e.g., multi-signature approvals)

Policies are the place where risk tolerance and governance principles are encoded.

---

## 3. System States

The system operates under explicit **states** that affect how policies are interpreted:

- `NORMAL` – standard operations.
- `ELEVATED_RISK` – warnings or suspicious activity; additional checks may apply.
- `CRISIS` – confirmed incident; certain actions are frozen, others are allowed with stricter thresholds.
- `INCAPACITATION` – the primary Sovereign Owner is unable to act.
- `SUCCESSION` – permanent transfer of control to a new Sovereign Owner.

Policies define:
- Which roles are active or limited in each state.
- Which permissions are temporarily blocked or enabled.
- What events or actions can cause a transition between states.

---

## 4. Initial Roles and Permissions (Draft)

This section will be expanded as requirements become clearer. Initial examples:

- `SOVEREIGN_OWNER`
  - Can view all data.
  - Can grant or revoke roles.
  - Can define or change policies.

- `FAMILY_GUARDIAN`
  - Can view family-relevant summaries.
  - Can participate in emergency actions when required by policy.

- `TRUST_ADVISOR`
  - Can view designated entity and asset information.
  - Cannot change system configuration or policies.

- `VIEW_ONLY_AUDITOR`
  - Can view reports and logs as allowed by scope.
  - Cannot make any state-changing actions.

---

## 5. Next Steps

- Formalize the exact list of Roles and Permissions for the first prototype.
- Define a minimal set of Policies to support:
  - Normal operation
  - A simple emergency scenario
- Map these conceptual models to Python data structures for the initial implementation.

This document will be revised as the implementation evolves.
