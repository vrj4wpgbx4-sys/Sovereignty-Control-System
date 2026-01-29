# v0.9 Planning — Sovereignty Control System

## Purpose

This document defines the **intent, scope, and guardrails** for the v0.9 release.

v0.8 established a complete, delegation-aware governance spine:
- Deterministic authority decisions
- Explicit delegation handling
- Immutable audit logging
- Executable, reviewer-safe CLI scenarios

v0.9 builds on that spine by introducing **controlled enforcement hooks** capable of producing **local, auditable effects**, without weakening or bypassing any existing governance guarantees.

This release is **evolution**, not repair.

---

## Release Objective

> **Introduce explicit, dispatcher-mediated local enforcement that can be invoked from the governance CLI, while preserving all v0.8 governance guarantees.**

Concretely, v0.9 exists to:

- Allow authorized decisions to trigger **explicit enforcement actions**
- Keep enforcement **subordinate to** and **separate from** decision logic
- Produce a **distinct enforcement audit trail**
- Remain **local-only**, deterministic, and reviewer-safe

If v0.8 is the **governance spine**, v0.9 introduces the first **controlled muscles**—capable of action, but incapable of independent intent.

---

## Scope (What v0.9 Will Deliver)

### 1. Enforcement Dispatcher Integration

Integrate the existing `EnforcementDispatcher` into the governance execution path.

The dispatcher is invoked **only** when all of the following are true:
- A decision has been fully evaluated
- The decision outcome permits enforcement (typically `ALLOW`)
- Enforcement has been **explicitly requested** by the caller (e.g., CLI flag)

Constraints:

- The dispatcher performs **no decision evaluation**
- The dispatcher performs **no delegation resolution**
- The dispatcher performs **no logging**
- All dispatcher inputs are explicit, validated, and serializable

The dispatcher is strictly a **routing mechanism**, not an authority-bearing component.

---

### 2. Lockdown State Effector (Operationalized)

Use the existing `LockdownStateEffector` as the **first concrete effector**.

- Action type: `lockdown_state`
- Supported operations:
  - `SET`
  - `CLEAR`
  - `TOGGLE`
- State file: `data/lockdown_state.json`

Behavioral guarantees:

- Local-only; no external side effects
- Fully dry-run aware
- Returns structured `EffectorResult` objects
- Never throws unhandled exceptions

Failure semantics:

- All failures are reported as structured `FAILED` results
- No direct logging occurs inside the effector
- No effector failure retroactively modifies a governance decision

---

### 3. Enforcement Logger

Integrate the existing `enforcement_logger` into the standard execution path.

- Log file: `data/enforcement_log.jsonl`
- Format: append-only JSON Lines

Each enforcement record includes:
- Timestamp
- Kind: `"enforcement_event"`
- `EnforcementResult.to_dict()` payload
- Optional execution metadata (CLI tool name, version, dry-run flag)

Constraints:

- Enforcement logging is **physically and conceptually separate** from decision auditing
- No decision records are written to the enforcement log
- Logging failures **never alter** the decision outcome

---

### 4. Governance CLI — Enforcement Path

Extend the governance CLI to support **explicit enforcement execution**.

High-level behavior:

- Preserve a **decision-only** execution path (v0.8 behavior)
- Introduce an **opt-in enforcement path**, for example:
  - `--enforce` flag, or
  - `enforce` execution mode

Execution semantics:

**Decision-only (default):**
- Evaluate decision
- Write decision to audit log
- Exit

**Decision + enforcement (opt-in):**
- Evaluate decision
- Write decision to audit log
- If outcome permits enforcement:
  - Construct an `EnforcementRequest`
  - Dispatch via `EnforcementDispatcher`
  - Log the resulting `EnforcementResult`
- Render a clear, human-readable CLI summary

CLI requirements:

- Decision outcome, enforcement attempt, and enforcement result must be clearly distinguished
- Dry-run enforcement must be supported and explicitly indicated

---

### 5. Documentation Updates

v0.9 requires aligned documentation updates:

- `docs/ENFORCEMENT_MODEL.md`
  - Remains the canonical description of:
    - Dispatcher responsibilities
    - Effector constraints
    - Enforcement logging
    - Explicit non-goals

- `RELEASES.md`
  - Add a **v0.9 (planned)** entry during development
  - Promote to a full release entry only upon tagging

- CLI usage documentation
  - Minimal, worked examples showing:
    - Decision-only execution
    - Decision + enforcement
    - Dry-run enforcement

---

## Non-Goals (Explicitly Out of Scope for v0.9)

v0.9 will **not**:

- Introduce external integrations (email, SMS, HTTP, webhooks, etc.)
- Add autonomous, scheduled, or background enforcement
- Modify authority resolution or delegation semantics
- Permit policy mutation via enforcement
- Introduce new decision outcomes beyond:
  - `ALLOW`
  - `DENY`
  - `REQUIRE_ADDITIONAL_APPROVAL`
- Collapse decision, enforcement, and logging into a single component

Any of the above require a **future release** and explicit design.

---

## Risks & Guardrails

### Identified Risks

- Enforcement invoked in ambiguous decision states
- Blurring of decision vs. enforcement audit boundaries
- Silent effector failures

### Guardrails

- Enforcement is **explicitly opt-in**
- Dispatcher contains **no authority logic**
- All effector execution is exception-safe and structured
- Decision and enforcement logs are **separate artifacts**
- v0.8 behavior is preserved when enforcement is not requested

---

## Pre-Tag Checklist for v0.9

v0.9 may only be tagged when all of the following are satisfied:

### Behavioral
- Decision-only CLI behavior matches v0.8 exactly
- Enforcement path:
  - Dispatches deterministically
  - Produces `data/enforcement_log.jsonl`
  - Never alters decision outcomes on enforcement failure

### Documentation
- `FOUNDATION_INDEX.md` references `ENFORCEMENT_MODEL.md` as canonical
- `RELEASES.md` updated on tag
- CLI usage includes at least one end-to-end scenario

### Auditability
- At least one scenario demonstrates:
  - Decision entry in `data/audit_log.jsonl`
  - Corresponding enforcement entry in `data/enforcement_log.jsonl`
- Cold review confirms the separation is obvious and defensible

### Tagging
- Tag name: `v0.9-enforcement-hooks`
- Tag message emphasizes:
  - Dispatcher integration
  - Local-only effectors
  - Separate enforcement logging

---

## Version Boundary Statement

v0.9 is the first release in which **authorized decisions may trigger local, structured enforcement via a dispatcher**, while leaving all v0.8 governance guarantees intact.

Any change that weakens those guarantees **does not belong in v0.9**.
