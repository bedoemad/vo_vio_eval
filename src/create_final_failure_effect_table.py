from pathlib import Path
import pandas as pd


EUROC_INPUT = Path("results/error_visual_correlation/binned/binned_failure_analysis.csv")
KITTI_INPUT = Path("results/error_visual_correlation/kitti_binned_all/kitti_all_binned_failure_analysis.csv")

OUT = Path("results/final_tables/failure_effect_summary_final.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

tables = []

if EUROC_INPUT.exists():
    euroc = pd.read_csv(EUROC_INPUT)
    euroc["dataset"] = "EuRoC"

    # Important fix: older EuRoC binned table may not have method column
    if "method" not in euroc.columns:
        euroc["method"] = "orbslam3_mono"

    tables.append(euroc)

if KITTI_INPUT.exists():
    kitti = pd.read_csv(KITTI_INPUT)
    kitti["dataset"] = "KITTI"

    if "method" not in kitti.columns:
        kitti["method"] = "orbslam3_kitti_mono"

    tables.append(kitti)

if not tables:
    raise RuntimeError("No binned failure analysis files found.")

df = pd.concat(tables, ignore_index=True)

# Extra safety: fill missing methods
df["method"] = df["method"].fillna(
    df["dataset"].map({
        "EuRoC": "orbslam3_mono",
        "KITTI": "orbslam3_kitti_mono",
    })
)

rows = []

for (dataset, sequence, method, metric), group in df.groupby(
    ["dataset", "sequence", "method", "visual_metric"],
    dropna=False,
):
    group = group.copy()

    low = group[group["bin"] == "low"]
    high = group[group["bin"] == "high"]

    if low.empty or high.empty:
        continue

    low_error = float(low["error_mean_m"].iloc[0])
    high_error = float(high["error_mean_m"].iloc[0])

    rows.append({
        "dataset": dataset,
        "sequence": sequence,
        "method": method,
        "visual_metric": metric,
        "low_bin_mean_error_m": low_error,
        "high_bin_mean_error_m": high_error,
        "error_difference_low_minus_high_m": low_error - high_error,
        "error_ratio_low_over_high": low_error / high_error if high_error != 0 else None,
        "low_bin_samples": int(low["samples"].iloc[0]),
        "high_bin_samples": int(high["samples"].iloc[0]),
    })

summary = pd.DataFrame(rows)
summary = summary.sort_values(["dataset", "sequence", "visual_metric"])
summary.to_csv(OUT, index=False)

print(summary)
print(f"\nSaved: {OUT}")