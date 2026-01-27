# DECISION_HISTORY_MODEL

## Purpose

The Decision History Model defines how **governance decisions are recorded, preserved, and inspected**
within the Sovereignty Control System.

It establishes a **read-only, reviewer-safe representation** of system decisions that is intentionally
separate from raw audit logs and internal enforcement mechanics.

This model is introduced in **v0.6**, marking the transition from a system that is merely auditable
to one that is **operationally inspectable**.

---

## Core Principles

### 1. Immutability

- Decision records are **append-only**
- Once written, a decision record **MUST NOT** be modified, overwritten, or deleted
- Historical integrity is non-negotiable

### 2. Separation of Concerns

Decision history is explicitly separate from:

- Audit logs
- Enforcement internals
- Runtime state machines

Decision history exists to explain **what was decided and why**,  
not **how the system executed the decision**.

### 3. Human-Readable First

- Decision records are structured for **human inspection**
- A reviewer MUST be able to understand outcomes **without reading source code**
- Explanations MUST be clear, concise, and outcome-focused

### 4. Read-Only Access

- Decision history is strictly non-mutating
- CLI and programmatic access MUST NOT allow:
  - Edits
  - Overrides
  - Deletions
- Any attempt to mutate history is a system violation

---

## Decision Record Structure

Each decision record MUST include the following fields:

### Required Fields

- **timestamp**
  - ISO-8601 UTC timestamp indicating when the decision was finalized

- **identity**
  - The identity requesting the action  
    (e.g., sovereign owner, guardian, delegate)

- **requested_action**
  - Canonical action identifier evaluated by the authority engine

- **system_state**
  - System state at the time of evaluation  
    (e.g., `NORMAL`, `CRISIS`)

- **decision_outcome**
  - One of:
    - `ALLOW`
    - `DENY`
    - `REQUIRE_ADDITIONAL_APPROVAL`

- **policy_ids**
  - One or more policy identifiers that directly influenced the decision

- **reason**
  - Human-readable explanation describing why the outcome occurred

---

## Storage Model

- Decision history MAY be persisted as:
  - JSONL files
  - Structured database records
- Storage MUST preserve **chronological ordering**
- Storage MUST support **deterministic replay** for review and verification

---

## Access Model

### CLI Access

Decision history is exposed via a **read-only CLI command**.

The command MUST support:

- Chronological listing (newest first by default)
- Optional filtering by:
  - identity
  - decision_outcome
  - system_state
  - policy_id
- Pagination or bounded output for large histories

### Access Guarantees

- No command may alter historical records
- No command may silently suppress records
- Any redaction rules MUST be:
  - Explicit
  - Documented
  - Reviewable

---

## Relationship to Audit Logs

| Decision History | Audit Logs |
|------------------|-----------|
| Human-readable   | Machine-oriented |
| Outcome-focused  | Event-focused |
| Immutable        | Append-only |
| Reviewer-safe    | Internal detail |

Decision history MAY reference audit event identifiers,  
but MUST NOT require audit log access to understand outcomes.

---

## Enforcement Boundary

- Enforcement components MAY emit decision records
- Enforcement components MUST NOT rewrite or reinterpret historical decisions
- Decision history is authoritative for **what the system decided**,  
  not how enforcement executed the outcome

---

## Versioning

- This model is introduced in **v0.6**
- Any schema changes MUST:
  - Be additive
  - Preserve backward readability
  - Be documented in `RELEASES.md`

---

## Reviewer Expectations

A reviewer SHOULD be able to:

- Inspect past decisions
- Understand why outcomes occurred
- Verify policy enforcement consistency
- Do so **without executing code**

If this condition is not met, the implementation is considered incomplete.

---

## Status

**ACTIVE — v0.6**

This document is normative and binding for all decision history implementations
within the Sovereignty Control System.
