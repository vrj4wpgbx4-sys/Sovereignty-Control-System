\# Sovereignty Control System – Decision Model



This document describes how the Sovereignty Control System evaluates requests for privileged actions and produces accountable, transparent decisions. It is intended for reviewers who need to understand \*how\* and \*why\* the system grants, denies, or escalates authority.



The decision model is consistent across all releases and is driven by externally defined governance policies and scenarios.


For a grant- and reviewer-facing explanation of how this decision model supports accountability and transparency, see:

docs/grant_alignment.md

---



\## 1. Overview



Every decision in the system follows the same high-level sequence:



1\. \*\*Input\*\* – An identity requests a specific permission in a given system state.

2\. \*\*Policy Evaluation\*\* – The request is evaluated against governance policies defined in configuration files.

3\. \*\*Decision\*\* – The engine issues one of three outcomes:

&nbsp;  - `ALLOW`

&nbsp;  - `DENY`

&nbsp;  - `REQUIRE\_ADDITIONAL\_APPROVAL`

4\. \*\*Audit Event\*\* – A structured, immutable record is written to the audit log, including the applied policy IDs and justification.

5\. \*\*Explainability\*\* – The CLI presents a human-readable explanation of which policy fired and why.



This architecture ensures that every decision is deterministic, reproducible, and traceable back to explicit governance rules.



---



\## 2. Inputs to the Decision Engine



The Authority Engine evaluates a decision using the following inputs:



\- \*\*Identity\*\*

&nbsp; - Display name (e.g., `Ronald`)

&nbsp; - Status (e.g., `ACTIVE`, `SUSPENDED`)

&nbsp; - Credentials (e.g., `SOVEREIGN\_OWNER`, `FAMILY\_GUARDIAN`)

&nbsp; - Assigned roles (e.g., `SOVEREIGN\_OWNER`, `FAMILY\_GUARDIAN`)



\- \*\*Requested Permission\*\*

&nbsp; - The specific action being requested, e.g.:

&nbsp;   - `AUTHORIZE\_EMERGENCY\_LOCKDOWN`



\- \*\*System State\*\*

&nbsp; - Contextual state of the system, e.g.:

&nbsp;   - `NORMAL`

&nbsp;   - `CRISIS`



\- \*\*Governance Policies (from config)\*\*

&nbsp; - Policy ID (e.g., `policy-001`)

&nbsp; - Policy name and description

&nbsp; - Conditions:

&nbsp;   - Required role

&nbsp;   - Required system state

&nbsp;   - Minimum approval threshold

&nbsp; - Human-readable reason



These inputs are provided by configuration and runtime context; the engine itself does not hard-code business rules.



---



\## 3. Governance Configuration



Governance behavior is defined in two primary configuration files:



1\. \*\*Scenarios\*\* – `config/governance\_scenarios.json` 

&nbsp;  Describes testable situations for the CLI, for example:

&nbsp;  - Identity label and role

&nbsp;  - Credential to attach

&nbsp;  - Requested permission

&nbsp;  - System state

&nbsp;  - Linked `policy\_id`

&nbsp;  - Expected decision (for validation)



2\. \*\*Policies\*\* – `config/governance\_policies.json` 

&nbsp;  Describes the actual rules of authority, including:

&nbsp;  - `id`: unique policy identifier (e.g., `policy-001`)

&nbsp;  - `name`: human-readable policy title 

&nbsp;  - `conditions`:

&nbsp;    - `identity\_role` – which role the identity must hold

&nbsp;    - `required\_system\_state` – which system state must be active

&nbsp;    - `minimum\_approvals` – how many approvals are required

&nbsp;  - `reason`: narrative rationale for the policy



Because policies reside in configuration, governance can be reviewed, versioned, and approved without modifying code.



---



\## 4. Evaluation Flow



When the Authority Engine is invoked, it follows this process:



1\. \*\*Identity \& Role Check\*\*

&nbsp;  - Confirms the identity is active.

&nbsp;  - Confirms the identity holds the relevant role(s) for the policy.



