from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/final_tables/visual_conditions_summary_final.csv")
OUT_DIR = Path("results/final_figures/visual_conditions")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

if df.empty:
    raise RuntimeError("Visual condition summary table is empty.")

df = df.dropna(subset=["sequence", "dataset"]).copy()
df["sequence"] = df["sequence"].astype(str)
df["dataset"] = df["dataset"].astype(str)

metric_name_map = {
    "blur_mean": "Mean Blur Score",
    "blur_median": "Median Blur Score",
    "texture_mean": "Mean ORB Texture Score",
    "texture_median": "Median ORB Texture Score",
    "fast_texture_mean": "Mean FAST Texture Score",
    "fast_texture_median": "Median FAST Texture Score",
    "brightness_mean": "Mean Brightness",
    "brightness_median": "Median Brightness",
    "contrast_mean": "Mean Contrast",
    "contrast_median": "Median Contrast",
}

plots = [
    ("blur_mean", "Mean Blur Score"),
    ("texture_mean", "Mean ORB Texture Score"),
    ("brightness_mean", "Mean Brightness"),
    ("contrast_mean", "Mean Contrast"),
]

if "fast_texture_mean" in df.columns:
    plots.insert(2, ("fast_texture_mean", "Mean FAST Texture Score"))


def save_horizontal_bar(plot_df, column, title, output_path, ascending=True):
    plot_df = plot_df.dropna(subset=[column]).copy()

    if plot_df.empty:
        print(f"[SKIP] No data for {column}")
        return

    plot_df = plot_df.sort_values(column, ascending=ascending)

    plt.figure(figsize=(10, max(4, 0.55 * len(plot_df))))

    plt.barh(plot_df["sequence"], plot_df[column])

    plt.xlabel(metric_name_map.get(column, column))
    plt.ylabel("Sequence")
    plt.title(title)

    values = plot_df[column].tolist()

    x_max = max(values) if values else 1.0
    if x_max == 0:
        x_max = 1.0

    for i, value in enumerate(values):
        plt.text(
            value + 0.01 * x_max,
            i,
            f"{value:.3g}",
            va="center",
            fontsize=9,
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()


# Separate dataset plots
for dataset in ["EuRoC", "KITTI"]:
    ds_df = df[df["dataset"] == dataset].copy()

    if ds_df.empty:
        continue

    ds_dir = OUT_DIR / dataset.lower()
    ds_dir.mkdir(parents=True, exist_ok=True)

    for column, title in plots:
        if column not in ds_df.columns:
            continue

        save_horizontal_bar(
            ds_df,
            column,
            f"{dataset}: {title}",
            ds_dir / f"{column}.png",
        )


# Combined plots
combined_dir = OUT_DIR / "combined"
combined_dir.mkdir(parents=True, exist_ok=True)

for column, title in plots:
    if column not in df.columns:
        continue

    save_horizontal_bar(
        df,
        column,
        f"Combined: {title}",
        combined_dir / f"{column}.png",
    )


# Create a compact visual-difficulty ranking table
# Lower blur, lower texture, lower brightness, lower contrast can indicate harder visual conditions.
rank_df = df.copy()

rank_cols = []

if "blur_mean" in rank_df.columns:
    rank_df["blur_difficulty_rank"] = rank_df["blur_mean"].rank(ascending=True)
    rank_cols.append("blur_difficulty_rank")

if "texture_mean" in rank_df.columns:
    rank_df["texture_difficulty_rank"] = rank_df["texture_mean"].rank(ascending=True)
    rank_cols.append("texture_difficulty_rank")

if "fast_texture_mean" in rank_df.columns:
    rank_df["fast_texture_difficulty_rank"] = rank_df["fast_texture_mean"].rank(ascending=True)
    rank_cols.append("fast_texture_difficulty_rank")

if "brightness_mean" in rank_df.columns:
    rank_df["brightness_difficulty_rank"] = rank_df["brightness_mean"].rank(ascending=True)
    rank_cols.append("brightness_difficulty_rank")

if "contrast_mean" in rank_df.columns:
    rank_df["contrast_difficulty_rank"] = rank_df["contrast_mean"].rank(ascending=True)
    rank_cols.append("contrast_difficulty_rank")

if rank_cols:
    rank_df["visual_difficulty_score"] = rank_df[rank_cols].mean(axis=1)

    rank_df = rank_df.sort_values("visual_difficulty_score")

    rank_out = OUT_DIR / "visual_difficulty_ranking.csv"
    rank_df[
        ["dataset", "sequence", "visual_difficulty_score"] + rank_cols
    ].to_csv(rank_out, index=False)

    save_horizontal_bar(
        rank_df,
        "visual_difficulty_score",
        "Overall Visual Difficulty Ranking",
        OUT_DIR / "visual_difficulty_ranking.png",
        ascending=True,
    )

print(f"Saved prettier visual-condition figures to {OUT_DIR}")