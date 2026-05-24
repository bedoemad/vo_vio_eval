import argparse
from pathlib import Path

import numpy as np

from config_utils import (
    load_sequences,
    resolve_sequence_paths,
    load_local_paths,
    resolve_path,
)


def ok(msg):
    print(f"[OK] {msg}")


def skip(msg):
    print(f"[SKIP] {msg}")


def warn(msg):
    print(f"[WARN] {msg}")


def rotation_matrix_to_quaternion(R):
    """
    Converts 3x3 rotation matrix to quaternion in qx qy qz qw format.
    """
    R = np.asarray(R, dtype=float)

    trace = np.trace(R)

    if trace > 0:
        s = np.sqrt(trace + 1.0) * 2.0
        qw = 0.25 * s
        qx = (R[2, 1] - R[1, 2]) / s
        qy = (R[0, 2] - R[2, 0]) / s
        qz = (R[1, 0] - R[0, 1]) / s

    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s

    elif R[1, 1] > R[2, 2]:
        s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s

    else:
        s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s

    q = np.array([qx, qy, qz, qw], dtype=float)
    norm = np.linalg.norm(q)

    if norm > 0:
        q = q / norm

    return q


def prepare_euroc_groundtruth(seq, force=False):
    name = seq["name"]
    gt_out = Path(seq["groundtruth"])

    if gt_out.exists() and not force:
        skip(f"{name}: ground truth already exists: {gt_out}")
        return

    source_csv = gt_out.parent / "data.csv"

    if not source_csv.exists():
        warn(f"{name}: missing EuRoC source ground truth CSV: {source_csv}")
        return

    gt_out.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    with open(source_csv, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    data_lines = [line for line in lines if not line.startswith("#")]

    for line in data_lines:
        parts = [p.strip() for p in line.split(",")]

        if len(parts) < 8:
            continue

        timestamp_ns = int(float(parts[0]))
        timestamp_sec = timestamp_ns * 1e-9

        tx = float(parts[1])
        ty = float(parts[2])
        tz = float(parts[3])

        # EuRoC data.csv stores quaternion as qw qx qy qz
        qw = float(parts[4])
        qx = float(parts[5])
        qy = float(parts[6])
        qz = float(parts[7])

        rows.append(
            f"{timestamp_sec:.9f} "
            f"{tx:.9f} {ty:.9f} {tz:.9f} "
            f"{qx:.9f} {qy:.9f} {qz:.9f} {qw:.9f}"
        )

    with open(gt_out, "w") as f:
        for row in rows:
            f.write(row + "\n")

    ok(f"{name}: wrote EuRoC TUM ground truth: {gt_out} ({len(rows)} poses)")


def kitti_sequence_id(seq_name):
    return seq_name.split("_")[-1]


def prepare_kitti_groundtruth(seq, force=False):
    name = seq["name"]
    seq_id = kitti_sequence_id(name)

    gt_out = Path(seq["groundtruth"])

    if gt_out.exists() and not force:
        skip(f"{name}: ground truth already exists: {gt_out}")
        return

    local_paths = load_local_paths()

    if "KITTI_POSES_ROOT" not in local_paths:
        warn(f"{name}: KITTI_POSES_ROOT not defined in configs/local_paths.json")
        return

    poses_root = resolve_path("${KITTI_POSES_ROOT}")
    pose_file = poses_root / f"{seq_id}.txt"

    seq_path = Path(seq["path"])
    times_file = seq_path / "times.txt"

    if not pose_file.exists():
        warn(f"{name}: missing KITTI pose file: {pose_file}")
        return

    if not times_file.exists():
        warn(f"{name}: missing KITTI times file: {times_file}")
        return

    poses = np.loadtxt(pose_file)
    times = np.loadtxt(times_file)

    if poses.ndim == 1:
        poses = poses.reshape(1, -1)

    n = min(len(poses), len(times))

    if len(poses) != len(times):
        warn(
            f"{name}: poses/times length mismatch. "
            f"poses={len(poses)}, times={len(times)}, using n={n}"
        )

    gt_out.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for i in range(n):
        vals = poses[i]

        if len(vals) != 12:
            warn(f"{name}: skipping malformed pose row {i}")
            continue

        T = vals.reshape(3, 4)

        R = T[:, :3]
        t = T[:, 3]

        qx, qy, qz, qw = rotation_matrix_to_quaternion(R)

        rows.append(
            f"{float(times[i]):.9f} "
            f"{t[0]:.9f} {t[1]:.9f} {t[2]:.9f} "
            f"{qx:.9f} {qy:.9f} {qz:.9f} {qw:.9f}"
        )

    with open(gt_out, "w") as f:
        for row in rows:
            f.write(row + "\n")

    ok(f"{name}: wrote KITTI TUM ground truth: {gt_out} ({len(rows)} poses)")


def prepare_sequence(seq, force=False):
    dataset = seq.get("dataset", "").lower()

    if dataset == "euroc":
        prepare_euroc_groundtruth(seq, force=force)

    elif dataset == "kitti":
        prepare_kitti_groundtruth(seq, force=force)

    else:
        warn(f"{seq['name']}: unsupported dataset type: {seq.get('dataset')}")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare dataset ground-truth files for VO/VIO evaluation."
    )

    parser.add_argument(
        "--dataset",
        choices=["euroc", "kitti", "all"],
        default="all",
        help="Which dataset ground truth to prepare.",
    )
    parser.add_argument(
    "--all",
    action="store_true",
    help="Shortcut for --dataset all.",
)

    parser.add_argument(
        "--sequences",
        nargs="+",
        default=None,
        help="Optional specific sequence names to prepare.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate files even if they already exist.",
    )

    args = parser.parse_args()
    if args.all:
        args.dataset = "all"

    sequences = [resolve_sequence_paths(seq) for seq in load_sequences()]

    if args.sequences:
        wanted = set(args.sequences)
        sequences = [seq for seq in sequences if seq["name"] in wanted]

    if args.dataset != "all":
        sequences = [
            seq
            for seq in sequences
            if seq.get("dataset", "").lower() == args.dataset
        ]

    if not sequences:
        warn("No matching sequences found.")
        return

    for seq in sequences:
        prepare_sequence(seq, force=args.force)

    print("\nDataset preparation finished.")


if __name__ == "__main__":
    main()
