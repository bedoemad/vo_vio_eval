from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/comparison_summary.csv")
OUT_DIR = Path("results/benchmark_plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

# Keep only successful real ORB-SLAM3 runs for now
df = df[(df["success"] == True) & (df["method"] == "orbslam3_mono")].copy()

difficulty_map = {
    "euroc_mh01": "easy",
    "euroc_mh02": "easy",
    "euroc_mh03": "medium",
    "euroc_mh04": "difficult",
    "euroc_mh05": "difficult",
}

df["difficulty"] = df["sequence"].map(difficulty_map)

sequence_order = ["euroc_mh01", "euroc_mh02", "euroc_mh03", "euroc_mh04", "euroc_mh05"]
df["sequence"] = pd.Categorical(df["sequence"], categories=sequence_order, ordered=True)
df = df.sort_values("sequence")

df.to_csv("results/orbslam3_mono_benchmark_summary.csv", index=False)

plots = [
    ("ape_rmse_m", "APE RMSE (m)", "ORB-SLAM3 APE RMSE Across EuRoC Sequences", "ape_rmse_by_sequence.png"),
    ("rpe_rmse_m", "RPE RMSE (m)", "ORB-SLAM3 RPE RMSE Across EuRoC Sequences", "rpe_rmse_by_sequence.png"),
    ("runtime_sec", "Runtime (sec)", "ORB-SLAM3 Runtime Across EuRoC Sequences", "runtime_by_sequence.png"),
    ("peak_memory_mb", "Peak Memory (MB)", "ORB-SLAM3 Peak Memory Across EuRoC Sequences", "peak_memory_by_sequence.png"),
    ("avg_memory_mb", "Average Memory (MB)", "ORB-SLAM3 Average Memory Across EuRoC Sequences", "avg_memory_by_sequence.png"),
]

for column, ylabel, title, filename in plots:
    plt.figure()
    plt.bar(df["sequence"].astype(str), df[column])
    plt.xlabel("Sequence")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(OUT_DIR / filename, dpi=200)
    plt.close()

# Accuracy-efficiency scatter
plt.figure()
plt.scatter(df["runtime_sec"], df["ape_rmse_m"], s=80)
for _, row in df.iterrows():
    plt.text(row["runtime_sec"], row["ape_rmse_m"], row["sequence"])
plt.xlabel("Runtime (sec)")
plt.ylabel("APE RMSE (m)")
plt.title("Accuracy-Efficiency Tradeoff")
plt.tight_layout()
plt.savefig(OUT_DIR / "accuracy_efficiency_tradeoff.png", dpi=200)
plt.close()

print(df)
print(f"Saved benchmark summary to results/orbslam3_mono_benchmark_summary.csv")
print(f"Saved plots to {OUT_DIR}")
