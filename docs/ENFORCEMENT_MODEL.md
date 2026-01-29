# Enforcement Model — Sovereignty Control System

## Purpose

The Enforcement Model defines **how governance decisions may produce controlled, auditable effects** within the Sovereignty Control System.

This document enforces a strict separation between:

- **Decision-making** (authority evaluation)
- **Auditability** (decision recording)
- **Enforcement** (execution of effects)

Enforcement is always *downstream* of governance.  
It is never a substitute for authority, policy, or judgment.

---

## Core Guarantee

> **No enforcement action may occur without a prior, recorded governance decision.**

A governance decision is a **mandatory precondition** for enforcement, but it does not guarantee that enforcement will occur or succeed.

Enforcement failures must never retroactively affect the decision record.

---

## Enforcement Preconditions

Enforcement may only be attempted after **all** of the following are true:

1. A request has been evaluated by the Authority Engine
2. A decision outcome has been produced
3. The decision has been written to the audit log
4. Enforcement has been explicitly invoked by the execution layer

Enforcement is never implicit, automatic, or backgrounded.

---

## Decision → Enforcement Relationship

Enforcement behavior is strictly determined by the finalized decision outcome.

| Decision Outcome | Enforcement Behavior |
|------------------|---------------------|
| `ALLOW` | Enforcement actions may be attempted |
| `DENY` | Enforcement must not occur |
| `REQUIRE_ADDITIONAL_APPROVAL` | Enforcement is deferred until conditions are satisfied |

Enforcement must never reinterpret, override, or weaken the decision.

---

## Enforcement Architecture

Enforcement is implemented as a **three-layer system**, with no collapsed responsibilities:

1. **Dispatcher** — routes actions
2. **Effectors** — perform bounded effects
3. **Enforcement Logger** — records outcomes

Each layer is isolated and independently auditable.

---

## Enforcement Dispatcher

The Enforcement Dispatcher is responsible for:

- Receiving an explicit enforcement request
- Routing declared actions to registered effectors
- Capturing structured execution results

The dispatcher **does not**:

- Evaluate authority or policy
- Resolve delegation
- Modify decisions
- Perform logging

It operates only on finalized, auditable decision context.

---

## Effectors

Effectors are isolated units that perform **specific, bounded actions**.

Required effector characteristics:

- Explicitly registered by `action_type`
- Local-only and side-effect constrained
- Dry-run aware
- Free of governance or policy logic
- Deterministic and observable

Effectors must never:

- Make authorization decisions
- Mutate policy
- Trigger other decisions implicitly
- Perform logging directly

Effectors return structured results; they do not persist them.

---

## Enforcement Logging

All enforcement attempts must be logged **separately** from governance decisions.

- Enforcement logs record *what was attempted and what occurred*
- Decision logs record *what was authorized*

Recommended file:

- `data/enforcement_log.jsonl` (append-only, JSON Lines)

Each enforcement log entry includes:

- Timestamp
- Decision reference
- Enforcement context
- Action results
- Dry-run indicator

This separation ensures audit clarity and prevents outcome conflation.

---

## v0.9 Enforcement Scope

v0.9 introduces **local, simulated enforcement only**.

There are:

- No external integrations
- No autonomous execution
- No background enforcement
- No policy mutation

All enforcement is explicitly invoked and fully observable.

---

## Initial Effectors (v0.9)

### Lockdown State Effector

- Action type: `lockdown_state`
- Writes system state to a local file (`data/lockdown_state.json`)
- Supports explicit operations:
  - `SET`
  - `CLEAR`
  - `TOGGLE`
- Fully dry-run aware
- No external effects

This effector represents **controlled state signaling**, not real-world control.

---

### Notification Effector (Planned / Simulated)

- Writes notification events to a local JSONL file
- Represents alerts such as:
  - Lockdown requested
  - Additional approval required
  - Lockdown activated or cleared

This effector simulates integrations without external side effects.

---

## Explicit Non-Goals

The Enforcement Model explicitly forbids:

- Autonomous enforcement
- Implicit execution
- External system control
- Policy mutation
- Hidden side effects

Any future expansion beyond these constraints requires a new version and explicit review.

---

## Enforcement Boundary Statement

Enforcement executes **only what governance has authorized**,  
**only when explicitly invoked**,  
and **only in ways that are observable and auditable**.

This boundary is intentional and non-negotiable.
