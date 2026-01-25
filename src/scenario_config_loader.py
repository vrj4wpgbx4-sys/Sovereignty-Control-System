"""
Scenario configuration loader.

Loads CLI scenarios from a JSON file so that identities, roles,
permissions, and policies can be adjusted without changing code.
"""

import json
from pathlib import Path
from typing import Dict, Any


def load_scenarios(config_path: str = "config/governance_scenarios.json") -> Dict[str, dict]:
    """
    Load scenario configurations from the given JSON file.

    Returns a mapping from menu option (e.g. "1", "2", "3") to the
    scenario configuration dictionary.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Scenario config file not found: {path}")

    data: Any = json.loads(path.read_text(encoding="utf-8"))
    scenarios: Dict[str, dict] = {}
    for scenario in data.get("scenarios", []):
        key = str(scenario.get("menu_option") or scenario.get("id"))
        if key:
            scenarios[key] = scenario

    return scenarios