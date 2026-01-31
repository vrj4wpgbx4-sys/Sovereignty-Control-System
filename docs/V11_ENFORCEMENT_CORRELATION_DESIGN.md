\# v1.1 Enforcement Correlation Design — Sovereignty Control System



\## Purpose



This document defines how \*\*governance decisions\*\* (audit log) and

\*\*enforcement outcomes\*\* (enforcement log) can be \*\*correlated after the

fact\*\*, without changing:



\- the v1.0 authority model

\- the v1.0 integrity guarantees

\- the v0.9/v1.0 separation of decision vs. enforcement



The objective is to let reviewers answer:



> “For this decision, what enforcement (if any) was actually attempted,

> and what happened?”



This is a \*\*review-time capability\*\*, not a runtime requirement.



---



\## Design Principles



\- \*\*Read-only first\*\*  

&nbsp; Correlation is for replay and review, not for driving runtime behavior.



\- \*\*No new implicit authority\*\*  

&nbsp; Correlation must not affect governance or enforcement logic.



\- \*\*Log-structure–only changes\*\*  

&nbsp; We enhance \*\*what is logged\*\*, not \*\*how decisions are made\*\*.



\- \*\*Integrity-preserving\*\*  

&nbsp; All new correlation fields must live inside the existing integrity model

&nbsp; (hash-chained entries).



\- \*\*Graceful with legacy data\*\*  

&nbsp; Correlation must handle:

&nbsp; - legacy audit entries (no hashes, no policy\_version\_id)

&nbsp; - legacy enforcement entries (no correlation identifiers)



---



\## Existing Artifacts



\### Audit Log (`data/audit\_log.jsonl`)



Each v1.0 decision entry includes (among others):



\- `timestamp`

\- `identity\_label` / `identity`

\- `requested\_permission\_name` / `requested\_action`

\- `decision` / `decision\_outcome`

\- `policy\_ids`

\- `policy\_version\_id` (v1.0+)

\- `prev\_hash`, `entry\_hash` (v1.0+)



\### Enforcement Log (`data/enforcement\_log.jsonl`)



Each enforcement entry (via `enforcement\_logger`) currently includes:



\- `timestamp`

\- `kind`: `"enforcement\_event"`

\- `payload`: `EnforcementResult.to\_dict()`

&nbsp; - `decision\_reference` (decision-related metadata)

&nbsp; - `context`

&nbsp; - `dry\_run`

&nbsp; - `action\_results` (outcomes, details)

\- `meta`: optional metadata (e.g., `invoked\_by`, `scenario\_path`)



---



\## Correlation Strategy



We adopt a \*\*two-tiered correlation approach\*\*:



1\. \*\*Primary correlation key: `decision\_correlation\_id`\*\*  

&nbsp;  - A stable, opaque identifier that can be:

&nbsp;    - generated once per decision

&nbsp;    - attached to the audit entry

&nbsp;    - propagated into enforcement entries



2\. \*\*Fallback correlation keys (when correlation\_id is absent):\*\*

&nbsp;  - `(timestamp, identity, requested\_action, policy\_version\_id)`

&nbsp;  - Only used for \*\*legacy\*\* or pre-correlation entries.



This preserves a clean, explicit link while remaining compatible with existing logs.



---



\## Correlation Fields



\### 1) `decision\_correlation\_id` (new, optional, recommended)



\- \*\*Type:\*\* string (opaque)

\- \*\*Where used:\*\*

&nbsp; - Audit log entries (decision records)

&nbsp; - Enforcement log `decision\_reference` field

\- \*\*Generation:\*\*

&nbsp; - Created once per non-dry-run decision at the CLI / orchestration layer.

&nbsp; - Can be:

&nbsp;   - a UUID

&nbsp;   - or a deterministic hash of key decision fields

\- \*\*Integrity:\*\*

&nbsp; - Included in the v1.0 hash chain payload for audit entries.

&nbsp; - Included in enforcement log records (which may later gain their own hash chain).



\*\*Rule:\*\*  

If present, `decision\_correlation\_id` is the \*\*authoritative link\*\* between

audit and enforcement.



\### 2) Fallback tuple



When `decision\_correlation\_id` is missing (legacy or transitional entries),

correlation MAY use:



\- `timestamp`

\- `identity\_label` / `identity`

\- `requested\_permission\_name` / `requested\_action`

\- `policy\_version\_id` (if present)



This is \*\*best-effort\*\* and must be clearly labeled as such in any tooling.



---



\## Correlation Semantics



For a given decision (audit entry):



1\. Locate all enforcement entries where:



&nbsp;  - `payload.decision\_reference.decision\_correlation\_id == audit.decision\_correlation\_id`  

&nbsp;    (primary case), or



&nbsp;  - Fallback match on the tuple:

&nbsp;    - timestamps approximately equal (review tool may allow a small tolerance)

&nbsp;    - identity matches

&nbsp;    - requested action matches

&nbsp;    - policy\_version\_id matches (when present)



2\. Present these as:



&nbsp;  - A list of \*\*enforcement attempts\*\* tied to that decision

&nbsp;  - With outcomes:

&nbsp;    - `SUCCESS`

&nbsp;    - `NOOP`

&nbsp;    - `FAILED`

&nbsp;    - `NOT\_IMPLEMENTED`

&nbsp;    - `NOT\_APPLICABLE`



3\. Clearly distinguish:



&nbsp;  - “No enforcement found” vs.

&nbsp;  - “Enforcement definitely did not run” vs.

&nbsp;  - “Logs incomplete; correlation inconclusive”



---



\## Impact on Existing Components



\### Audit Logger



\- \*\*Status (v1.0):\*\* already logs integrity-aware decisions.

\- \*\*v1.1 correlation extension:\*\*

&nbsp; - Optionally accept a `decision\_correlation\_id` field on the decision record.

&nbsp; - Include it in the record before hash-chaining.

&nbsp; - Do \*\*not\*\* generate it internally; it must be provided by caller.



\### Governance CLI (`governance\_cli.py`)



\- Responsible for:

&nbsp; - Generating a `decision\_correlation\_id` for each non-dry-run decision.

&nbsp; - Attaching it to:

&nbsp;   - the decision record (before `log\_decision`)

&nbsp;   - the enforcement `decision\_reference` (if enforcement is invoked)

&nbsp;   - optional `additional\_metadata` for enforcement logging.



\- Must preserve v0.9/v1.0 guarantees:

&nbsp; - No enforcement without a decision

&nbsp; - No implicit behavior beyond correlation metadata



\### Enforcement Logger



\- Extend the `EnforcementResult`-derived payload to ensure

&nbsp; `decision\_reference` includes:



&nbsp; - `decision\_correlation\_id` (if available)

&nbsp; - `timestamp`

&nbsp; - `identity` / `identity\_label`

&nbsp; - `requested\_action` / `requested\_permission\_name`

&nbsp; - `policy\_version\_id` (if available)



This is a \*\*non-breaking extension\*\*: old entries remain valid; new entries

just carry more structured context.



---



\## Tooling: Correlation in v1.1 Replay



The existing v1.1 `decision\_replay` CLI can be extended with a new subcommand:



\### `correlate`



Example:



```bash

python -m src.decision\_replay correlate --index 10



