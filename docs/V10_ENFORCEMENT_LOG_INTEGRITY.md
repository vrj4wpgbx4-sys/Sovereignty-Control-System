# v1.0 Enforcement Log Integrity — Sovereignty Control System

## Purpose

This document specifies the **log integrity mechanism for enforcement actions** in v1.0 of the Sovereignty Control System.

While audit logs capture **governance decisions**, enforcement logs capture **what the system actually did** in response to those decisions.

The objective is to ensure that enforcement actions are:

- Tamper-detectable after the fact
- Auditable by offline reviewers
- Deterministically verifiable
- Clearly separated from governance decision records

This document is **normative for v1.0 enforcement integrity design** and **implementation-guiding**, but does not itself introduce code.

---

## Scope

Enforcement actions are recorded in:

- `data/enforcement_log.jsonl`

These entries represent **executed system behavior**, such as:

- Lockdown effectors triggered
- Local enforcement outcomes
- Idempotent no-op results
- Enforcement failures or refusals

For v1.0, enforcement logs MUST provide the same integrity guarantees as audit logs:

- Append-only semantics
- Detectable modification, deletion, or reordering
- Offline verification without external services

---

## Design Goals (Non-Negotiable)

The enforcement integrity model MUST:

- Preserve append-only JSONL logs
- Be local-first and offline-verifiable
- Introduce no implicit authority or autonomy
- Be deterministic and reproducible
- Remain human-readable
- Be explainable to non-cryptographers

If a proposal violates any of the above, it is rejected.

---

## Selected Integrity Model

### Hash-Chained Enforcement Entries (v1.0)

Each enforcement log entry cryptographically commits to the previous enforcement entry via a hash pointer, forming an immutable chain within the enforcement log.

The enforcement log uses the **same hash-chaining model** as the audit log, but maintains a **separate, independent chain**.

---

## Hash Algorithm

### Algorithm: **SHA-256**

Rationale:

- Widely standardized and understood
- Stable across platforms
- Sufficient security margin for integrity guarantees
- Available in standard libraries
- Familiar to reviewers and auditors

No alternative algorithms are supported in v1.0.

---

## Canonical Entry Structure (Conceptual)

Each enforcement log entry includes **two integrity fields**:

```json
{
  "timestamp": "...",
  "enforcement_action": "...",
  "target": "...",
  "result": "...",
  "details": { ... },

  "prev_hash": "hex-encoded SHA-256 hash or null",
  "entry_hash": "hex-encoded SHA-256 hash"
}
