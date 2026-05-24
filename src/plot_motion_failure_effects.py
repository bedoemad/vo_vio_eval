from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/final_tables/motion_failure_effect_summary.csv")
OUT_DIR = Path("results/final_figures/motion_failure_effects")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

metric_name_map = {
    "frame_translation_m": "Frame-to-Frame Translation",
    "translation_speed_mps": "Translation Speed",
    "frame_rotation_deg": "Frame-to-Frame Rotation",
    "rotation_speed_degps": "Rotation Speed",
}


def pretty(metric):
    return metric_name_map.get(metric, metric.replace("_", " ").title())


# Convert to more intuitive direction:
# positive means high-motion bin has higher error than low-motion bin.
df["high_minus_low_error_m"] = (
    df["high_bin_mean_error_m"] - df["low_bin_mean_error_m"]
)

df["high_over_low_error_ratio"] = (
    df["high_bin_mean_error_m"] / df["low_bin_mean_error_m"]
)


def save_effect_plot(sub_df, dataset, metric, output_path, title_suffix="", clip_outliers=False):
    if sub_df.empty:
        return

    plot_df = sub_df.copy()

    if clip_outliers and len(plot_df) > 4:
        q_low = plot_df["high_minus_low_error_m"].quantile(0.05)
        q_high = plot_df["high_minus_low_error_m"].quantile(0.95)
        plot_df = plot_df[
            (plot_df["high_minus_low_error_m"] >= q_low) &
            (plot_df["high_minus_low_error_m"] <= q_high)
        ].copy()

    if plot_df.empty:
        return

    plot_df = plot_df.sort_values("high_minus_low_error_m")

    values = plot_df["high_minus_low_error_m"].tolist()

    plt.figure(figsize=(11, max(4, 0.65 * len(plot_df))))
    plt.barh(plot_df["sequence"], plot_df["high_minus_low_error_m"])
    plt.axvline(0, linestyle="--", linewidth=1)

    plt.xlabel("Mean Error Increase in High-Motion Bin (m)")
    plt.ylabel("Sequence")
    plt.title(f"{dataset}: Effect of {pretty(metric)}{title_suffix}")

    # ---- Add padding so labels do not touch borders ----
    x_min = min(values) if values else -1
    x_max = max(values) if values else 1
    x_range = max(abs(x_min), abs(x_max))
    if x_range == 0:
        x_range = 1.0

    pad = 0.12 * x_range
    plt.xlim(x_min - pad, x_max + pad)

    # ---- Annotate values with safer offset ----
    for i, v in enumerate(values):
        offset = 0.03 * x_range
        if v >= 0:
            plt.text(v + offset, i, f"{v:.2f}", va="center", ha="left", fontsize=9)
        else:
            plt.text(v - offset, i, f"{v:.2f}", va="center", ha="right", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

def save_ratio_plot(sub_df, dataset, metric, output_path):
    if sub_df.empty:
        return

    plot_df = sub_df.dropna(subset=["high_over_low_error_ratio"]).copy()
    plot_df = plot_df[
        plot_df["high_over_low_error_ratio"].replace([float("inf"), -float("inf")], pd.NA).notna()
    ]

    if plot_df.empty:
        return

    plot_df = plot_df.sort_values("high_over_low_error_ratio")

    values = plot_df["high_over_low_error_ratio"].tolist()

    plt.figure(figsize=(11, max(4, 0.65 * len(plot_df))))
    plt.barh(plot_df["sequence"], plot_df["high_over_low_error_ratio"])
    plt.axvline(1.0, linestyle="--", linewidth=1)

    plt.xlabel("Error Ratio: High-Motion / Low-Motion")
    plt.ylabel("Sequence")
    plt.title(f"{dataset}: Error Ratio for {pretty(metric)}")

    x_min = min(values) if values else 0
    x_max = max(values) if values else 1
    x_range = x_max - x_min
    if x_range == 0:
        x_range = 1.0

    pad = 0.12 * x_range
    plt.xlim(max(0, x_min - pad), x_max + pad)

    for i, v in enumerate(values):
        offset = 0.03 * x_range
        plt.text(v + offset, i, f"{v:.2f}", va="center", ha="left", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close()

for dataset in ["EuRoC", "KITTI"]:
    ds_df = df[df["dataset"] == dataset].copy()

    if ds_df.empty:
        continue

    ds_dir = OUT_DIR / dataset.lower()
    ds_dir.mkdir(parents=True, exist_ok=True)

    for metric in sorted(ds_df["motion_metric"].unique()):
        metric_df = ds_df[ds_df["motion_metric"] == metric].copy()

        save_effect_plot(
            metric_df,
            dataset,
            metric,
            ds_dir / f"motion_effect_high_minus_low_{metric}_full.png",
            title_suffix="",
            clip_outliers=False,
        )

        save_effect_plot(
            metric_df,
            dataset,
            metric,
            ds_dir / f"motion_effect_high_minus_low_{metric}_zoomed.png",
            title_suffix=" (Zoomed, Outliers Removed)",
            clip_outliers=True,
        )

        save_ratio_plot(
            metric_df,
            dataset,
            metric,
            ds_dir / f"motion_ratio_high_over_low_{metric}.png",
        )

print(f"Saved improved motion failure-effect plots to {OUT_DIR}")