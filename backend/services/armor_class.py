from __future__ import annotations
import json
import os
from typing import Dict, Any

_cache: Dict[str, Any] | None = None


def _load() -> Dict[str, Any]:
    global _cache
    if _cache is None:
        data_dir = os.environ.get("DATA_DIR", "/app/data")
        path = os.path.join(data_dir, "armor_classes.json")
        with open(path) as f:
            _cache = json.load(f)
    return _cache


def get_multiplier(armor_class: str, shell_type: str) -> float:
    """Return the KE or HEAT multiplier for an armor class. Defaults to 1.0 for unknown classes."""
    classes = _load()
    entry = classes.get(armor_class)
    if entry is None:
        return 1.0
    key = "ke" if shell_type == "ke" else "heat"
    return float(entry.get(key, 1.0))
