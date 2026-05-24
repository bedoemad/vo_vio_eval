from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/final_tables/failure_effect_summary_final.csv")
OUT_DIR = Path("results/final_figures/failure_effects")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

if df.empty:
    raise RuntimeError("Input failure effect table is empty.")

# Make names cleaner in plots
df["dataset"] = df["dataset"].astype(str)
df["sequence"] = df["sequence"].astype(str)
df["visual_metric"] = df["visual_metric"].astype(str)

# Nice display names
metric_name_map = {
    "blur_score": "Blur Score",
    "texture_score": "ORB Texture Score",
    "fast_texture_score": "FAST Texture Score",
    "brightness_mean": "Brightness",
    "brightness_std": "Contrast",
}

dataset_order = ["EuRoC", "KITTI"]


def prettify_metric(metric):
    return metric_name_map.get(metric, metric.replace("_", " ").title())


def save_effect_plot(sub_df, dataset, metric, output_path):
    """
    Horizontal bar plot:
    x = mean error difference (low - high)
    y = sequence
    Positive means low-quality bin had higher error.
    Negative means high-quality bin had higher error.
    """
    if sub_df.empty:
        return

    # Sort so the plot is easier to read
    sub_df = sub_df.sort_values("error_difference_low_minus_high_m")

    plt.figure(figsize=(10, max(4, 0.6 * len(sub_df))))

    plt.barh(
        sub_df["sequence"],
        sub_df["error_difference_low_minus_high_m"],
    )

    plt.axvline(0, linestyle="--", linewidth=1)

    plt.xlabel("Mean Error Difference (low - high) [m]")
    plt.ylabel("Sequence")
    plt.title(f"{dataset}: Failure Effect of {prettify_metric(metric)}")

    # Annotate values at the end of each bar
    values = sub_df["error_difference_low_minus_high_m"].tolist()
    seqs = sub_df["sequence"].tolist()

    x_range = max(abs(min(values)), abs(max(values))) if values else 1.0
    if x_range == 0:
        x_range = 1.0

    for i, v in enumerate(values):
        offset = 0.02 * x_range
        if v >= 0:
            plt.text(v + offset, i, f"{v:.2f}", va="center", fontsize=9)
        else:
            plt.text(v - offset, i, f"{v:.2f}", va="center", ha="right", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()


def save_ratio_plot(sub_df, dataset, metric, output_path):
    """
    Horizontal bar plot:
    x = error ratio low/high
    y = sequence
    Ratio > 1 means low-quality bin had higher error.
    Ratio < 1 means high-quality bin had higher error.
    """
    if sub_df.empty:
        return

    sub_df = sub_df.dropna(subset=["error_ratio_low_over_high"]).copy()
    if sub_df.empty:
        return

    sub_df = sub_df.sort_values("error_ratio_low_over_high")

    plt.figure(figsize=(10, max(4, 0.6 * len(sub_df))))

    plt.barh(
        sub_df["sequence"],
        sub_df["error_ratio_low_over_high"],
    )

    plt.axvline(1.0, linestyle="--", linewidth=1)

    plt.xlabel("Error Ratio (low / high)")
    plt.ylabel("Sequence")
    plt.title(f"{dataset}: Failure Effect Ratio of {prettify_metric(metric)}")

    values = sub_df["error_ratio_low_over_high"].tolist()

    x_max = max(values) if values else 1.0
    if x_max == 0:
        x_max = 1.0

    for i, v in enumerate(values):
        offset = 0.02 * x_max
        plt.text(v + offset, i, f"{v:.2f}", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()


# Create separate plots for each dataset and each metric
for dataset in dataset_order:
    ds_df = df[df["dataset"] == dataset].copy()
    if ds_df.empty:
        continue

    ds_dir = OUT_DIR / dataset.lower()
    ds_dir.mkdir(parents=True, exist_ok=True)

    for metric in sorted(ds_df["visual_metric"].unique()):
        metric_df = ds_df[ds_df["visual_metric"] == metric].copy()
        if metric_df.empty:
            continue

        save_effect_plot(
            metric_df,
            dataset,
            metric,
            ds_dir / f"failure_effect_{metric}.png",
        )

        save_ratio_plot(
            metric_df,
            dataset,
            metric,
            ds_dir / f"failure_ratio_{metric}.png",
        )

print(f"Saved prettier failure-effect figures to {OUT_DIR}")