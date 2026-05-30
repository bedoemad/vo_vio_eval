from pathlib import Path
import json
import re

import matplotlib.pyplot as plt
import pandas as pd


INPUT_CSV = Path("results/final_tables/benchmark_summary_final.csv")
OUTPUT_ROOT = Path("results/final_figures/benchmark_clean")
METHODS_CONFIG = Path("configs/methods.json")


METRICS = {
    # Legacy/default columns. These correspond to Sim(3) in the current summary.
    "ape_rmse_m": "APE Sim(3) RMSE (m)",
    "rpe_rmse_m": "RPE Sim(3) RMSE (m)",

    # Explicit alignment-aware metrics.
    "ape_sim3_rmse_m": "APE Sim(3) RMSE (m)",
    "rpe_sim3_rmse_m": "RPE Sim(3) RMSE (m)",
    "ape_se3_rmse_m": "APE SE(3) RMSE (m)",
    "rpe_se3_rmse_m": "RPE SE(3) RMSE (m)",

    # Normalized accuracy and efficiency.
    "ape_rmse_percent_of_path": "APE Sim(3) RMSE (% of path)",
    "runtime_sec": "Runtime (s)",
    "runtime_per_frame_sec": "Runtime per Frame (s)",
    "processed_fps": "Processed FPS",
    "runtime_per_meter_sec": "Runtime per Meter (s/m)",
    "peak_memory_mb": "Peak Memory (MB)",
    "avg_memory_mb": "Average Memory (MB)",
}


HIGHER_IS_BETTER = {
    "processed_fps",
}


TOKEN_LABELS = {
    "orbslam3": "ORB-SLAM3",
    "orbslam": "ORB-SLAM",
    "dpvo": "DPVO",
    "droidslam": "DROID-SLAM",
    "dso": "DSO",
    "svo": "SVO",
    "openvins": "OpenVINS",
    "msckf": "MSCKF",
    "vins": "VINS",
    "vio": "VIO",
    "vo": "VO",
    "slam": "SLAM",
    "mono": "Mono",
    "monocular": "Monocular",
    "stereo": "Stereo",
    "rgbd": "RGB-D",
    "rgb": "RGB",
    "imu": "IMU",
    "inertial": "Inertial",
    "euroc": "EuRoC",
    "kitti": "KITTI",
}


def auto_method_label(method_name: str) -> str:
    """
    Creates a readable label for any method name.

    Example:
        orbslam3_euroc_mono_inertial -> ORB-SLAM3 Mono Inertial
        my_new_vio_model             -> My New VIO Model
    """
    cleaned = method_name.strip()

    # Remove dataset tokens from labels because dataset is already shown separately.
    parts = re.split(r"[_\-\s]+", cleaned)
    readable_parts = []

    for part in parts:
        key = part.lower()

        if key in {"euroc", "kitti"}:
            continue

        readable_parts.append(TOKEN_LABELS.get(key, part.title()))

    if not readable_parts:
        return method_name

    label = " ".join(readable_parts)

    # Small cleanup for common labels.
    label = label.replace("Mono Inertial", "Mono-Inertial")

    return label


def load_method_labels() -> dict[str, str]:
    """
    Loads optional display labels from configs/methods.json.

    If a method has one of these optional fields, it will be used:
        display_name
        plot_label
        label

    Otherwise, a readable label is generated automatically.
    """
    labels = {}

    if METHODS_CONFIG.exists():
        with METHODS_CONFIG.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for method in data.get("methods", []):
            name = method.get("name")

            if not name:
                continue

            display_name = (
                method.get("display_name")
                or method.get("plot_label")
                or method.get("label")
                or auto_method_label(name)
            )

            labels[name] = display_name

    return labels


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def clean_dataset_name(dataset: str) -> str:
    return str(dataset).strip().lower().replace(" ", "_")


def dynamic_figsize(num_sequences: int, num_methods: int) -> tuple[float, float]:
    width = max(7.0, min(16.0, 2.8 + num_sequences * max(0.8, num_methods * 0.35)))
    height = max(4.2, min(8.0, 3.8 + num_methods * 0.25))
    return width, height


