from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/final_tables/diagnostic_effect_summary_final.csv")
OUT_DIR = Path("results/final_figures/diagnostic_effects")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

metric_name_map = {
    "blur_score": "Blur",
    "texture_score": "ORB Texture",
    "fast_texture_score": "FAST Texture",
    "brightness_mean": "Brightness",
    "brightness_std": "Contrast",
    "frame_translation_m": "Frame Translation",
    "translation_speed_mps": "Translation Speed",
    "frame_rotation_deg": "Frame Rotation",
    "rotation_speed_degps": "Rotation Speed",
}


def pretty_metric(x):
    return metric_name_map.get(x, str(x).replace("_", " ").title())


for dataset in ["EuRoC", "KITTI"]:
    ds_df = df[df["dataset"] == dataset].copy()

    if ds_df.empty:
        continue

    # Keep strongest 15 effects for readability
    plot_df = ds_df.sort_values("abs_effect_m", ascending=False).head(15).copy()

    plot_df["label"] = (
        plot_df["sequence"].astype(str)
        + " | "
        + plot_df["condition_group"].astype(str)
        + " | "
        + plot_df["condition_metric"].apply(pretty_metric)
    )

    plot_df = plot_df.sort_values("hard_minus_easy_error_m")

    plt.figure(figsize=(12, max(5, 0.65 * len(plot_df))))
    plt.barh(plot_df["label"], plot_df["hard_minus_easy_error_m"])
    plt.axvline(0, linestyle="--", linewidth=1)

    plt.xlabel("Error Increase in Hard Condition (m)")
    plt.ylabel("Sequence | Group | Condition")
    plt.title(f"{dataset}: Top Diagnostic Failure Factors")

    values = plot_df["hard_minus_easy_error_m"].tolist()
    x_min = min(values)
    x_max = max(values)
    x_range = max(abs(x_min), abs(x_max))
    if x_range == 0:
        x_range = 1.0

    pad = 0.15 * x_range
    plt.xlim(x_min - pad, x_max + pad)

    for i, v in enumerate(values):
        offset = 0.03 * x_range
        if v >= 0:
            plt.text(v + offset, i, f"{v:.2f}", va="center", ha="left", fontsize=9)
        else:
            plt.text(v - offset, i, f"{v:.2f}", va="center", ha="right", fontsize=9)

    plt.tight_layout()
    plt.savefig(OUT_DIR / f"{dataset.lower()}_top_diagnostic_effects.png", dpi=220, bbox_inches="tight")
    plt.close()

print(f"Saved diagnostic effect plots to {OUT_DIR}")

