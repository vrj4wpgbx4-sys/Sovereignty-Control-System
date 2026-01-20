# Foundation Index
## Digital Sovereignty & Asset Control System

This document defines the canonical foundation of the Digital Sovereignty & Asset Control System.

All implementation, documentation, and future extensions must conform to the principles and structures defined in the documents listed below.

This index exists to prevent drift, ambiguity, and uncontrolled scope expansion.

---

## 1. Canonical Foundation Documents

The following documents collectively define the system’s meaning, behavior, and constraints.

They are authoritative by design.

### 1.1 Identity & Authority Model
**File:** `IDENTITY_AUTHORITY_MODEL.md`

Defines:
- Core system objects (Identity, Credential, Role, Permission, Policy)
- The meaning and boundaries of each object
- The vocabulary used throughout the system

This document defines **what exists**.

---

### 1.2 Authority Resolution & State Model
**File:** `AUTHORITY_RESOLUTION_AND_STATE_MODEL.md`

Defines:
- The step-by-step authority resolution process
- The role of system state in decision-making
- Allowed outcomes of authority evaluation
- Failure and ambiguity handling

This document defines **how decisions are made**.

---

### 1.3 Technical Appendix
**File:** `TECHNICAL_APPENDIX.md`

Defines:
- Architectural positioning
- Execution philosophy
- System layering
- Security posture
- Design constraints and non-goals

This document defines **how the system is built without locking implementation**.

---

### 1.4 Foundational Whitepaper
**File:** `FOUNDATIONAL_WHITEPAPER.md`

Defines:
- The philosophical basis of the system
- The problem of control failure under stress
- Long-term vision and durability
- Why authority must be explicit and auditable

This document defines **why the system should exist**.

---

### 1.5 Acquisition Memorandum
**File:** `ACQUISITION_MEMO.md`

Defines:
- Strategic value to potential acquirers
- Differentiation from adjacent solutions
- Integration and expansion considerations
- Risk framing and defensibility

This document defines **why the system is valuable as an asset**.

---

## 2. Authority Hierarchy

In the event of conflict or ambiguity, documents are interpreted in the following order of precedence:

1. Authority Resolution & State Model  
2. Identity & Authority Model  
3. Technical Appendix  
4. Foundational Whitepaper  
5. Acquisition Memorandum  

Code, diagrams, and presentations must conform to these documents.

---

## 3. Change Control

Changes to canonical foundation documents require:

- Explicit intent
- Clear rationale
- A commit
