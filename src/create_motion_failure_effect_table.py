from pathlib import Path
import pandas as pd


INPUT = Path("results/error_visual_correlation/motion_binned/motion_binned_failure_analysis.csv")
OUT = Path("results/final_tables/motion_failure_effect_summary.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

rows = []

for (dataset, sequence, method, metric), group in df.groupby(
    ["dataset", "sequence", "method", "visual_metric"],
    dropna=False,
):
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
        "motion_metric": metric,
        "low_bin_mean_error_m": low_error,
        "high_bin_mean_error_m": high_error,
        "error_difference_low_minus_high_m": low_error - high_error,
        "error_ratio_low_over_high": low_error / high_error if high_error != 0 else None,
        "low_bin_samples": int(low["samples"].iloc[0]),
        "high_bin_samples": int(high["samples"].iloc[0]),
    })

summary = pd.DataFrame(rows)
summary = summary.sort_values(["dataset", "sequence", "motion_metric"])
summary.to_csv(OUT, index=False)

print(summary)
print(f"\nSaved: {OUT}")
