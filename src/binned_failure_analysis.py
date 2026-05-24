from pathlib import Path

import pandas as pd


INPUT = Path("results/error_visual_correlation/all_sequences_orbslam3_mono.csv")
OUT_DIR = Path("results/error_visual_correlation/binned")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

metrics = [
    "blur_score",
    "texture_score",
    "brightness_mean",
    "brightness_std",
]

all_binned = []


def make_quantile_bins(series, q=4):
    """
    Creates quantile bins safely even when duplicate bin edges exist.
    Returns integer bin IDs first, then maps them to readable labels.
    """
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


for sequence, seq_df in df.groupby("sequence"):
    for metric in metrics:
        temp = seq_df.copy()

        if temp[metric].nunique() < 2:
            print(f"[SKIP] {sequence} {metric}: not enough unique values")
            continue

        temp["bin"] = make_quantile_bins(temp[metric], q=4)

        grouped = (
            temp.groupby("bin", observed=True)
            .agg(
                sequence=("sequence", "first"),
                visual_metric=(metric, lambda x: metric),
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

        all_binned.append(grouped)

if not all_binned:
    raise RuntimeError("No binned results were created. Check input data.")

result = pd.concat(all_binned, ignore_index=True)

bin_order = {
    "all": 0,
    "low": 1,
    "medium": 2,
    "medium_low": 2,
    "medium_high": 3,
    "high": 4,
}

result["bin_order"] = result["bin"].map(bin_order)
result = result.sort_values(["sequence", "visual_metric", "bin_order"])

out_path = OUT_DIR / "binned_failure_analysis.csv"
result.to_csv(out_path, index=False)

print(result)
print(f"\nSaved: {out_path}")