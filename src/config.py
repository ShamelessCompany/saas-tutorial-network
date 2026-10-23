"""Config loader and validator for SaaS tutorial workflows."""
from pathlib import Path
from typing import Any, Dict
import yaml

def load_workflow(config_path: str | Path) -> Dict[str, Any]:
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Workflow config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Invalid workflow configuration: Root must be a mapping")

    # Sensible defaults
    data.setdefault("title", "SaaS Tutorial")
    data.setdefault("viewport", {"width": 1920, "height": 1080})
    data.setdefault("steps", [])
    data.setdefault("narration", {"enabled": False})
    data.setdefault("affiliate", {})

    return data
