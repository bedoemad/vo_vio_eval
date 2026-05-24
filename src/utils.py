import json
from pathlib import Path
from typing import Dict

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def load_json(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Dict) -> None:
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)