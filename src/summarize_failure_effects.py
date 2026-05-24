from pathlib import Path
import pandas as pd


INPUT = Path("results/error_visual_correlation/binned/binned_failure_analysis.csv")
OUT = Path("results/error_visual_correlation/failure_effect_summary.csv")

df = pd.read_csv(INPUT)

difficulty_map = {
    "euroc_mh01": "easy",
    "euroc_mh02": "easy",
    "euroc_mh03": "medium",
    "euroc_mh04": "difficult",
    "euroc_mh05": "difficult",
}

rows = []

for (sequence, metric), group in df.groupby(["sequence", "visual_metric"]):
    group = group.copy()

    low_row = group[group["bin"] == "low"]
    high_row = group[group["bin"] == "high"]

    if low_row.empty or high_row.empty:
        continue

    low_error = float(low_row["error_mean_m"].iloc[0])
    high_error = float(high_row["error_mean_m"].iloc[0])

    rows.append({
        "sequence": sequence,
        "difficulty": difficulty_map.get(sequence, "unknown"),
        "visual_metric": metric,
        "low_bin_mean_error_m": low_error,
        "high_bin_mean_error_m": high_error,
        "error_difference_low_minus_high_m": low_error - high_error,
        "error_ratio_low_over_high": low_error / high_error if high_error != 0 else None,
        "low_bin_samples": int(low_row["samples"].iloc[0]),
        "high_bin_samples": int(high_row["samples"].iloc[0]),
    })

summary = pd.DataFrame(rows)
summary.to_csv(OUT, index=False)

print(summary)
print(f"\nSaved: {OUT}")
