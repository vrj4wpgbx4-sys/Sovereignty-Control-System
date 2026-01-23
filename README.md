# Sovereignty Control System

This repository contains the core architecture, prototypes, and documentation for a Digital Sovereignty & Asset Control System.

Document governance core (v0.1) in README

## Governance Core (v0.1)

This repository contains a **locked governance core** for a Digital Sovereignty & Asset Control System.

The governance core defines *how authority decisions are made* and *how those decisions are auditable*, independent of any UI, custody system, or execution platform.

The core is versioned and frozen at:

> **Tag:** `v0.1-governance-core`

---

### What This Core Does

At its core, the system answers one question deterministically:

> **“Is this identity allowed to perform this action right now?”**

It does so by evaluating:

- Identity status
- Credentials
- Roles
- Permissions
- Policies
- Explicit system state (e.g., NORMAL, CRISIS)

The output is a clear decision:

- `ALLOW`
- `DENY`
- `REQUIRE_ADDITIONAL_APPROVAL`
- `DEFER`

No action is executed automatically.  
This system governs decisions — it does not perform them.

---

### Auditability by Design

Every authority decision can optionally emit a structured **audit event** that records:

- Who attempted the action
- What permission was requested
- The system state at the time
- The decision outcome
- Relevant policy identifiers
- A timestamp and optional human-readable reason

This creates a durable, reviewable provenance trail suitable for:
- Compliance
- Dispute resolution
- Governance review
- Long-term continuity

---

### What This Core Explicitly Does *Not* Do

The governance core intentionally does **not**:

- Hold or move assets
- Replace legal or custodial systems
- Perform market execution
- Provide a user interface
- Persist data or logs

These concerns are designed to be layered **on top** of the core without altering its behavior.

---

### Why the Core Is Locked

The governance core is frozen at `v0.1-governance-core` to:

- Preserve a known-good authority model
- Prevent accidental scope creep
- Enable future extensions without rewriting fundamentals
- Provide a stable reference for review, grants, or acquisition discussions

All future development should build *around* this core, not change it casually.

---

### Key Files

- `src/authority_engine.py`  
  Deterministic authority resolution logic.

- `src/audit_event.py`  
  Structured audit record for authority decisions.

- `src/test_authority_engine_basic.py`  
  Behavioral tests for authority resolution.

- `src/test_audit_event_basic.py`  
  Smoke test for audit event structure.

---

### Status

The governance core is complete, tested, and versioned.

Further development will focus on:
- Integration layers
- Interfaces
- Persistence
- Policy authoring tools

without modifying the core authority logic.



## Purpose

- Provide individuals, families, and organizations with secure visibility and control over their digital identities and assets.
- Encode authority, permissions, and emergency controls in a verifiable, auditable way.
- Serve as a time-stamped record of design and development to support proof of authorship and ownership.

## Current Status

- Initial planning and architecture
- Language: Python
- Early experiments may be built in cloud IDEs (e.g., Replit) then synced here

