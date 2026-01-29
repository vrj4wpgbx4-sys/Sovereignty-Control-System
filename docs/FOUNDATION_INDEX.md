# FOUNDATION INDEX  
## Sovereignty Control System

This document defines the **canonical foundation** of the Sovereignty Control System.

All implementation, documentation, execution paths, and future extensions **must conform** to the principles, constraints, and structures defined here.

This index exists to prevent:
- Conceptual drift
- Authority ambiguity
- Uncontrolled scope expansion
- Post-hoc reinterpretation

Anything not anchored in this index is **non-canonical by definition**.

---

## 1. Canonical Foundation Documents

The following documents collectively define the system’s **meaning, behavior, and limits**.

They are authoritative by design and must be interpreted together.

---

### 1.1 Identity & Authority Model  
**File:** `IDENTITY_AUTHORITY_MODEL.md`

Defines:
- Core system entities (Identity, Credential, Role, Permission, Policy)
- Explicit boundaries of each entity
- Canonical vocabulary used throughout the system

This document defines **what exists**.

---

### 1.2 Authority Resolution & State Model  
**File:** `AUTHORITY_RESOLUTION_AND_STATE_MODEL.md`

Defines:
- The deterministic authority evaluation sequence
- How system state participates in decisions
- Allowed decision outcomes
- Failure, ambiguity, and fail-closed behavior

This document defines **how decisions are made**.

---

### 1.3 Governance & Accountability Framework  
**Directory:** `docs/governance/`

Defines:
- Policy lifecycle and versioning
- Accountability guarantees
- Review and audit expectations
- Evidence required for external evaluation

These documents define **how authority is governed, reviewed, and defended**.

---

### 1.4 Enforcement Model  
**File:** `docs/ENFORCEMENT_MODEL.md`

Defines:
- The boundary between decision and action
- Enforcement preconditions and guarantees
- Dispatcher, effector, and logging separation
- Explicit non-goals and prohibitions

This document defines **how authorized decisions may produce effects**.

---

### 1.5 Technical Appendix  
**File:** `TECHNICAL_APPENDIX.md`

Defines:
- Architectural layering
- Execution philosophy
- Security posture
- Design constraints and non-goals

This document defines **how the system is built without constraining implementation detail**.

---

### 1.6 Foundational Whitepaper  
**File:** `FOUNDATIONAL_WHITEPAPER.md`

Defines:
- Philosophical basis of the system
- Failure modes of authority under stress
- Long-term durability objectives
- Why explicit, auditable authority matters

This document defines **why the system must exist**.

---

### 1.7 Acquisition Memorandum  
**File:** `ACQUISITION_MEMO.md`

Defines:
- Strategic and commercial value
- Differentiation from adjacent solutions
- Integration and expansion considerations
- Risk framing and defensibility

This document defines **why the system is valuable as an asset**.

---

### 1.8 Versioning Philosophy  
**File:** `docs/VERSIONING_PHILOSOPHY.md`

Defines:
- How versions and releases should be interpreted
- Why certain internal phases are intentionally unlisted
- Criteria for release-worthy milestones

This document defines **how to correctly read the release history**.

---

## 2. Authority Precedence

In the event of conflict, ambiguity, or interpretation disputes, documents are applied in the following order:

1. Authority Resolution & State Model  
2. Identity & Authority Model  
3. Governance & Accountability Framework  
4. Enforcement Model  
5. Technical Appendix  
6. Foundational Whitepaper  
7. Acquisition Memorandum  

All code, tests, diagrams, tooling, and presentations **must conform** to this hierarchy.

---

## 3. Change Control

Changes to canonical foundation documents require:

- Explicit intent
- Clear rationale
- A committed change
- Association with a tagged release where appropriate

Canonical documents **must not be edited casually**.

Any material change to:
- Authority
- Governance
- Enforcement boundaries
- Accountability guarantees

**requires a new release**.

---

## 4. Relationship to Releases

Formal system milestones are recorded in `RELEASES.md`.

Each tagged release represents a **locked governance state** that aligns with this foundation index.

Reviewers must evaluate the system against:
- The latest tagged release
- The canonical documents listed here

---

## 5. Reviewer Entry Guidance

Reviewers should proceed in the following order:

1. This document (`FOUNDATION_INDEX.md`)
2. `RELEASES.md`
3. Governance framework (`docs/governance/`)
4. CLI execution paths
5. Audit and enforcement artifacts

This ordering is intentional and enforced.

---

## Boundary Statement

This index is **not a roadmap**.  
It is **not aspirational**.  
It is a **boundary**.

Anything not explicitly anchored here is non-canonical, non-authoritative, and non-binding.
