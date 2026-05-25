import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from config_utils import load_local_paths


TIMESTAMP_FILES = {
    "euroc_mh01": "MH01.txt",
    "euroc_mh02": "MH02.txt",
    "euroc_mh03": "MH03.txt",
    "euroc_mh04": "MH04.txt",
    "euroc_mh05": "MH05.txt",
}


OUTPUT_SUFFIXES = {
    "euroc_mh01": "dataset-MH01_monoi",
    "euroc_mh02": "dataset-MH02_monoi",
    "euroc_mh03": "dataset-MH03_monoi",
    "euroc_mh04": "dataset-MH04_monoi",
    "euroc_mh05": "dataset-MH05_monoi",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run ORB-SLAM3 Monocular-Inertial on a EuRoC sequence."
    )

    parser.add_argument("--sequence-name", required=True)
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--output", required=True)

    return parser.parse_args()


def find_sequence_root(sequence_path: Path) -> Path:
    """
    Framework sequence path usually points to:
        <EUROC_ROOT>/MH_01_easy/mav0/cam0/data

    ORB-SLAM3 expects the sequence root:
        <EUROC_ROOT>/MH_01_easy
    """
    if sequence_path.name == "data":
        return sequence_path.parents[2]

    return sequence_path
def normalize_euroc_timestamps(input_path: Path, output_path: Path) -> None:
    """
    Converts ORB-SLAM3 EuRoC timestamps to TUM-compatible seconds if needed.

    ORB-SLAM3 EuRoC outputs may store timestamps in nanoseconds, while evo
    expects both prediction and ground truth to use the same time unit.
    """
    converted_lines = []

    with input_path.open("r") as f:
        for line in f:
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            parts = stripped.split()

            if len(parts) < 8:
                continue

            timestamp = float(parts[0])

            # EuRoC raw timestamps are usually nanoseconds around 1e18.
            # TUM/evo trajectory files usually use seconds around 1e9.
            if timestamp > 1e12:
                timestamp /= 1e9

            parts[0] = f"{timestamp:.9f}"
            converted_lines.append(" ".join(parts))

    if not converted_lines:
        raise RuntimeError(f"No valid trajectory rows found in {input_path}")

    output_path.write_text("\n".join(converted_lines) + "\n")

def main():
    args = parse_args()

    sequence_name = args.sequence_name
    sequence_path = Path(args.sequence).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if sequence_name not in TIMESTAMP_FILES:
        raise ValueError(f"Unsupported EuRoC sequence: {sequence_name}")

    local_paths = load_local_paths()

    if "ORB_SLAM3_ROOT" not in local_paths:
        raise KeyError("ORB_SLAM3_ROOT is missing from configs/local_paths.json")

    orb_root = Path(local_paths["ORB_SLAM3_ROOT"]).expanduser().resolve()

    executable = orb_root / "Examples" / "Monocular-Inertial" / "mono_inertial_euroc"
    vocabulary = orb_root / "Vocabulary" / "ORBvoc.txt"
    settings = orb_root / "Examples" / "Monocular-Inertial" / "EuRoC.yaml"
    timestamps = (
        orb_root
        / "Examples"
        / "Monocular-Inertial"
        / "EuRoC_TimeStamps"
        / TIMESTAMP_FILES[sequence_name]
    )

    sequence_root = find_sequence_root(sequence_path)
    output_suffix = OUTPUT_SUFFIXES[sequence_name]

    required_paths = [orb_root, executable, vocabulary, settings, timestamps, sequence_root]

    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(f"Required path not found: {path}")

    expected_outputs = [
        orb_root / f"f_{output_suffix}.txt",
        orb_root / f"kf_{output_suffix}.txt",
        orb_root / "CameraTrajectory.txt",
        orb_root / "KeyFrameTrajectory.txt",
    ]

    for old_output in expected_outputs:
        if old_output.exists():
            old_output.unlink()

    command = [
        str(executable),
        str(vocabulary),
        str(settings),
        str(sequence_root),
        str(timestamps),
        output_suffix,
    ]

    print("Running ORB-SLAM3 Monocular-Inertial:")
    print(" ".join(command))

    completed = subprocess.run(command, cwd=str(orb_root))

    candidate_outputs = [
        orb_root / f"f_{output_suffix}.txt",
        orb_root / "CameraTrajectory.txt",
        orb_root / f"kf_{output_suffix}.txt",
        orb_root / "KeyFrameTrajectory.txt",
    ]

    trajectory = None

    for candidate in candidate_outputs:
        if candidate.exists() and candidate.stat().st_size > 0:
            trajectory = candidate
            break

    if trajectory is None:
        raise RuntimeError(
            f"ORB-SLAM3 failed with return code {completed.returncode}, "
            f"and no trajectory file was found. Check stdout.log and stderr.log."
    )

    if completed.returncode != 0:
        print(
            f"Warning: ORB-SLAM3 exited with return code {completed.returncode}, "
            f"but a trajectory was found at {trajectory}. Continuing."
        )

    raw_copy = output_path.parent / "predicted_trajectory_raw.txt"
    shutil.copyfile(trajectory, raw_copy)

    normalize_euroc_timestamps(raw_copy, output_path)

    print(f"Saved raw trajectory to: {raw_copy}")
    print(f"Saved timestamp-normalized framework trajectory to: {output_path}")


if __name__ == "__main__":
    main()
