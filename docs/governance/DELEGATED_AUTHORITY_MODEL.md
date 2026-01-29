\# DELEGATED AUTHORITY MODEL  

\*\*Sovereignty Control System — Version 0.7\*\*



\## 1. Purpose



This document defines how \*\*delegated authority\*\* operates within the Sovereignty Control System.



The objective is to allow carefully scoped delegation (e.g., guardians, operators, or automation) \*\*without expanding ultimate sovereign power\*\* and without weakening the accountability, correlation, and visibility guarantees established in versions 0.4–0.6.



Delegation provides \*convenience and continuity\*; it must not create \*new, uncontrolled centers of power\*.



---



\## 2. Core Principles



1\. \*\*Delegation is Derived, Not Native\*\*  

&nbsp;  All delegated authority is derived from an existing principal (e.g., Sovereign Owner) and exists only within the limits defined here. Delegates never gain more authority than the principal holds.



2\. \*\*Scope Before Power\*\*  

&nbsp;  Delegations must be narrowly defined by:

&nbsp;  - action types,

&nbsp;  - thresholds,

&nbsp;  - time bounds, and

&nbsp;  - system states  

&nbsp;  before any delegated action can be evaluated.



3\. \*\*No Hidden Delegation\*\*  

&nbsp;  Every delegation must be recorded as an explicit governance artifact. Implicit, verbal, or undocumented delegations are treated as \*\*invalid\*\*.



4\. \*\*Reversible by Design\*\*  

&nbsp;  Every delegation must be:

&nbsp;  - revocable,

&nbsp;  - inspectable, and

&nbsp;  - auditable  

&nbsp;  without system downtime or special intervention.



5\. \*\*Compatibility with Existing Guarantees\*\*  

&nbsp;  Delegation must not weaken:

&nbsp;  - deterministic decision outcomes,

&nbsp;  - decision correlation,

&nbsp;  - enforcement rules, or

&nbsp;  - oversight visibility.



---



\## 3. Actors and Roles



\### 3.1 Principal



The \*\*Principal\*\* is the originating source of authority (e.g., Sovereign Owner or explicitly defined sovereign body).



Characteristics:



\- Holds the \*\*full, original authority\*\* within their defined scope.

\- May grant or revoke delegations within the limits defined by policy.

\- Remains \*\*ultimately accountable\*\* for delegated actions.



\### 3.2 Delegate



A \*\*Delegate\*\* is an identity that is granted a subset of the Principal’s authority.



Characteristics:



\- May act only within the \*\*explicitly defined scope\*\* of the delegation.

\- Cannot create further delegations unless policies explicitly permit it (and then only within additional constraints).

\- All actions taken by a delegate must remain \*\*correlated\*\* to both:

&nbsp; - the delegate’s identity, and

&nbsp; - the originating Principal and delegation record.



\### 3.3 Oversight / Auditor



Oversight roles do not hold functional authority but must be able to see:



\- active delegations,

\- their scopes and limits,

\- decisions taken under delegated authority, and

\- enforcement outcomes.



They cannot create, use, or extend delegations.



---



\## 4. Delegation Types



\### 4.1 Action-Scoped Delegation



Delegation that is restricted to \*\*specific actions\*\*, such as:



\- routine account access,

\- non-emergency configuration changes,

\- informational queries.



Rules:



\- The allowed actions must be enumerated.

\- Any attempt to use a delegated identity for an \*\*out-of-scope action\*\* must be denied.



\### 4.2 Threshold-Scoped Delegation



Delegation tied to \*\*quantitative limits\*\* (e.g., transaction size, frequency, or risk weight).



Rules:



\- Policies must define:

&nbsp; - the metric,

&nbsp; - the threshold,

&nbsp; - the evaluation window (per action, per day, etc.).

\- Attempts to exceed a threshold must result in:

&nbsp; - `REQUIRE\_ADDITIONAL\_APPROVAL` or `DENY`, as defined by policy.



\### 4.3 Time-Scoped Delegation



Delegation active only within a \*\*defined time window\*\*.



Rules:



\- Every time-scoped delegation must have:

&nbsp; - a start timestamp, and

&nbsp; - an end timestamp.

\- Actions requested outside the valid time window must be treated as \*\*unauthorized\*\*, regardless of other conditions.



---



\## 5. Delegation Records



Each delegation must be represented as a structured record, containing at minimum:



\- `delegation\_id` (unique, immutable)

