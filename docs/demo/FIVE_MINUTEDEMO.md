\# Five-Minute Demo Script: Sovereignty Control System



This guide is designed so a non-technical reviewer, partner, or buyer can understand the value of the Sovereignty Control System in under five minutes by running a single command and observing the outcome.



---



\## What This Demo Shows



In less than five minutes, this demo demonstrates:



\* Authority rules are explicit and policy-driven

\* Decisions are deterministic and explainable

\* High-risk actions cannot occur silently

\* Every decision produces an auditable record



No code changes or configuration edits are required.



---



\## Prerequisites



\* Python 3.10 or later installed

\* Access to the project repository



No external services or databases are required.



---



\## Step 1: Open a Terminal



Navigate to the project root directory:



```bash

cd Sovereignty-Control-System

```



---



\## Step 2: Run the Governance Demo



Execute the command-line interface:



```bash

python src/sovereignty\_cli.py

```



You will see a menu of predefined governance scenarios.



---



\## Step 3: Run a High-Stakes Scenario



Select the following option:



```

1

```



This scenario represents an emergency lockdown request made by a sovereign owner during a declared crisis.



---



\## Step 4: Observe the Decision



The system will immediately display:



\* The identity requesting the action

\* The system state

\* The requested permission

\* The final decision (ALLOW / DENY / REQUIRE\_ADDITIONAL\_APPROVAL)



Example output:



```

Decision: ALLOW

```



This decision is deterministic and will not change unless governance policies are explicitly modified.



---



\## Step 5: Observe Policy Explainability



Immediately after the decision, the system shows \*why\* the decision was made:



```

Applied policies:

policy-001: Emergency Sovereign Authority – Sovereign owner may authorize emergency actions during crisis

```



This confirms that the outcome is tied to an explicit, human-readable policy—not hidden logic or discretion.



---



\## Step 6: Observe the Audit Record



The system then prints the audit event that was written to the log:



```json

{

&nbsp; "identity\_label": "Ronald",

&nbsp; "requested\_permission\_name": "AUTHORIZE\_EMERGENCY\_LOCKDOWN",

&nbsp; "system\_state": "CRISIS",

&nbsp; "decision": "ALLOW",

&nbsp; "policy\_ids": \["policy-001"],

&nbsp; "timestamp": "<ISO8601 timestamp>",

&nbsp; "reason": "Sovereign owner attempts emergency lockdown in crisis state"

}

```



This record is also appended to:



```

data/audit\_log.jsonl

```



No decision exists without a corresponding audit artifact.



---



\## Optional: Demonstrate a Denial or Escalation



To further illustrate governance constraints:



\* Select option `2` to observe a denial during a normal system state

\* Select option `3` to observe a decision that requires additional approval



These scenarios demonstrate that authority is conditional and proportionate.



---



\## Reviewer Takeaway



In under five minutes, the reviewer can verify that:



\* Governance rules are explicit and inspectable

\* Decisions are consistent and explainable

\* High-impact actions are logged automatically

\* Accountability is enforced by system design



This demo provides direct evidence of accountable, transparent decision-making without requiring trust in undocumented processes.



---



\## When to Use This Demo



\* Partner or buyer walkthroughs

\* Grant reviewer demonstrations

\* Governance or compliance discussions

\* Internal validation of authority rules



This script is intentionally simple so the system’s behavior—not its complexity—is the focus.



