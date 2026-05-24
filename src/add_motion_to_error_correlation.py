from pathlib import Path

import pandas as pd


MOTION_DIR = Path("results/motion_conditions")
ERROR_DIR = Path("results/error_visual_correlation")

INPUT_FILES = [
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


all_rows = []

for input_path in INPUT_FILES:
    if not input_path.exists():
        print(f"[SKIP] Missing: {input_path}")
        continue

    df = pd.read_csv(input_path)

    if "sequence" not in df.columns:
        print(f"[SKIP] No sequence column in: {input_path}")
        print(df.columns.tolist())
        continue

    for sequence, seq_df in df.groupby("sequence"):
        motion_path = MOTION_DIR / f"{sequence}_motion.csv"

        if not motion_path.exists():
            print(f"[SKIP] Missing motion file: {motion_path}")
            continue

        motion = pd.read_csv(motion_path)

        # Avoid duplicate sequence columns during merge
        motion = motion.drop(columns=["sequence"], errors="ignore")

        merged = nearest_merge(seq_df, motion, tolerance=0.05)

        merged = merged.dropna(subset=[
            "frame_translation_m",
            "translation_speed_mps",
            "frame_rotation_deg",
            "rotation_speed_degps",
        ])

        # Make sure sequence is preserved
        merged["sequence"] = sequence

        all_rows.append(merged)

        print(f"{sequence}: merged {len(merged)} rows")

if not all_rows:
    raise RuntimeError("No motion/error rows were merged.")

combined = pd.concat(all_rows, ignore_index=True)

# Safety cleanup if old duplicated columns exist
if "sequence_x" in combined.columns and "sequence" not in combined.columns:
    combined["sequence"] = combined["sequence_x"]

combined = combined.drop(columns=["sequence_x", "sequence_y", "sequence_motion"], errors="ignore")

combined.to_csv(OUT, index=False)

print(f"\nSaved: {OUT}")
print("Columns:")
print(combined.columns.tolist())