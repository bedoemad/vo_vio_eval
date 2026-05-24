from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/error_visual_correlation/failure_effect_summary.csv")
OUT_DIR = Path("results/error_visual_correlation/failure_effect_plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

sequence_order = ["euroc_mh01", "euroc_mh02", "euroc_mh03", "euroc_mh04", "euroc_mh05"]

for metric in df["visual_metric"].unique():
    metric_df = df[df["visual_metric"] == metric].copy()
    metric_df["sequence"] = pd.Categorical(
        metric_df["sequence"],
        categories=sequence_order,
        ordered=True,
    )
    metric_df = metric_df.sort_values("sequence")

    plt.figure()
    plt.bar(
        metric_df["sequence"].astype(str),
        metric_df["error_difference_low_minus_high_m"],
    )
    plt.xlabel("Sequence")
    plt.ylabel("Mean error difference: low bin - high bin (m)")
    plt.title(f"Failure Effect of {metric}")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"failure_effect_{metric}.png", dpi=200)
    plt.close()

print(f"Saved plots to {OUT_DIR}")
