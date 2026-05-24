import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PATHS_FILE = PROJECT_ROOT / "configs" / "local_paths.json"


def load_local_paths():
    """
    Loads machine-specific local paths.

    local_paths.json is intentionally not meant to be committed to GitHub.
    Each user creates their own copy based on local_paths.example.json.
    """
    local_paths = {
        "PROJECT_ROOT": str(PROJECT_ROOT),
    }

    if LOCAL_PATHS_FILE.exists():
        with open(LOCAL_PATHS_FILE, "r") as f:
            user_paths = json.load(f)

        local_paths.update(user_paths)

    return local_paths


def resolve_path(path_value):
    """
    Resolves paths with placeholders.

    Supports:
      ${PROJECT_ROOT}/data/...
      ${KITTI_COLOR_ROOT}/sequences/00
      ~/datasets/...
      relative/path
    """
    if path_value is None:
        return None

    path_str = str(path_value)
    local_paths = load_local_paths()

    for key, value in local_paths.items():
        path_str = path_str.replace("${" + key + "}", str(value))

    path_str = os.path.expandvars(path_str)
    path_str = os.path.expanduser(path_str)

    path = Path(path_str)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


def load_json(path):
    path = resolve_path(path)

    with open(path, "r") as f:
        return json.load(f)


def load_sequences():
    config = load_json("configs/sequences.json")
    return config["sequences"]


def load_methods():
    config = load_json("configs/methods.json")
    return config["methods"]


def get_sequence(sequence_name):
    for seq in load_sequences():
        if seq["name"] == sequence_name:
            return seq

    raise KeyError(f"Sequence not found: {sequence_name}")


def get_method(method_name):
    for method in load_methods():
        if method["name"] == method_name:
            return method

    raise KeyError(f"Method not found: {method_name}")


def resolve_sequence_paths(seq):
    """
    Returns a copy of a sequence config with path-like fields resolved.
    """
    seq = dict(seq)

    if "path" in seq:
        seq["path"] = str(resolve_path(seq["path"]))

    if "groundtruth" in seq:
        seq["groundtruth"] = str(resolve_path(seq["groundtruth"]))

    return seq