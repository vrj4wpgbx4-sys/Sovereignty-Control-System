# Sovereignty Control System – Releases

This document records the **formal release history and release semantics** of the Sovereignty Control System.

Releases in this repository are **governance milestones**, not feature drops or experimental snapshots.  
Each release represents a **locked, reviewable state** of the system’s authority model, documentation, and audit behavior.

---

## Release Semantics

A release is created only when:

- Governance behavior is deterministic
- Authority rules are explicit and documented
- Accountability artifacts are present
- System behavior can be reviewed without privileged access

Releases are intended for:
- Grant reviewers
- Independent auditors
- Institutional governance evaluators

---

## Branches vs. Tags

### Branches

- **`main`**
  - Canonical, reviewable line of development
  - Always expected to be in a clean, working, review-ready state
  - New work is merged into `main` only when it is conceptually complete and documented

- **Feature or integration branches** (e.g., `integration-v0.2`)
  - Temporary or transitional
  - Used for development and integration work
  - Not considered governance milestones
  - May be deleted after merge

### Tags

Tags represent **locked governance milestones**.

Once created, a tag:

- Must not be moved
- Must not be deleted
- Serves as an immutable reference point for reviewers and auditors

Tags are named using a version identifier and a short descriptor of the milestone (for example, `v0.3-foundation-complete`).

---

## Tagged Release History

### v0.4-policy-lifecycle (Current)

**Status:** Stable  
**Purpose:** Formal governance enforcement

This release introduces explicit policy lifecycle controls and static validation. Policies are no longer implicit configuration; they are treated as **governed system artifacts**.

**Key characteristics:**
- Explicit policy outcomes (`ALLOW`, `DENY`, `REQUIRE_ADDITIONAL_APPROVAL`)
- Policy versioning and lifecycle documentation
- Static policy validation via CLI
- Append-only policy change log
- Reviewer-grade governance documentation

This release is intended for **formal external review**.

---

### v0.3-foundation-complete

**Status:** Stable  
**Purpose:** Locked governance foundation

This release establishes the core governance engine, deterministic decision evaluation, and audit emission. It marks the point at which governance behavior became **observable and reproducible**.

**Key characteristics:**
- Deterministic authority engine
- Append-only audit logging
- CLI-based scenario execution
- Stable documentation structure

---

### v0.2 Series – Integration and Accountability

- **`v0.2-governance-accountability`**  
  Introduced early accountability documentation and framing.

- **`v0.2-governance-complete`**  
  Consolidated governance behavior for early review.

- **`v0.2-integration-cli`**  
  Added command-line integration and executable scenarios.

These releases represent the transition from conceptual governance to executable demonstration.

---

### v0.1-governance-core

**Status:** Archived (Foundational)

Initial implementation of the authority engine and audit model. This release established the conceptual and structural basis for all later governance enforcement.

---

## How Reviewers Should Use This Document

1. Start with the **latest tagged release** (currently `v0.4-policy-lifecycle`)
2. Check out that tag locally:
   ```bash
   git fetch --tags
   git checkout v0.4-policy-lifecycle
