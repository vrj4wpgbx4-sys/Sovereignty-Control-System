# v1.0 Policy Versioning Design — Sovereignty Control System

## Purpose

This document defines **policy versioning** for v1.0 of the Sovereignty Control System.

The goal is to ensure that every governance decision can be tied **after the fact** to a specific, declared snapshot of the policies that were in force when the decision was made.

This allows reviewers to answer a critical question:

> “Which policy version did the system claim to be following at the time of this decision?”

This design focuses on **decision provenance**, not policy authoring workflows or formal verification.

---

## Design Goals (Non-Negotiable)

Policy versioning in v1.0 MUST:

- Bind each decision to an explicit policy snapshot
- Be recorded directly in the audit log
- Be integrity-protected by existing hash chaining
- Be deterministic and offline-verifiable
- Avoid implicit or inferred “latest policy” behavior
- Remain simple enough for non-specialist reviewers

Any design that violates these goals is rejected.

---

## Scope

### In Scope

- Governance policies used by the decision engine
- Decision records written to `data/audit_log.jsonl`
- Minimal fields required to bind decisions to policy versions

### Out of Scope (v1.0)

- Policy authoring tools
- Formal policy languages
- Automated policy validation or proofs
- External registries, signatures, or notarization
- Distributed consensus on policy state

These may be introduced in later versions.

---

## Policy Version Identifier

### Definition

Each coherent set of policies is identified by a single, explicit string:

```text
policy_version_id
