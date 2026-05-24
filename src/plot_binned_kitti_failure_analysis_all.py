from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/error_visual_correlation/kitti_binned_all/kitti_all_binned_failure_analysis.csv")
OUT_DIR = Path("results/error_visual_correlation/kitti_binned_all/plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

bin_order = ["all", "low", "medium", "medium_low", "medium_high", "high"]

for sequence in df["sequence"].unique():
    seq_df_all = df[df["sequence"] == sequence]

    for metric in seq_df_all["visual_metric"].unique():
        seq_df = seq_df_all[seq_df_all["visual_metric"] == metric].copy()

        seq_df["bin"] = pd.Categorical(
            seq_df["bin"],
            categories=bin_order,
            ordered=True,
        )

        seq_df = seq_df.sort_values("bin")

        plt.figure()
        plt.bar(seq_df["bin"].astype(str), seq_df["error_mean_m"])
        plt.xlabel(f"{metric} bin")
        plt.ylabel("Mean aligned position error (m)")
        plt.title(f"{sequence}: Error vs {metric} bin")
        plt.xticks(rotation=25)
        plt.tight_layout()

        out_path = OUT_DIR / f"{sequence}_error_vs_{metric}_bins.png"
        plt.savefig(out_path, dpi=200)
        plt.close()

print(f"Saved plots to {OUT_DIR}")
