# v1.0 Log Integrity Design — Sovereignty Control System

## Purpose

This document specifies the **log integrity mechanism** for v1.0 of the Sovereignty Control System.

The objective is to ensure that governance and enforcement logs can be **cryptographically verified after the fact**, such that any modification, deletion, or reordering of entries is detectable, without introducing external dependencies or altering execution semantics.

This document is **normative for v1.0 design** and **implementation-guiding**, but does not itself introduce code.

---

## Design Goals (Non-Negotiable)

The integrity model MUST:

- Preserve append-only JSONL logs
- Be local-first and offline-verifiable
- Introduce no implicit authority or autonomy
- Be deterministic and reproducible
- Remain human-readable
- Be explainable to non-cryptographers in review contexts

If a proposal violates any of the above, it is rejected.

---

## Selected Integrity Model

### Hash-Chained Log Entries (Canonical v1.0 Model)

Each log entry cryptographically commits to the previous entry via a hash pointer, forming an immutable chain.

This applies independently to:

- `data/audit_log.jsonl`
- `data/enforcement_log.jsonl`

The two logs remain **separate chains**.

---

## Hash Algorithm

### Algorithm: **SHA-256**

Rationale:

- Widely standardized and understood
- Stable across platforms
- Sufficient security margin for audit integrity
- Readily available in standard libraries
- Reviewer-familiar

No alternative algorithms are supported in v1.0.

---

## Canonical Entry Structure (Conceptual)

Each log entry includes **two integrity fields**:

```json
{
  "timestamp": "...",
  "kind": "...",
  "payload": {...},

  "prev_hash": "hex-encoded SHA-256 hash or null",
  "entry_hash": "hex-encoded SHA-256 hash"
}
