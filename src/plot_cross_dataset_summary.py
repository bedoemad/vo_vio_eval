from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/comparison_summary.csv")
OUT_DIR = Path("results/cross_dataset_plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

df = df[df["success"] == True].copy()

df["dataset"] = df["sequence"].apply(
    lambda x: "KITTI" if str(x).startswith("kitti") else "EuRoC"
)

df["label"] = df["method"] + "\n" + df["sequence"]

plots = [
    (
        "ape_rmse_m",
        "APE RMSE (m)",
        "Absolute Trajectory Accuracy Across Datasets",
        "ape_rmse_cross_dataset.png",
    ),
    (
        "ape_rmse_percent_of_path",
        "APE RMSE (% of path length)",
        "Normalized Accuracy Across Datasets",
        "normalized_ape_cross_dataset.png",
    ),
    (
        "runtime_sec",
        "Runtime (sec)",
        "Runtime Across Datasets",
        "runtime_cross_dataset.png",
    ),
    (
        "peak_memory_mb",
        "Peak Memory (MB)",
        "Peak Memory Across Datasets",
        "peak_memory_cross_dataset.png",
    ),
]

for column, ylabel, title, filename in plots:
    plot_df = df.dropna(subset=[column]).copy()

    plt.figure()
    plt.bar(plot_df["label"], plot_df[column])
    plt.xlabel("Method / Sequence")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_DIR / filename, dpi=200)
    plt.close()

print(f"Saved plots to {OUT_DIR}")
