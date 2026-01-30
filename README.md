# Sovereignty Control System (SCS)

**Version:** v1.0  
**Status:** Active Development (Integrity & Provenance Established)  
**Focus:** Deterministic governance, explicit enforcement, and cryptographically verifiable decision history

---

## Overview

The **Sovereignty Control System (SCS)** is a governance-first control framework designed to
**evaluate, enforce, and permanently record authority-based decisions** in high-trust,
high-risk systems.

SCS treats governance as **executable logic**, not documentation.

Every privileged action is:

1. **Explicitly evaluated** against policy and authority
2. **Optionally enforced** through controlled effectors
3. **Immutably recorded** in tamper-detectable logs
4. **Auditable offline**, after the fact

The system is intentionally opinionated:

- Authority is explicit
- Policies are declared
- Enforcement is downstream of decisions
- Decisions cannot be silently altered
- Oversight does not require live system access

---

## Core Guarantees

As of v1.0, SCS guarantees that:

- No enforcement occurs without a recorded decision
- Decisions are deterministic and reproducible
- Decision and enforcement trails are cryptographically tamper-detectable
- Policy provenance is recorded and verifiable
- Reviewers can validate system behavior offline

---

## What SCS Does

At its core, SCS evaluates **requested actions** against:

- Identity and authority
- System state (e.g., NORMAL vs CRISIS)
- Explicit governance policies
- Declared policy versions

Each evaluation produces a **decision record** explaining:

- Who requested the action
- What was requested
- Under which conditions
- Which policies applied
- Why the outcome occurred

Possible outcomes:

- **ALLOW**
- **DENY**
- **REQUIRE_ADDITIONAL_APPROVAL**

---

## Current Capabilities (v1.0)

### ✅ Governance & Authority
- Explicit authority hierarchy
- Sovereign owner, delegates, and guardians
- Deterministic evaluation (no heuristics or inference)

### ✅ Policy Engine
- Policy-driven authorization
- State-dependent rules
- Explicit policy identifiers
- Declared **policy_version_id** for provenance

### ✅ Enforcement Layer (v0.9+)
- Enforcement is downstream of decisions
- Dispatcher-mediated execution
- Local-only effectors
- Idempotent safety behavior (e.g., lockdown NOOPs)

### ✅ Audit Logging (v1.0)
- Append-only JSONL audit log
- Hash-chained entries (`prev_hash`, `entry_hash`)
- Offline verification via CLI
- Legacy-safe (hashing begins at v1.0 boundary)

### ✅ Enforcement Logging (v1.0)
- Separate enforcement log
- Hash-chained integrity model
- Clear separation from decision records
- Optional propagation of decision provenance

### ✅ Policy Versioning (v1.0)
- Every non-dry-run decision binds to an explicit `policy_version_id`
- Policy provenance is included in the integrity envelope
- Tampering with policy history is detectable

---

## Verification & Review

SCS is designed to be reviewed **after the fact**.

Reviewers can:

1. Verify audit log integrity:
   ```bash
   python -m src.log_integrity verify --log-path data/audit_log.jsonl
