from pathlib import Path
import pandas as pd


VISUAL_INPUT = Path("results/final_tables/failure_effect_summary_final.csv")
MOTION_INPUT = Path("results/final_tables/motion_failure_effect_summary.csv")

OUT = Path("results/final_tables/diagnostic_effect_summary_final.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

rows = []

# -------------------------
# Visual appearance effects
# -------------------------
if VISUAL_INPUT.exists():
    visual = pd.read_csv(VISUAL_INPUT)

    for _, row in visual.iterrows():
        metric = row["visual_metric"]

        rows.append({
            "dataset": row["dataset"],
            "sequence": row["sequence"],
            "method": row["method"],
            "condition_group": "appearance",
            "condition_metric": metric,
            "hard_condition": "low",
            "easy_condition": "high",
            "hard_condition_mean_error_m": row["low_bin_mean_error_m"],
            "easy_condition_mean_error_m": row["high_bin_mean_error_m"],
            "hard_minus_easy_error_m": row["low_bin_mean_error_m"] - row["high_bin_mean_error_m"],
            "hard_over_easy_error_ratio": (
                row["low_bin_mean_error_m"] / row["high_bin_mean_error_m"]
                if row["high_bin_mean_error_m"] != 0 else None
            ),
            "hard_condition_samples": row["low_bin_samples"],
            "easy_condition_samples": row["high_bin_samples"],
        })


# -------------------------
# Motion effects
# -------------------------
if MOTION_INPUT.exists():
    motion = pd.read_csv(MOTION_INPUT)

    for _, row in motion.iterrows():
        metric = row["motion_metric"]

        # For motion, high speed/rotation is the harder condition.
        rows.append({
            "dataset": row["dataset"],
            "sequence": row["sequence"],
            "method": row["method"],
            "condition_group": "motion",
            "condition_metric": metric,
            "hard_condition": "high",
            "easy_condition": "low",
            "hard_condition_mean_error_m": row["high_bin_mean_error_m"],
            "easy_condition_mean_error_m": row["low_bin_mean_error_m"],
            "hard_minus_easy_error_m": row["high_bin_mean_error_m"] - row["low_bin_mean_error_m"],
            "hard_over_easy_error_ratio": (
                row["high_bin_mean_error_m"] / row["low_bin_mean_error_m"]
                if row["low_bin_mean_error_m"] != 0 else None
            ),
            "hard_condition_samples": row["high_bin_samples"],
            "easy_condition_samples": row["low_bin_samples"],
        })


summary = pd.DataFrame(rows)

if summary.empty:
    raise RuntimeError("No diagnostic effects found.")

summary["abs_effect_m"] = summary["hard_minus_easy_error_m"].abs()

summary = summary.sort_values(
    ["dataset", "abs_effect_m"],
    ascending=[True, False],
)

summary.to_csv(OUT, index=False)

print(summary)
print(f"\nSaved: {OUT}")
