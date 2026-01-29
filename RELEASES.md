# Sovereignty Control System — Releases

This document records the **formal release history and release semantics** of the Sovereignty Control System.

Releases in this repository are **governance milestones**, not feature drops or experimental snapshots.  
Each release represents a **locked, reviewable state** of authority, delegation, enforcement boundaries, audit guarantees, and documentation.

---

## Release Semantics

A release is created only when **all** of the following are true:

- Governance behavior is deterministic
- Authority rules are explicit and documented
- Decision outcomes are audit-instrumented
- Enforcement boundaries are clearly defined
- System behavior can be reviewed without privileged access

Releases are intended for:

- Grant reviewers
- Independent auditors
- Institutional governance evaluators
- Strategic partners assessing trust and control boundaries

---

## Branches vs. Tags

### Branches

- **`main`**
  - Canonical development branch
  - Always expected to be clean, executable, and documented
  - New work lands here only when conceptually complete

- **Feature / integration branches**
  - Temporary and non-authoritative
  - Used for isolated development
  - Not governance milestones
  - May be deleted after merge

---

### Tags

Tags represent **immutable governance milestones**.

Once created, a tag:

- Must not be moved
- Must not be deleted
- Serves as a fixed reference for external review

Tags follow the pattern:


---

## v0.8-delegation-enforcement

**Status:** Complete  
**Tag:** `v0.8-delegation-enforcement`

### Summary

Introduces **delegation-aware decision enforcement**.

Delegation transitions from informational context to **policy-satisfying authority input**, while preserving determinism, auditability, and fail-closed behavior.

This release marks the system’s transition from *delegation visibility* to *delegation-aware execution*.

---

### What Changed in v0.8

- **Delegation-Aware Authority Evaluation**
  - The authority engine resolves applicable delegations during evaluation
  - Policies may explicitly require valid delegation to allow an action
  - Delegation never bypasses policy; it only satisfies policy-defined conditions

- **Delegation Constraints**
  - Delegations are scoped by:
    - principal
    - delegate
    - action
    - system state
    - policy ID(s)
    - validity window
  - Missing, expired, or mismatched delegations are ignored

- **Principal / Delegate Accountability**
  - Decisions influenced by delegation explicitly record:
    - principal identity
    - delegate identity
    - delegation ID(s)
  - Accountability remains anchored to the principal authority

- **Audit Model Extensions**
  - Audit events include delegation context only when applicable
  - All decisions remain traceable to:
    - policy
    - decision
    - delegation (if used)

- **Execution Model Formalization**
  - `docs/V08_EXECUTION_MODEL.md` defines:
    - evaluation order
    - delegation resolution
    - enforcement eligibility
    - fail-closed behavior

---

### What Did *Not* Change

- No implicit or automatic delegation
- No delegation creation or revocation CLI
- No re-delegation (multi-hop authority)
- No privilege escalation paths
- No silent or background enforcement
- No new decision outcomes beyond:
  - `ALLOW`
  - `DENY`
  - `REQUIRE_ADDITIONAL_APPROVAL`

Delegation remains **explicit, narrow, and auditable**.

---

### Governance Guarantees Preserved

- **Fail-Closed by Default**  
  Invalid or ambiguous delegations are treated as nonexistent.

- **Deterministic Outcomes**  
  Identical inputs always produce identical results.

- **Policy Supremacy**  
  Policies remain the sole source of authority.

- **Oversight Visibility**  
  Delegation influence is observable without granting execution power.

---

## v0.7-delegation-visibility

**Status:** Complete  
**Tag:** `v0.7-delegation-visibility`

### Summary

Introduces **read-only delegation visibility**.

Delegations can be recorded, inspected, and correlated with decisions, without affecting enforcement behavior.

### Key Characteristics

- Append-only delegation registry (`data/delegations.jsonl`)
- Delegation resolution logic
- Read-only decision inspection with delegation context
- No enforcement impact

---

## v0.6-decision-visibility

**Status:** Stable  
**Tag:** `v0.6-decision-visibility`

### Summary

Introduces **read-only decision visibility**.

Governance outcomes become independently reviewable without execution authority.

### Key Characteristics

- Deterministic decision replay
- Immutable audit trail visibility
- Explicit denial visibility in non-crisis states

This release formalizes the separation between:
- decision-making,
- enforcement,
- oversight.

---

## v0.4-policy-lifecycle

**Status:** Stable  
**Tag:** `v0.4-policy-lifecycle`

### Summary

Introduces **formal policy lifecycle governance**.

Policies become versioned, validated, first-class artifacts.

### Key Characteristics

- Explicit policy outcomes
- Static policy validation
- Append-only policy change log
- Reviewer-grade documentation

---

## v0.3-foundation-complete

**Status:** Stable  
**Tag:** `v0.3-foundation-complete`

### Summary

Locks the core governance foundation.

### Key Characteristics

- Deterministic authority engine
- Append-only audit logging
- Executable governance scenarios
- Stable documentation structure

---

## v0.2 Series — Integration and Accountability

- `v0.2-governance-accountability`
- `v0.2-governance-complete`
- `v0.2-integration-cli`

These releases mark the transition from conceptual governance to executable demonstration.

---

## v0.1-governance-core

**Status:** Archived (Foundational)

Initial implementation of the authority engine and audit model.

---

## Reviewer Usage Guidance

1. Identify the **latest tagged release**
2. Check out the tag:
   ```bash
   git fetch --tags
   git checkout <tag>
