from pathlib import Path
import pandas as pd


INPUT = Path("results/error_visual_correlation/kitti_00_orbslam3_kitti_mono.csv")
OUT_DIR = Path("results/error_visual_correlation/kitti_00_binned")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

metrics = [
    "blur_score",
    "texture_score",
    "fast_texture_score",
    "brightness_mean",
    "brightness_std",
]

rows = []


def make_quantile_bins(series, q=4):
    binned = pd.qcut(series, q=q, labels=False, duplicates="drop")
    unique_bins = sorted(binned.dropna().unique())

    if len(unique_bins) == 1:
        label_map = {unique_bins[0]: "all"}
    elif len(unique_bins) == 2:
        label_map = {
            unique_bins[0]: "low",
            unique_bins[1]: "high",
        }
    elif len(unique_bins) == 3:
        label_map = {
            unique_bins[0]: "low",
            unique_bins[1]: "medium",
            unique_bins[2]: "high",
        }
    else:
        label_map = {
            unique_bins[0]: "low",
            unique_bins[1]: "medium_low",
            unique_bins[2]: "medium_high",
            unique_bins[3]: "high",
        }

    return binned.map(label_map)


for metric in metrics:
    temp = df.copy()

    if temp[metric].nunique() < 2:
        print(f"[SKIP] {metric}: not enough unique values")
        continue

    temp["bin"] = make_quantile_bins(temp[metric], q=4)

    grouped = (
        temp.groupby("bin", observed=True)
        .agg(
            samples=("aligned_position_error_m", "count"),
            metric_min=(metric, "min"),
            metric_max=(metric, "max"),
            error_mean_m=("aligned_position_error_m", "mean"),
            error_median_m=("aligned_position_error_m", "median"),
            error_std_m=("aligned_position_error_m", "std"),
            error_max_m=("aligned_position_error_m", "max"),
        )
        .reset_index()
    )

    grouped["visual_metric"] = metric
    grouped["sequence"] = "kitti_00"
    grouped["method"] = "orbslam3_kitti_mono"

    rows.append(grouped)

if not rows:
    raise RuntimeError("No binned KITTI results were created.")

result = pd.concat(rows, ignore_index=True)

bin_order = {
    "all": 0,
    "low": 1,
    "medium": 2,
    "medium_low": 2,
    "medium_high": 3,
    "high": 4,
}

result["bin_order"] = result["bin"].map(bin_order)
result = result.sort_values(["visual_metric", "bin_order"])

out = OUT_DIR / "kitti_00_binned_failure_analysis.csv"
result.to_csv(out, index=False)

print(result)
print(f"\nSaved: {out}")