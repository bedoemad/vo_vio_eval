import numpy as np
import pandas as pd
from pathlib import Path

from config_utils import load_sequences, resolve_sequence_paths


OUT_DIR = Path("results/motion_conditions")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_tum(path: Path):
    return pd.read_csv(
        path,
        sep=r"\s+",
        header=None,
        names=["timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw"],
    )


def normalize_quat(q):
    q = np.asarray(q, dtype=float)
    norm = np.linalg.norm(q)

    if norm == 0:
        return q

    return q / norm


def quat_angle_deg(q1, q2):
    """
    Computes the angular difference between two orientations.
    Quaternion format: qx qy qz qw
    """
    q1 = normalize_quat(q1)
    q2 = normalize_quat(q2)

    # q and -q represent the same rotation
    dot = abs(float(np.dot(q1, q2)))
    dot = np.clip(dot, -1.0, 1.0)

    angle_rad = 2.0 * np.arccos(dot)
    return float(np.degrees(angle_rad))


def analyze_sequence(sequence):
    name = sequence["name"]
    gt_path = Path(sequence["groundtruth"])

    if not gt_path.exists():
        print(f"[SKIP] Missing ground truth for {name}: {gt_path}")
        return

    df = load_tum(gt_path)

    rows = []

    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]

        dt = float(curr["timestamp"] - prev["timestamp"])

        if dt <= 0:
            continue

        p_prev = np.array([prev["tx"], prev["ty"], prev["tz"]], dtype=float)
        p_curr = np.array([curr["tx"], curr["ty"], curr["tz"]], dtype=float)

        frame_translation_m = float(np.linalg.norm(p_curr - p_prev))
        translation_speed_mps = frame_translation_m / dt

        q_prev = np.array(
            [prev["qx"], prev["qy"], prev["qz"], prev["qw"]],
            dtype=float,
        )

        q_curr = np.array(
            [curr["qx"], curr["qy"], curr["qz"], curr["qw"]],
            dtype=float,
        )

        frame_rotation_deg = quat_angle_deg(q_prev, q_curr)
        rotation_speed_degps = frame_rotation_deg / dt

        rows.append(
            {
                "timestamp": float(curr["timestamp"]),
                "sequence": name,
                "frame_translation_m": frame_translation_m,
                "translation_speed_mps": translation_speed_mps,
                "frame_rotation_deg": frame_rotation_deg,
                "rotation_speed_degps": rotation_speed_degps,
            }
        )

    out = OUT_DIR / f"{name}_motion.csv"
    pd.DataFrame(rows).to_csv(out, index=False)

    print(f"{name}: saved {out}")


def main():
    sequences = load_sequences()

    for sequence in sequences:
        sequence = resolve_sequence_paths(sequence)
        analyze_sequence(sequence)


if __name__ == "__main__":
    main()