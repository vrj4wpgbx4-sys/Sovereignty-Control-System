\# v1.1 Planning — Sovereignty Control System



\## Purpose



v1.1 builds on the stabilized v1.0 checkpoint to improve \*\*reviewability,

explainability, and operational clarity\*\* without changing the core authority

model or integrity guarantees.



Where v1.0 focused on \*making history tamper-detectable\*, v1.1 focuses on

\*making that history understandable and reviewable at scale\*.



This is an incremental release: no breaking changes to v1.0 guarantees.



---



\## Guiding Principles



\- Preserve v1.0 integrity and provenance guarantees

\- No new implicit authority or autonomy

\- Prefer \*\*read-only tools\*\* over new write paths

\- Improve reviewer and operator experience

\- Keep everything local-first and offline-verifiable



---



\## In Scope (v1.1)



\### 1) Decision Replay / Explanation CLI (Primary)



\*\*Goal:\*\*  

Allow reviewers to replay and explain past decisions from the audit log.



\*\*Capabilities:\*\*

\- Walk `data/audit\_log.jsonl`

\- Select a decision by index, timestamp, or correlation ID

\- Display:

&nbsp; - Decision outcome

&nbsp; - Identity

&nbsp; - Requested action

&nbsp; - Policy IDs

&nbsp; - `policy\_version\_id`

&nbsp; - Reason

\- Clearly separate:

&nbsp; - What the system \*decided\*

&nbsp; - What policy version it \*claimed to follow\*



\*\*Constraints:\*\*

\- Read-only

\- No enforcement

\- No mutation of logs



---



\### 2) Cross-Log Correlation (Audit ↔ Enforcement)



\*\*Goal:\*\*  

Make it easy to correlate a decision with downstream enforcement actions.



\*\*Ideas:\*\*

\- Standardize a correlation field (e.g., `decision\_correlation\_id`)

\- Ensure enforcement `decision\_reference` consistently includes:

&nbsp; - timestamp

&nbsp; - identity

&nbsp; - policy\_version\_id



\*\*Status:\*\*

\- Design-first in v1.1

\- Optional wiring if low-risk



---



\### 3) Reviewer-Facing Summaries



\*\*Goal:\*\*  

Produce concise summaries suitable for non-technical reviewers.



\*\*Examples:\*\*

\- “Why was this lockdown allowed?”

\- “Which policy version governed this action?”

\- “Was enforcement actually performed?”



\*\*Format options:\*\*

\- CLI text output

\- Markdown export

\- JSON summary for tooling



---



\## Explicitly Out of Scope (v1.1)



\- New authority roles

\- Policy language changes

\- Automated policy correctness proofs

\- External services or anchoring

\- GUI or web interfaces (deferred)



---



\## Success Criteria



v1.1 is complete when:



\- A reviewer can explain \*any\* v1.0+ decision using only:

&nbsp; - the audit log

&nbsp; - the verification CLI

&nbsp; - v1.1 replay/explanation tools

\- No new integrity risks are introduced

\- v1.0 behavior remains unchanged



---



\## Relationship to v1.0



v1.1:

\- Extends \*visibility\*, not \*authority\*

\- Consumes existing logs, does not redefine them

\- Treats v1.0 artifacts as immutable



---



\## Tentative Milestones



1\. v1.1-step-1: Decision replay CLI (read-only)

2\. v1.1-step-2: Correlation enhancements (design or light wiring)

3\. v1.1-step-3: Reviewer summary outputs

4\. v1.1-checkpoint



---



\## Status



Planning document — active.

No code changes have been made yet.



