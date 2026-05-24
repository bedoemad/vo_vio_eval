from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/error_visual_correlation/kitti_00_binned/kitti_00_binned_failure_analysis.csv")
OUT_DIR = Path("results/error_visual_correlation/kitti_00_binned/plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

bin_order = ["all", "low", "medium",  "medium_low", "medium_high", "high"]

for metric in df["visual_metric"].unique():
    metric_df = df[df["visual_metric"] == metric].copy()
    metric_df["bin"] = pd.Categorical(metric_df["bin"], categories=bin_order, ordered=True)
    metric_df = metric_df.sort_values("bin")

    plt.figure()
    plt.bar(metric_df["bin"].astype(str), metric_df["error_mean_m"])
    plt.xlabel(f"{metric} bin")
    plt.ylabel("Mean aligned position error (m)")
    plt.title(f"KITTI 00: Error vs {metric} bin")
    plt.xticks(rotation=25)
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"kitti_00_error_vs_{metric}_bins.png", dpi=200)
    plt.close()

print(f"Saved plots to {OUT_DIR}")
