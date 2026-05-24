from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from benchmark_filters import keep_real_benchmark_methods


INPUT = Path("results/final_tables/benchmark_summary_final.csv")
OUT_DIR = Path("results/final_figures/benchmark_clean")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

# Safety filter: final plots should never include smoke-test/demo adapters.
df = keep_real_benchmark_methods(df)

df = df[df["success"] == True].copy()
df = df.dropna(subset=["dataset", "sequence", "method"])

df["dataset"] = df["dataset"].astype(str)
df["sequence"] = df["sequence"].astype(str)
df["method"] = df["method"].astype(str)

metric_name_map = {
    "trajectory_length_m": "Trajectory Length (m)",
    "ape_rmse_m": "APE RMSE (m)",
    "rpe_rmse_m": "RPE RMSE (m)",
    "ape_rmse_percent_of_path": "APE RMSE (% of path length)",
    "runtime_sec": "Runtime (sec)",
    "runtime_per_frame_sec": "Runtime per Frame (sec/frame)",
    "processed_fps": "Processed FPS",
    "runtime_per_meter_sec": "Runtime per Meter (sec/m)",
    "peak_memory_mb": "Peak Memory (MB)",
    "avg_memory_mb": "Average Memory (MB)",
}

plots = [
    "ape_rmse_m",
    "rpe_rmse_m",
    "ape_rmse_percent_of_path",
    "runtime_sec",
    "runtime_per_frame_sec",
    "processed_fps",
    "peak_memory_mb",
    "avg_memory_mb",
]


def save_grouped_bar(dataset_df, dataset, metric):
    plot_df = dataset_df.dropna(subset=[metric]).copy()

    if plot_df.empty:
        print(f"[SKIP] {dataset} {metric}: no data")
        return

    sequences = sorted(plot_df["sequence"].unique())
    methods = sorted(plot_df["method"].unique())

    x = np.arange(len(sequences))
    width = 0.8 / max(len(methods), 1)

    plt.figure(figsize=(max(10, 0.8 * len(sequences)), 6))

    for i, method in enumerate(methods):
        values = []

        for seq in sequences:
            row = plot_df[
                (plot_df["sequence"] == seq)
                & (plot_df["method"] == method)
            ]

            if row.empty:
                values.append(np.nan)
            else:
                values.append(float(row[metric].iloc[0]))

        offset = (i - (len(methods) - 1) / 2) * width
        plt.bar(x + offset, values, width, label=method)

    plt.xticks(x, sequences, rotation=45, ha="right")
    plt.ylabel(metric_name_map.get(metric, metric))
    plt.xlabel("Sequence")
    plt.title(f"{dataset}: {metric_name_map.get(metric, metric)}")
    plt.legend()
    plt.tight_layout()

    dataset_dir = OUT_DIR / dataset.lower()
    dataset_dir.mkdir(parents=True, exist_ok=True)

    plt.savefig(dataset_dir / f"{metric}.png", dpi=220, bbox_inches="tight")
    plt.close()


for dataset in sorted(df["dataset"].unique()):
    dataset_df = df[df["dataset"] == dataset].copy()

    for metric in plots:
        if metric in dataset_df.columns:
            save_grouped_bar(dataset_df, dataset, metric)


# Clean accuracy-efficiency tradeoff without value labels
trade_metrics = ["runtime_per_frame_sec", "ape_rmse_m"]

if all(c in df.columns for c in trade_metrics):
    trade_df = df.dropna(subset=trade_metrics).copy()

    for dataset in sorted(trade_df["dataset"].unique()):
        ds = trade_df[trade_df["dataset"] == dataset].copy()

        if ds.empty:
            continue

        plt.figure(figsize=(9, 6))

        for method in sorted(ds["method"].unique()):
            sub = ds[ds["method"] == method]
            plt.scatter(
                sub["runtime_per_frame_sec"],
                sub["ape_rmse_m"],
                s=70,
                label=method,
            )

            for _, row in sub.iterrows():
                plt.annotate(
                    row["sequence"],
                    (row["runtime_per_frame_sec"], row["ape_rmse_m"]),
                    textcoords="offset points",
                    xytext=(5, 5),
                    fontsize=8,
                )

        plt.xlabel("Runtime per Frame (sec/frame)")
        plt.ylabel("APE RMSE (m)")
        plt.title(f"{dataset}: Accuracy vs Runtime per Frame")
        plt.legend()

        if dataset == "KITTI":
            plt.yscale("log")

        plt.tight_layout()
        plt.savefig(
            OUT_DIR / dataset.lower() / "accuracy_vs_runtime_per_frame.png",
            dpi=220,
            bbox_inches="tight",
        )
        plt.close()

print(f"Saved clean benchmark figures to {OUT_DIR}")