\# v1.1 Decision Replay \& Explanation CLI — Design



\## Purpose



Provide a \*\*read-only CLI\*\* that allows reviewers to replay and explain past

governance decisions using existing audit logs, without mutating state or

triggering enforcement.



This tool improves \*\*reviewability and accountability\*\* while preserving all

v1.0 integrity guarantees.



---



\## Design Goals (Non-Negotiable)



\- Read-only (no writes, no enforcement)

\- Local-first, offline

\- Deterministic output for the same inputs

\- Human-readable by default

\- Machine-parseable when requested

\- Zero impact on v1.0 execution paths



---



\## Inputs



\- Audit log: `data/audit\_log.jsonl`

\- Optional enforcement log: `data/enforcement\_log.jsonl`

\- Optional filters:

&nbsp; - entry index

&nbsp; - timestamp

&nbsp; - decision\_correlation\_id

&nbsp; - identity

&nbsp; - requested\_action



---



\## Core Capabilities



\### 1) List Decisions



Command:



