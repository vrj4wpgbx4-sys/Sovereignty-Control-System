
# Sovereignty Control System (SCS)

**Version:** v0.6  
**Status:** Active Development  
**Focus:** Deterministic governance, policy enforcement, and decision visibility

---

## Overview

The **Sovereignty Control System (SCS)** is a governance-first control framework designed to model, enforce, and audit authority-based decisions in high-trust, high-risk systems.

SCS treats governance as executable logic — not documentation — and ensures that **every privileged action is evaluated, enforced, and recorded according to explicit policy**.

The system is intentionally opinionated:
- Authority is defined
- Policies are explicit
- Enforcement is deterministic
- Decisions are immutable
- Oversight is visible

---

## What SCS Does

At its core, SCS evaluates **requested actions** against:
- Identity
- System state
- Authority hierarchy
- Active policies

It then produces one of three outcomes:

- **ALLOW** — action is permitted
- **DENY** — action is prohibited
- **REQUIRE_ADDITIONAL_APPROVAL** — action is gated by governance rules

Every evaluation produces a **decision record** explaining *why* the outcome occurred.

---

## Current Capabilities (v0.6)

### ✅ Governance & Authority
- Explicit authority hierarchy
- Sovereign owner and delegated roles
- Guardian-based escalation rules

### ✅ Policy Engine
- Policy-driven authorization
- State-dependent rules (e.g., NORMAL vs CRISIS)
- Deterministic evaluation (no heuristics)

### ✅ Enforcement Layer
- Central decision gate for sensitive actions
- Action requests cannot bypass evaluation
- Enforcement logic isolated from callers

### ✅ Decision Logging
- Every decision is recorded with:
  - Timestamp
  - Identity
  - Requested action
  - System state
  - Decision outcome
  - Applied policy IDs
  - Human-readable reasoning

### ✅ Decision Visibility (New in v0.6)
- Read-only CLI access to decision history
- No authority required to view past decisions
- Supports governance review, audits, and oversight

Example:
```bash
python src/main.py view-decisions


Sovereignty-Control-System/
├── src/
│   ├── authority_engine.py
│   ├── audit_event.py
│   ├── decision_gate.py
│   ├── main.py
│   ├── view_decisions_cli.py
│   └── enforcement/
│       └── decision_gate.py
│
├── docs/
│   ├── FOUNDATION_INDEX.md
│   ├── VERSIONING_PHILOSOPHY.md
│   └── governance/
│       ├── DECISION_MODEL.md
│       ├── POLICY_LIFECYCLE.md
│       ├── DECISION_HISTORY_MODEL.md
│       └── OVERSIGHT_VISIBILITY.md
│
├── RELEASES.md
└── README.md
