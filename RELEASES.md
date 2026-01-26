# Sovereignty Control System – Release Semantics

This document explains how releases are represented in this repository so that governance reviewers, auditors, and contributors can understand what each tag and version boundary means.

Releases are **governance milestones**, not just code snapshots. Each release reflects a coherent, reviewable state of the system’s authority model, documentation, and audit behavior.

---

## Branches vs. Tags

### Branches

- **`main`**
  - Canonical, reviewable line of development.
  - Always expected to be in a clean, working, review-ready state.
  - New work is merged into `main` only when it is conceptually complete and documented.

- **Feature / integration branches** (e.g., `integration-v0.2`)
  - Temporary or transitional branches used for development and integration.
  - Not considered governance milestones.
  - May be deleted after their work is merged into `main`.

### Tags

Tags represent **locked governance milestones**. Once created, a tag:

- Must not be moved to a different commit.
- Must not be deleted.
- Serves as an immutable reference point for reviewers and auditors.

Tags are named using a version and a short descriptor of the milestone (e.g., `v0.3-foundation-complete`).

---

## Current Tagged Milestones

- `v0.1-governance-core`  
  Initial governance engine and authority model.

- `v0.2-governance-accountability`  
  Enhanced accountability features and documentation.

- `v0.2-governance-complete`  
  Consolidated governance behavior for early review.

- `v0.2-integration-cli`  
  Command-line integration and scenario execution.

- `v0.3-foundation-complete`  
  Locked foundation phase with stable documentation and scenarios.

- `v0.4-policy-lifecycle`  
  Introduced explicit policy outcomes, policy lifecycle documentation, and static policy validation via CLI.

Each tag corresponds to a **reviewable state** of the Sovereignty Control System. Reviewers can check out any tag and see the exact code, configuration, and documentation that were present at that milestone.

---

## How to Use Releases as a Reviewer

If you are reviewing the system for a grant, audit, or governance evaluation:

1. Start with the **latest tagged milestone** (currently `v0.4-policy-lifecycle`).
2. Check out that tag locally, for example:

   ```bash
   git fetch --tags
   git checkout v0.4-policy-lifecycle
