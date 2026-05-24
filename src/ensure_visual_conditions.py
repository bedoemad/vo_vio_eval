import argparse
import subprocess
from pathlib import Path

from config_utils import load_sequences, resolve_sequence_paths


OUT_DIR = Path("results/visual_conditions")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd):
    cmd = [str(c) for c in cmd]

    print("\n" + "=" * 90)
    print(" ".join(cmd))
    print("=" * 90)

    result = subprocess.run(cmd)

    if result.returncode != 0:
        raise RuntimeError(f"Command failed with return code {result.returncode}")


def image_dir_for_sequence(seq):
    seq_path = Path(seq["path"])
    dataset = seq.get("dataset", "").lower()

    # If path already points directly to images
    if list(seq_path.glob("*.png")) or list(seq_path.glob("*.jpg")):
        return seq_path

    # If camera folder is specified
    folder = seq.get("camera_topic_or_folder")
    if folder:
        candidate = seq_path / folder
        if candidate.exists():
            return candidate

    # KITTI common folders
    for folder_name in ["image_2", "image_0", "image_3", "image_1"]:
        candidate = seq_path / folder_name
        if candidate.exists():
            return candidate

    # EuRoC common structure if root path was given
    candidate = seq_path / "mav0" / "cam0" / "data"
    if candidate.exists():
        return candidate

    raise RuntimeError(
        f"Could not determine image directory for {seq['name']}: {seq_path}"
    )


def times_file_for_sequence(seq):
    seq_path = Path(seq["path"])
    times_file = seq_path / "times.txt"

    if times_file.exists():
        return times_file

    return None


def ensure_visual_conditions(seq, force=False):
    name = seq["name"]
    dataset = seq.get("dataset", "").lower()

    out = OUT_DIR / f"{name}_cam0.csv"

    if out.exists() and not force:
        print(f"[SKIP] Visual conditions already exist: {out}")
        return

    image_dir = image_dir_for_sequence(seq)

    if dataset == "kitti":
        times_file = times_file_for_sequence(seq)

        if times_file is None:
            raise RuntimeError(f"KITTI sequence missing times.txt: {name}")

        run(
            [
                "python",
                "src/analyze_kitti_visual_conditions.py",
                "--image-dir",
                image_dir,
                "--times-file",
                times_file,
                "--output",
                out,
            ]
        )

    else:
        run(
            [
                "python",
                "src/analyze_visual_conditions.py",
                "--image-dir",
                image_dir,
                "--output",
                out,
            ]
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sequences", nargs="+", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    sequences = [resolve_sequence_paths(seq) for seq in load_sequences()]

    if args.sequences:
        wanted = set(args.sequences)
        sequences = [seq for seq in sequences if seq["name"] in wanted]

    for seq in sequences:
        ensure_visual_conditions(seq, force=args.force)


if __name__ == "__main__":
    main()