\- `principal\_identity\_label`

\- `delegate\_identity\_label`

\- `delegation\_scope` (actions, thresholds, states)

\- `valid\_from` (timestamp)

\- `valid\_until` (timestamp or explicit “until revoked” flag)

\- `policy\_ids` (policies authorizing this delegation)

\- `created\_timestamp`

\- `created\_reason`

\- `revoked\_timestamp` (if applicable)

\- `revoked\_reason` (if applicable)



Delegation records must be stored in an \*\*append-only, auditable form\*\*, analogous to decisions and audit events.



---



\## 6. Decision Evaluation with Delegation



When a delegated identity initiates a governed action, the decision engine must:



1\. \*\*Resolve Principal Context\*\*  

&nbsp;  Determine whether the delegate is acting under:

&nbsp;  - an active, valid delegation record, and

&nbsp;  - which Principal the delegation derives from.



2\. \*\*Verify Delegation Scope\*\*  

&nbsp;  Confirm that:

&nbsp;  - the requested action is within the delegation scope,

&nbsp;  - any thresholds are respected, and

&nbsp;  - the current system state is permitted for delegated use.



3\. \*\*Apply Standard Policies\*\*  

&nbsp;  Evaluate the requested action using the \*\*existing decision model\*\*, as if the Principal had requested it, subject to delegation limits.



4\. \*\*Emit Delegation-Aware Decision\*\*  

&nbsp;  Decision records must include sufficient information to identify:

&nbsp;  - the delegate identity,

&nbsp;  - the principal identity, and

&nbsp;  - the `delegation\_id` involved (if any).



If delegation validation fails at any step, the decision outcome must be `DENY` or `REQUIRE\_ADDITIONAL\_APPROVAL`, as defined by policy.



---



\## 7. Correlation and Enforcement



All actions taken under delegated authority must preserve the existing guarantees:



\- Every decision must carry a `decision\_correlation\_id`.

\- Every enforcement record must:

&nbsp; - reference the `decision\_correlation\_id`, and

&nbsp; - include `delegate\_identity\_label` and `delegation\_id` where applicable.



If enforcement detects that an action is being executed under an \*\*expired, revoked, or invalid delegation\*\*, it must:



\- block the action (`BLOCKED`), and

\- emit an enforcement record indicating the delegation failure.



---



\## 8. Revocation and Expiry



Delegations may end in three ways:



1\. \*\*Natural Expiry\*\*  

&nbsp;  The `valid\_until` timestamp passes. Further delegated actions must be treated as unauthorized.



2\. \*\*Explicit Revocation\*\*  

&nbsp;  The Principal (or a policy-defined authority) revokes the delegation, setting:

&nbsp;  - `revoked\_timestamp`, and

&nbsp;  - `revoked\_reason`.



3\. \*\*Automatic Policy-Based Revocation\*\*  

&nbsp;  Policies may define conditions under which a delegation is automatically revoked (e.g., repeated policy violations, risk triggers).



After revocation or expiry:



\- The delegation record remains immutable and visible.

\- Any attempted use must be identified as an \*\*invalid delegation attempt\*\*.



---



\## 9. Oversight Visibility for Delegations



Oversight views must allow reviewers to see:



\- all active delegations,

\- the principals and delegates involved,

\- the scope and time bounds of each delegation,

\- decisions taken under delegated authority, and

\- enforcement results for those decisions.



Oversight remains \*\*read-only\*\* and must not provide controls to:



\- create delegations,

\- edit delegations, or

\- approve delegated actions.



---



\## 10. Compatibility and Non-Regressions



The Delegated Authority Model must not:



\- weaken existing decision determinism,

\- bypass the Enforcement Model,

\- break Decision Correlation,

\- or reduce Oversight Visibility.



Any implementation of delegation must be treated as \*\*non-compliant\*\* if it introduces:



\- implicit or undocumented delegations,

\- elevation of delegate authority beyond policy limits,

\- or untraceable delegated actions.



---



\## 11. Summary



Version 0.7 introduces \*\*structured, auditable delegation\*\*:



\- Delegates may act, but only within defined scopes.

\- Principals remain accountable.

\- All delegated actions remain:

&nbsp; - policy-governed,

&nbsp; - correlated,

&nbsp; - enforced, and

&nbsp; - visible to oversight.



Delegation is a \*\*narrower channel for existing authority\*\*, not a new source of power.



