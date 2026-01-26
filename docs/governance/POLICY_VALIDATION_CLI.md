Policy Validation CLI Command

Purpose



This command provides a deterministic, read-only check of the current governance policy configuration. It ensures that policies meet the Policy Validation Checklist before they are loaded and used by the Sovereignty Control System.



The command is intended for:



System operators



Governance maintainers



Reviewers who want to confirm configuration integrity



It does not execute any governance decisions or modify any files.



Command Overview



The policy validation command is exposed as a subcommand of the existing CLI:



python src/sovereignty\_cli.py validate-policies





This command:



Loads the active policy configuration



Applies all static validation rules



Reports any structural, logical, or consistency errors



Exits with a clear success/failure status



Usage

Basic Usage

python src/sovereignty\_cli.py validate-policies



Optional Arguments (Conceptual)



--config PATH

Use an explicit policy configuration file or directory instead of the default.



python src/sovereignty\_cli.py validate-policies --config config/policies.json





--strict

Treat warnings as errors (fail on any non-ideal configuration).



python src/sovereignty\_cli.py validate-policies --strict





These options are optional and may be introduced incrementally. The core behavior is the no-argument form.



Behavior



When invoked, the command MUST:



Load policy configuration from the defined source



Apply the Policy Validation Checklist, including:



Policy identity validation



Policy version validation



Activation status validation



Scope and condition validation



Conflict detection



Decision outcome validation



Policy change log consistency checks



Produce a human-readable summary to stdout



Exit with an appropriate status code (see below)



The command MUST NOT:



Modify any policy files



Modify any logs



Write to data/policy\_change\_log.jsonl or data/audit\_log.jsonl



Trigger any governance decisions



Exit Codes



0 — Validation passed



Policy configuration is structurally valid and consistent



1 — Validation failed



One or more validation errors were found



2 — CLI or runtime error



Configuration could not be loaded, or an unexpected error occurred



These codes allow automated tooling (CI, deployment scripts, etc.) to gate changes on successful validation.



Example Outputs

Successful Validation

Running static policy validation...



\[OK] Policy set loaded successfully.

\[OK] All policy IDs are unique.

\[OK] Policy versions are valid and consistent.

\[OK] No conflicting active policies detected.

\[OK] All policies reference valid decision outcomes.

\[OK] Policy change log is consistent with current versions.



Validation completed: PASS





Exit code: 0



Failed Validation (Example)

Running static policy validation...



\[OK] Policy set loaded successfully.

\[ERROR] Duplicate policy\_id detected: policy-001

\[ERROR] Conflict detected between policies policy-001 and policy-004 for role=Guardian, permission=AUTHORIZE\_EMERGENCY\_LOCKDOWN, state=CRISIS.

\[ERROR] Policy policy-003 references unknown previous\_version: 1.2.0 in policy\_change\_log.jsonl.



Validation completed: FAIL (3 error(s) found)





Exit code: 1



The goal is to produce clear, reviewer-readable messages that make misconfiguration obvious.

