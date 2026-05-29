from pathlib import Path

import pandas as pd


MOTION_DIR = Path("results/motion_conditions")
ERROR_DIR = Path("results/error_visual_correlation")
GENERIC_DIR = Path("results/generic_failure_diagnostics")

# Prefer the newest all-method diagnostic table.
# Fall back to older ORB-SLAM-only files for compatibility.
INPUT_FILES = [
    GENERIC_DIR / "all_methods_error_conditions.csv",
    ERROR_DIR / "all_sequences_orbslam3_mono.csv",
    ERROR_DIR / "all_kitti_sequences_orbslam3_kitti_mono.csv",
]

OUT = ERROR_DIR / "all_error_visual_motion_conditions.csv"


def nearest_merge(left, right, tolerance=0.05):
    return pd.merge_asof(
        left.sort_values("timestamp"),
        right.sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
        tolerance=tolerance,
        suffixes=("", "_motion"),
    )


def load_error_condition_rows():
    for input_path in INPUT_FILES:
        if input_path.exists():
            print(f"Using error-condition input: {input_path}")
            return pd.read_csv(input_path), input_path

    raise FileNotFoundError(
        "No error-condition input file found. Run "
        "`python src/run_generic_failure_diagnostics.py` first."
    )


def main():
    df, input_path = load_error_condition_rows()

    if "sequence" not in df.columns:
        raise RuntimeError(
            f"No sequence column in: {input_path}\n"
            f"Columns: {df.columns.tolist()}"
        )

    if "timestamp" not in df.columns:
        raise RuntimeError(
            f"No timestamp column in: {input_path}\n"
            f"Columns: {df.columns.tolist()}"
        )

    all_rows = []

    for sequence, seq_df in df.groupby("sequence"):
        motion_path = MOTION_DIR / f"{sequence}_motion.csv"

        if not motion_path.exists():
            print(f"[SKIP] Missing motion file: {motion_path}")
            continue

        motion = pd.read_csv(motion_path)

        if "timestamp" not in motion.columns:
            print(f"[SKIP] No timestamp column in motion file: {motion_path}")
            continue

        # Avoid duplicate sequence columns during merge.
        motion = motion.drop(columns=["sequence"], errors="ignore")

        merged = nearest_merge(seq_df, motion, tolerance=0.05)

        required_motion_cols = [
            "frame_translation_m",
            "translation_speed_mps",
            "frame_rotation_deg",
            "rotation_speed_degps",
        ]

        missing = [col for col in required_motion_cols if col not in merged.columns]
        if missing:
            print(f"[SKIP] Missing merged motion columns for {sequence}: {missing}")
            continue

        merged = merged.dropna(subset=required_motion_cols)

        # Make sure sequence is preserved.
        merged["sequence"] = sequence

        all_rows.append(merged)

        print(f"{sequence}: merged {len(merged)} rows")

    if not all_rows:
        raise RuntimeError("No motion/error rows were merged.")

    combined = pd.concat(all_rows, ignore_index=True)

    # Safety cleanup if old duplicated columns exist.
    if "sequence_x" in combined.columns and "sequence" not in combined.columns:
        combined["sequence"] = combined["sequence_x"]

    combined = combined.drop(
        columns=["sequence_x", "sequence_y", "sequence_motion"],
        errors="ignore",
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT, index=False)

    print(f"\nSaved: {OUT}")
    print("Columns:")
    print(combined.columns.tolist())


if __name__ == "__main__":
    main()