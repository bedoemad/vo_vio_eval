import json
import shutil
from pathlib import Path

from config_utils import load_local_paths, load_sequences, load_methods, resolve_sequence_paths


def ok(msg):
    print(f"[OK] {msg}")


def warn(msg):
    print(f"[WARN] {msg}")


def missing(msg):
    print(f"[MISSING] {msg}")


def check_file(path, label):
    path = Path(path)
    if path.exists():
        ok(f"{label}: {path}")
        return True
    missing(f"{label}: {path}")
    return False


def check_dir(path, label):
    path = Path(path)
    if path.exists() and path.is_dir():
        ok(f"{label}: {path}")
        return True
    missing(f"{label}: {path}")
    return False


def check_json(path):
    path = Path(path)
    if not path.exists():
        missing(f"JSON file not found: {path}")
        return False

    try:
        with open(path, "r") as f:
            json.load(f)
        ok(f"Valid JSON: {path}")
        return True
    except Exception as exc:
        missing(f"Invalid JSON: {path} ({exc})")
        return False


def check_tool(name):
    found = shutil.which(name)
    if found:
        ok(f"Found tool {name}: {found}")
        return True
    missing(f"Tool not found in PATH: {name}")
    return False


def image_dir_for_sequence(seq):
    seq_path = Path(seq["path"])

    if list(seq_path.glob("*.png")) or list(seq_path.glob("*.jpg")):
        return seq_path

    folder = seq.get("camera_topic_or_folder")
    if folder:
        candidate = seq_path / folder
        if candidate.exists():
            return candidate

    for folder_name in ["image_2", "image_0", "image_3", "image_1"]:
        candidate = seq_path / folder_name
        if candidate.exists():
            return candidate

    candidate = seq_path / "mav0" / "cam0" / "data"
    if candidate.exists():
        return candidate

    return None


def main():
    print("\n=== Checking config files ===")
    check_json("configs/local_paths.json")
    check_json("configs/sequences.json")
    check_json("configs/methods.json")
    check_json("configs/benchmark_presets.json")

    print("\n=== Checking local paths ===")
    local_paths = load_local_paths()

    for key, value in local_paths.items():
        if key == "PROJECT_ROOT":
            check_dir(value, key)
        else:
            path = Path(value).expanduser()
            if path.exists():
                ok(f"{key}: {path}")
            else:
                warn(f"{key} path does not exist or is not configured: {path}")

    print("\n=== Checking tools ===")
    check_tool("python")
    check_tool("evo_ape")
    check_tool("evo_rpe")

    print("\n=== Checking methods ===")
    try:
        methods = load_methods()
        for method in methods:
            name = method.get("name", "<missing name>")
            command = method.get("command_template", "")
            if name and command:
                ok(f"Method configured: {name}")
            else:
                warn(f"Incomplete method config: {method}")
    except Exception as exc:
        missing(f"Could not load methods: {exc}")

    print("\n=== Checking sequences ===")
    try:
        sequences = [resolve_sequence_paths(seq) for seq in load_sequences()]

        for seq in sequences:
            name = seq["name"]
            print(f"\nSequence: {name}")

            check_dir(seq["path"], "sequence path")
            check_file(seq["groundtruth"], "ground truth")

            img_dir = image_dir_for_sequence(seq)
            if img_dir:
                images = list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg"))
                ok(f"image directory: {img_dir} ({len(images)} images)")
            else:
                missing(f"could not determine image directory for {name}")

            if seq.get("dataset", "").lower() == "kitti":
                times = Path(seq["path"]) / "times.txt"
                check_file(times, "KITTI times.txt")

    except Exception as exc:
        missing(f"Could not load sequences: {exc}")

    print("\nSetup check finished.")


if __name__ == "__main__":
    main()
