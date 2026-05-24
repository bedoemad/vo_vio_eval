from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/final_tables/all_methods_condition_effect_summary.csv")
OUT_DIR = Path("results/final_figures/generic_failure_diagnostics_clean")
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


def pretty_metric(metric):
    return metric_name_map.get(metric, str(metric).replace("_", " ").title())


for (dataset, method), group in df.groupby(["dataset", "method"]):
    out_dir = OUT_DIR / dataset.lower() / method
    out_dir.mkdir(parents=True, exist_ok=True)

    # Keep only strongest 10 effects to avoid clutter
    plot_df = group.sort_values("abs_effect_m", ascending=False).head(10).copy()

    plot_df["label"] = (
        plot_df["sequence"].astype(str)
        + " | "
        + plot_df["condition_group"].astype(str)
        + " | "
        + plot_df["condition_metric"].apply(pretty_metric)
    )

    plot_df = plot_df.sort_values("hard_minus_easy_error_m")

    plt.figure(figsize=(12, max(5, 0.7 * len(plot_df))))

    plt.barh(plot_df["label"], plot_df["hard_minus_easy_error_m"])
    plt.axvline(0, linestyle="--", linewidth=1)

    plt.xlabel("Error Increase in Hard Condition (m)")
    plt.ylabel("Sequence | Condition Group | Metric")
    plt.title(f"{dataset} / {method}: Top Diagnostic Failure Factors")

    plt.tight_layout()

    plt.savefig(
        out_dir / "top_diagnostic_failure_factors.png",
        dpi=220,
        bbox_inches="tight",
    )

    plt.close()

print(f"Saved clean generic diagnostic plots to {OUT_DIR}")