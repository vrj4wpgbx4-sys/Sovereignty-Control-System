import json
import os
from typing import Any, Dict, List, Tuple

POLICY_CONFIG_DEFAULT = os.path.join("config", "governance_policies.json")
POLICY_CHANGE_LOG_DEFAULT = os.path.join("data", "policy_change_log.jsonl")

ALLOWED_DECISIONS = {"ALLOW", "DENY", "REQUIRE_ADDITIONAL_APPROVAL"}


class ValidationResult:
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {lineno} in {path}: {e}") from e
    return events


def normalize_policy_id(policy: Dict[str, Any]) -> str:
    # Support either "policy_id" or "id"
    if "policy_id" in policy:
        return str(policy["policy_id"])
    if "id" in policy:
        return str(policy["id"])
    return ""


def normalize_policy_version(policy: Dict[str, Any]) -> str:
    # Support either "policy_version" or "version"
    if "policy_version" in policy:
        return str(policy["policy_version"])
    if "version" in policy:
        return str(policy["version"])
    return ""


def normalize_policy_decision(policy: Dict[str, Any]) -> str:
    # Support either "decision" or "outcome"
    if "decision" in policy:
        return str(policy["decision"])
    if "outcome" in policy:
        return str(policy["outcome"])
    return ""


def find_policy_list(raw: Any, result: ValidationResult) -> List[Dict[str, Any]]:
    """
    Try to interpret the loaded JSON as a list of policies.
    Acceptable shapes:
      - [ {policy...}, {...} ]
      - { "policies": [ {...}, {...} ] }
    """
    if isinstance(raw, list):
        if all(isinstance(p, dict) for p in raw):
            return raw  # type: ignore[return-value]
        result.add_error("Policy config JSON is a list but contains non-object entries.")
        return []

    if isinstance(raw, dict) and "policies" in raw:
        policies = raw["policies"]
        if isinstance(policies, list) and all(isinstance(p, dict) for p in policies):
            return policies  # type: ignore[return-value]
        result.add_error(
            "Policy config JSON has 'policies' key but its value is not a list of objects."
        )
        return []

    result.add_error(
        "Policy config JSON is not in a supported format. "
        "Expected a list of policy objects or an object with a 'policies' list."
    )
    return []


def validate_policies(
    config_path: str = POLICY_CONFIG_DEFAULT,
    change_log_path: str = POLICY_CHANGE_LOG_DEFAULT,
) -> ValidationResult:
    result = ValidationResult()

    # 1. Load policy configuration
    if not os.path.exists(config_path):
        result.add_error(f"Policy config file not found: {config_path}")
        return result

    try:
        raw_config = load_json(config_path)
    except Exception as e:
        result.add_error(f"Failed to load policy config '{config_path}': {e}")
        return result

    policies = find_policy_list(raw_config, result)
    if not policies:
        # If we already logged an error above, stop here.
        if not result.ok:
            return result

    # 2. Basic identity & version checks
    seen_ids = set()
    for idx, policy in enumerate(policies):
        label = f"Policy at index {idx}"

        policy_id = normalize_policy_id(policy)
        if not policy_id:
            result.add_error(f"{label} is missing 'policy_id' or 'id' field.")
        else:
            if policy_id in seen_ids:
                result.add_error(f"Duplicate policy_id detected: {policy_id}")
            else:
                seen_ids.add(policy_id)

        version = normalize_policy_version(policy)
        if not version:
            result.add_warning(
                f"{label} ({policy_id or 'unknown id'}) is missing a policy version field "
                "('policy_version' or 'version')."
            )

        decision = normalize_policy_decision(policy)
        if not decision:
            result.add_error(
                f"{label} ({policy_id or 'unknown id'}) is missing a decision field "
                "('decision' or 'outcome')."
            )
        elif decision not in ALLOWED_DECISIONS:
            result.add_error(
                f"{label} ({policy_id or 'unknown id'}) has unsupported decision value: {decision!r} "
                f"(expected one of {sorted(ALLOWED_DECISIONS)})."
            )

    # 3. Optional: policy change log consistency
    if os.path.exists(change_log_path):
        try:
            events = load_jsonl(change_log_path)
        except Exception as e:
            result.add_error(f"Failed to load policy change log '{change_log_path}': {e}")
            return result

        for idx, event in enumerate(events):
            label = f"Change log entry at line {idx + 1}"
            for key in ("timestamp", "policy_id", "policy_version", "change_type"):
                if key not in event:
                    result.add_error(f"{label} is missing required field: {key}")

            change_type = event.get("change_type")
            if change_type not in ("CREATE", "UPDATE", "DEPRECATE"):
                result.add_error(
                    f"{label} has invalid change_type={change_type!r} "
                    "(expected 'CREATE', 'UPDATE', or 'DEPRECATE')."
                )

        # Basic consistency: every policy in config should have at least one change log entry
        # This is a soft requirement: we treat it as a warning, not a hard error.
        event_policy_ids = {str(e.get("policy_id")) for e in events if "policy_id" in e}
        for policy in policies:
            pid = normalize_policy_id(policy)
            if pid and pid not in event_policy_ids:
                result.add_warning(
                    f"No policy change log entry found for policy_id={pid}. "
                    f"Consider adding a CREATE entry in {change_log_path}."
                )
    else:
        result.add_warning(
            f"Policy change log not found at {change_log_path}. "
            "Skipping change log consistency checks."
        )

    return result


def summarize_validation(result: ValidationResult) -> Tuple[str, int]:
    """
    Build a human-readable summary and choose an appropriate exit code.

    Returns:
        (summary_text, exit_code)
    """
    lines: List[str] = []
    lines.append("Running static policy validation...\n")

    if result.errors:
        for err in result.errors:
            lines.append(f"[ERROR] {err}")
    else:
        lines.append("[OK] No structural policy errors detected.")

    if result.warnings:
        for warn in result.warnings:
            lines.append(f"[WARN] {warn}")

    if result.ok:
        lines.append("\nValidation completed: PASS")
        code = 0
    else:
        lines.append(f"\nValidation completed: FAIL ({len(result.errors)} error(s) found)")
        code = 1

    return "\n".join(lines), code
