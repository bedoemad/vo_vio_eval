from pathlib import Path
import pandas as pd


INPUT_DIR = Path("results/visual_conditions")
OUT = Path("results/final_tables/visual_conditions_summary_final.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

rows = []

for csv_path in sorted(INPUT_DIR.glob("*_cam0.csv")):
    df = pd.read_csv(csv_path)
    sequence = csv_path.stem.replace("_cam0", "")

    dataset = "KITTI" if sequence.startswith("kitti") else "EuRoC"

    row = {
        "dataset": dataset,
        "sequence": sequence,
        "frames": len(df),
        "blur_mean": df["blur_score"].mean(),
        "blur_median": df["blur_score"].median(),
        "blur_min": df["blur_score"].min(),
        "blur_max": df["blur_score"].max(),
        "texture_mean": df["texture_score"].mean(),
        "texture_median": df["texture_score"].median(),
        "texture_min": df["texture_score"].min(),
        "texture_max": df["texture_score"].max(),
        "brightness_mean": df["brightness_mean"].mean(),
        "brightness_median": df["brightness_mean"].median(),
        "contrast_mean": df["brightness_std"].mean(),
        "contrast_median": df["brightness_std"].median(),
    }

    if "fast_texture_score" in df.columns:
        row["fast_texture_mean"] = df["fast_texture_score"].mean()
        row["fast_texture_median"] = df["fast_texture_score"].median()
        row["fast_texture_min"] = df["fast_texture_score"].min()
        row["fast_texture_max"] = df["fast_texture_score"].max()

    rows.append(row)

summary = pd.DataFrame(rows)
summary = summary.sort_values(["dataset", "sequence"])
summary.to_csv(OUT, index=False)

print(summary)
print(f"\nSaved: {OUT}")