2\. \*\*Permission Check\*\*

&nbsp;  - Confirms the requested permission is associated with the role.

&nbsp;  - If the role does not grant the permission, the request is denied.



3\. \*\*Policy Condition Check\*\*

&nbsp;  - Looks up the policy associated with the scenario via `policy\_id`.

&nbsp;  - Verifies that:

&nbsp;    - The identity’s role matches `identity\_role`.

&nbsp;    - The current system state matches `required\_system\_state`.

&nbsp;    - Any approval thresholds (`minimum\_approvals`) are satisfied or flagged as additional requirements.



4\. \*\*Decision Determination\*\*

&nbsp;  - If all conditions are satisfied and approvals are sufficient:

&nbsp;    - Decision → `ALLOW`

&nbsp;  - If conditions are violated (e.g., wrong system state):

&nbsp;    - Decision → `DENY`

&nbsp;  - If conditions are partially satisfied but more approvals are required:

&nbsp;    - Decision → `REQUIRE\_ADDITIONAL\_APPROVAL`



5\. \*\*Audit Event Creation\*\*

&nbsp;  - The engine constructs an audit event containing:

&nbsp;    - Identity label

&nbsp;    - Requested permission

&nbsp;    - System state

&nbsp;    - Final decision

&nbsp;    - Applied policy IDs

&nbsp;    - Timestamp

&nbsp;    - Reason string summarizing the situation



6\. \*\*Persistence and Explainability\*\*

&nbsp;  - The audit event is written to `data/audit\_log.jsonl`.

&nbsp;  - The CLI prints the decision and an “Applied policies” section showing:

&nbsp;    - Policy ID

&nbsp;    - Policy name

&nbsp;    - Policy rationale (reason)



---



\## 5. Example Decision



\*\*Scenario:\*\* The identity “Ronald” holds the `SOVEREIGN\_OWNER` role and requests `AUTHORIZE\_EMERGENCY\_LOCKDOWN` while the system is in `CRISIS` state.



\*\*Relevant Policy (from config):\*\*



\- `policy-001` – \*Emergency Sovereign Authority\* 

&nbsp; - `identity\_role`: `SOVEREIGN\_OWNER` 

&nbsp; - `required\_system\_state`: `CRISIS` 

&nbsp; - `minimum\_approvals`: `1` 

&nbsp; - `reason`: “Sovereign owner may authorize emergency actions during crisis”



\*\*Engine Outcome:\*\*



\- Decision: `ALLOW` 

\- Applied policies:

&nbsp; - `policy-001: Emergency Sovereign Authority – Sovereign owner may authorize emergency actions during crisis` 

\- Audit event written with:

&nbsp; - `identity\_label = "Ronald"`

&nbsp; - `requested\_permission\_name = "AUTHORIZE\_EMERGENCY\_LOCKDOWN"`

&nbsp; - `system\_state = "CRISIS"`

&nbsp; - `decision = "ALLOW"`

&nbsp; - `policy\_ids = \["policy-001"]`

&nbsp; - `timestamp = <ISO8601 timestamp>`

&nbsp; - `reason = "Sovereign owner attempts emergency lockdown in crisis state"`



This illustrates how a single policy’s conditions lead to a clear, explainable decision and a verifiable audit record.



---



\## 6. Accountability and Transparency Properties



The decision model enforces accountability and transparency through:



\- \*\*Policy-Driven Behavior\*\* 

&nbsp; All authority rules are configuration-based, not buried in code.



\- \*\*Deterministic Outcomes\*\* 

&nbsp; Identical inputs always lead to identical decisions, supporting reproducibility and testing.



\- \*\*Immutable Audit Trail\*\* 

&nbsp; Every decision is recorded with inputs, policy IDs, outcome, and rationale.



\- \*\*Explainability\*\* 

&nbsp; The system surfaces which policies were applied and why, in human-readable language, suitable for oversight and external review.



Together, these properties ensure that governance decisions are not only technically correct, but also understandable, challengeable, and defensible.