def save_current_plot(output_path: Path) -> None:
    ensure_dir(output_path.parent)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_grouped_metric(df: pd.DataFrame, metric: str, title: str, output_path: Path) -> None:
    if metric not in df.columns:
        print(f"[SKIP] Missing metric column: {metric}")
        return

    data = df.copy()

    if "success" in data.columns:
        data = data[data["success"] == True]

    data = data.dropna(subset=[metric])

    if data.empty:
        print(f"[SKIP] No valid data for metric: {metric}")
        return

    pivot = data.pivot_table(
        index="sequence",
        columns="method_label",
        values=metric,
        aggfunc="mean",
    )

    pivot = pivot.sort_index()

    figsize = dynamic_figsize(
        num_sequences=len(pivot.index),
        num_methods=len(pivot.columns),
    )

    ax = pivot.plot(kind="bar", figsize=figsize, width=0.82)

    direction = "Higher is better" if metric in HIGHER_IS_BETTER else "Lower is better"

    ax.set_title(f"{title}\n{direction}", fontsize=12, fontweight="bold")
    ax.set_xlabel("Sequence")
    ax.set_ylabel(title)
    ax.grid(axis="y", alpha=0.3)

    if len(pivot.index) > 5:
        ax.tick_params(axis="x", rotation=35)
    else:
        ax.tick_params(axis="x", rotation=0)

    ax.legend(
        title="Method",
        fontsize=8,
        title_fontsize=9,
        loc="best",
        frameon=True,
    )

    save_current_plot(output_path)


def plot_accuracy_efficiency(df: pd.DataFrame, output_path: Path) -> None:
    required = {"ape_rmse_m", "runtime_per_frame_sec", "method_label"}

    if not required.issubset(df.columns):
        print("[SKIP] Missing columns for accuracy-efficiency plot")
        return

    data = df.copy()

    if "success" in data.columns:
        data = data[data["success"] == True]

    data = data.dropna(subset=["ape_rmse_m", "runtime_per_frame_sec"])

    if data.empty:
        print("[SKIP] No valid data for accuracy-efficiency plot")
        return

    methods = list(data["method_label"].dropna().unique())

    plt.figure(figsize=(8.5, 5.2))

    for method in methods:
        subset = data[data["method_label"] == method]

        plt.scatter(
            subset["runtime_per_frame_sec"],
            subset["ape_rmse_m"],
            label=method,
            s=55,
            alpha=0.85,
        )

        if len(data) <= 20:
            for _, row in subset.iterrows():
                plt.annotate(
                    str(row.get("sequence", "")),
                    (
                        row["runtime_per_frame_sec"],
                        row["ape_rmse_m"],
                    ),
                    fontsize=7,
                    xytext=(4, 4),
                    textcoords="offset points",
                )

    plt.title("Accuracy vs Runtime per Frame\nLower-left is better", fontsize=12, fontweight="bold")
    plt.xlabel("Runtime per Frame (s)")
    plt.ylabel("APE RMSE (m)")
    plt.grid(alpha=0.3)
    plt.legend(title="Method", fontsize=8, title_fontsize=9)

    save_current_plot(output_path)


def add_method_labels(df: pd.DataFrame) -> pd.DataFrame:
    labels = load_method_labels()

    df = df.copy()
    df["method_label"] = df["method"].map(
        lambda name: labels.get(name, auto_method_label(str(name)))
    )

    return df


def generate_for_dataset(df: pd.DataFrame, dataset_name: str, output_dir: Path) -> None:
    ensure_dir(output_dir)

    for metric, title in METRICS.items():
        output_path = output_dir / f"{metric}.png"
        plot_grouped_metric(df, metric, title, output_path)

    plot_accuracy_efficiency(
        df,
        output_dir / "accuracy_vs_runtime_per_frame.png",
    )


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing benchmark table: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)

    if df.empty:
        raise RuntimeError(f"Benchmark table is empty: {INPUT_CSV}")

    if "method" not in df.columns:
        raise RuntimeError("Benchmark table must contain a 'method' column.")

    if "sequence" not in df.columns:
        raise RuntimeError("Benchmark table must contain a 'sequence' column.")

    df = add_method_labels(df)

    ensure_dir(OUTPUT_ROOT)

    # Combined plots across all datasets.
    generate_for_dataset(df, "combined", OUTPUT_ROOT / "combined")

    # Dataset-specific plots are generated automatically for any dataset name.
    if "dataset" in df.columns:
        for dataset_name, dataset_df in df.groupby("dataset"):
            clean_name = clean_dataset_name(dataset_name)
            generate_for_dataset(dataset_df, str(dataset_name), OUTPUT_ROOT / clean_name)
    else:
        print("[WARN] No dataset column found; only combined plots generated.")

    print(f"Saved benchmark figures to {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()