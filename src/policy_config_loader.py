"""
Policy configuration loader.

Loads governance policies from JSON so authority rules
can be audited and changed without touching code.
"""

import json
from pathlib import Path
from typing import Dict, Any


def load_policies(config_path: str = None) -> Dict[str, dict]:
    """
    Load policy configurations.

    Returns a mapping from policy_id -> policy dict.
    Paths are resolved relative to the repository root.
    """
    repo_root = Path(__file__).resolve().parent.parent
    path = Path(config_path) if config_path else repo_root / "config" / "governance_policies.json"

    if not path.exists():
        raise FileNotFoundError(f"Policy config file not found: {path}")

    data: Any = json.loads(path.read_text(encoding="utf-8"))
    policies: Dict[str, dict] = {}

    for policy in data.get("policies", []):
        policy_id = policy.get("id")
        if policy_id:
            policies[policy_id] = policy

    return policies