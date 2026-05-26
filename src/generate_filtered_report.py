from __future__ import annotations

import argparse
import html
import json
import os
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


FINAL_TABLES_DIR = Path("results/final_tables")
BENCHMARK_TABLE = FINAL_TABLES_DIR / "benchmark_summary_final.csv"
VISUAL_TABLE = FINAL_TABLES_DIR / "visual_conditions_summary_final.csv"
METHODS_CONFIG = Path("configs/methods.json")


TOKEN_LABELS = {
    "orbslam3": "ORB-SLAM3",
    "orbslam": "ORB-SLAM",
    "dpvo": "DPVO",
    "droidslam": "DROID-SLAM",
    "openvins": "OpenVINS",
    "vins": "VINS",
    "msckf": "MSCKF",
    "vio": "VIO",
    "vo": "VO",
    "slam": "SLAM",
    "mono": "Mono",
    "monocular": "Monocular",
    "stereo": "Stereo",
    "rgbd": "RGB-D",
    "imu": "IMU",
    "inertial": "Inertial",
    "euroc": "EuRoC",
    "kitti": "KITTI",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a filtered VO/VIO dashboard report."
    )

    parser.add_argument(
        "--dataset",
        default=None,
        help="Dataset filter, for example: EuRoC or KITTI.",
    )

    parser.add_argument(
        "--methods",
        nargs="*",
        default=None,
        help="Optional method names to include.",
    )

    parser.add_argument(
        "--sequences",
        nargs="*",
        default=None,
        help="Optional sequence names to include.",
    )

    parser.add_argument(
        "--name",
        default="filtered_report",
        help="Report output folder name under results/reports/.",
    )

    return parser.parse_args()


def safe(value) -> str:
    return html.escape(str(value))


def fmt(value, digits: int = 3) -> str:
    if value is None or pd.isna(value):
        return "—"

    if isinstance(value, float):
        return f"{value:.{digits}f}"

    return str(value)


def auto_method_label(method_name: str) -> str:
    parts = re.split(r"[_\-\s]+", str(method_name).strip())
    readable = []

    for part in parts:
        key = part.lower()

        if key in {"euroc", "kitti"}:
            continue

        readable.append(TOKEN_LABELS.get(key, part.title()))

    label = " ".join(readable) if readable else str(method_name)
    label = label.replace("Mono Inertial", "Mono-Inertial")

    return label


def load_method_labels() -> dict[str, str]:
    labels = {}

    if not METHODS_CONFIG.exists():
        return labels

    with METHODS_CONFIG.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for method in data.get("methods", []):
        name = method.get("name")

        if not name:
            continue

        labels[name] = (
            method.get("display_name")
            or method.get("plot_label")
            or method.get("label")
            or auto_method_label(name)
        )

    return labels


def add_method_labels(df: pd.DataFrame) -> pd.DataFrame:
    labels = load_method_labels()

    df = df.copy()
    df["method_label"] = df["method"].map(
        lambda name: labels.get(name, auto_method_label(name))
    )

    return df


def filter_dataframe(
    df: pd.DataFrame,
    dataset: str | None,
    methods: list[str] | None,
    sequences: list[str] | None,
) -> pd.DataFrame:
    out = df.copy()

    if dataset and "dataset" in out.columns:
        out = out[out["dataset"].astype(str).str.lower() == dataset.lower()]

    if methods and "method" in out.columns:
        out = out[out["method"].isin(methods)]

    if sequences and "sequence" in out.columns:
        out = out[out["sequence"].isin(sequences)]

    return out


def rel(path: Path, report_path: Path) -> str:
    return os.path.relpath(path.resolve(), report_path.parent.resolve()).replace("\\", "/")


def metric_card(title: str, value: str, subtitle: str) -> str:
    return f"""
    <div class="metric-card">
      <div class="metric-title">{safe(title)}</div>
      <div class="metric-value">{safe(value)}</div>
      <div class="metric-subtitle">{safe(subtitle)}</div>
    </div>
    """


def overview_cards(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class='empty'>No matching benchmark rows found.</p>"

    runs = len(df)
    methods = df["method"].nunique() if "method" in df.columns else 0
    sequences = df["sequence"].nunique() if "sequence" in df.columns else 0
    successful = int(df["success"].sum()) if "success" in df.columns else runs

    best_ape = "—"
    if "ape_rmse_m" in df.columns and df["ape_rmse_m"].notna().any():
        best_ape = f"{df['ape_rmse_m'].min():.4f} m"

    median_fps = "—"
    if "processed_fps" in df.columns and df["processed_fps"].notna().any():
        median_fps = f"{df['processed_fps'].median():.2f}"

    cards = [
        metric_card("Runs", str(runs), "Filtered result rows"),
        metric_card("Successful", f"{successful}/{runs}", "Completed evaluations"),
        metric_card("Methods", str(methods), "Included systems"),
        metric_card("Sequences", str(sequences), "Included sequences"),
        metric_card("Best APE", best_ape, "Lower is better"),
        metric_card("Median FPS", median_fps, "Higher is better"),
    ]

    return "<div class='metric-grid'>" + "\n".join(cards) + "</div>"


def ranking_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class='empty'>No ranking data available.</p>"

    data = df.copy()

    if "success" in data.columns:
        data = data[data["success"] == True]

    if data.empty:
        return "<p class='empty'>No successful runs available.</p>"

    grouped = data.groupby("method_label").agg(
        runs=("sequence", "count"),
        mean_ape=("ape_rmse_m", "mean"),
        median_ape=("ape_rmse_m", "median"),
        mean_rpe=("rpe_rmse_m", "mean"),
        mean_fps=("processed_fps", "mean"),
        runtime_per_frame=("runtime_per_frame_sec", "mean"),
        peak_memory=("peak_memory_mb", "mean"),
    ).reset_index()

    grouped = grouped.sort_values("mean_ape", ascending=True)

    rows = []
    for rank, (_, row) in enumerate(grouped.iterrows(), start=1):
        rows.append(
            f"""
            <tr>
              <td class="rank">{rank}</td>
              <td><strong>{safe(row["method_label"])}</strong></td>
              <td>{fmt(row["runs"], 0)}</td>
              <td>{fmt(row["mean_ape"], 4)}</td>
              <td>{fmt(row["median_ape"], 4)}</td>
              <td>{fmt(row["mean_rpe"], 4)}</td>
              <td>{fmt(row["mean_fps"], 2)}</td>
              <td>{fmt(row["runtime_per_frame"], 4)}</td>
              <td>{fmt(row["peak_memory"], 1)}</td>
            </tr>
            """
        )

    return f"""
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Method</th>
            <th>Runs</th>
            <th>Mean APE RMSE (m)</th>
            <th>Median APE RMSE (m)</th>
            <th>Mean RPE RMSE (m)</th>
            <th>Mean FPS</th>
            <th>Runtime/frame (s)</th>
            <th>Peak memory (MB)</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


def sequence_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class='empty'>No sequence results available.</p>"

    data = df.copy()

    sort_cols = [c for c in ["sequence", "method_label"] if c in data.columns]
    if sort_cols:
        data = data.sort_values(sort_cols)

    rows = []
    for _, row in data.iterrows():
        status = "OK" if bool(row.get("success", True)) else "FAIL"

        rows.append(
            f"""
            <tr>
              <td>{safe(row.get("dataset", "—"))}</td>
              <td>{safe(row.get("sequence", "—"))}</td>
              <td>{safe(row.get("difficulty", "—"))}</td>
              <td>{safe(row.get("method_label", "—"))}</td>
              <td>{status}</td>
              <td>{fmt(row.get("ape_rmse_m"), 4)}</td>
              <td>{fmt(row.get("rpe_rmse_m"), 4)}</td>
              <td>{fmt(row.get("ape_rmse_percent_of_path"), 3)}</td>
              <td>{fmt(row.get("runtime_sec"), 2)}</td>
              <td>{fmt(row.get("runtime_per_frame_sec"), 4)}</td>
              <td>{fmt(row.get("processed_fps"), 2)}</td>
              <td>{fmt(row.get("peak_memory_mb"), 1)}</td>
            </tr>
            """
        )

    return f"""
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Dataset</th>
            <th>Sequence</th>
            <th>Difficulty</th>
            <th>Method</th>
            <th>Status</th>
            <th>APE RMSE (m)</th>
            <th>RPE RMSE (m)</th>
            <th>APE (% path)</th>
            <th>Runtime (s)</th>
            <th>Runtime/frame (s)</th>
            <th>FPS</th>
            <th>Peak memory (MB)</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


def visual_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p class='empty'>No visual-condition data available for this filter.</p>"

    columns = [
        "dataset",
        "sequence",
        "frames",
        "blur_mean",
        "texture_mean",
        "brightness_mean",
        "contrast_mean",
        "fast_texture_mean",
    ]

    columns = [c for c in columns if c in df.columns]
    data = df[columns].copy()

    if "sequence" in data.columns:
        data = data.sort_values("sequence")

    rows = []
    for _, row in data.iterrows():
        rows.append(
            f"""
            <tr>
              <td>{safe(row.get("dataset", "—"))}</td>
              <td>{safe(row.get("sequence", "—"))}</td>
              <td>{fmt(row.get("frames"), 0)}</td>
              <td>{fmt(row.get("blur_mean"), 2)}</td>
              <td>{fmt(row.get("texture_mean"), 2)}</td>
              <td>{fmt(row.get("brightness_mean"), 2)}</td>
              <td>{fmt(row.get("contrast_mean"), 2)}</td>
              <td>{fmt(row.get("fast_texture_mean"), 2)}</td>
            </tr>
            """
        )

    return f"""
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Dataset</th>
            <th>Sequence</th>
            <th>Frames</th>
            <th>Blur</th>
            <th>Texture</th>
            <th>Brightness</th>
            <th>Contrast</th>
            <th>FAST Texture</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    """


def save_plot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=170, bbox_inches="tight")
    plt.close()


def plot_bar(df: pd.DataFrame, metric: str, ylabel: str, output_path: Path) -> None:
    if df.empty or metric not in df.columns:
        return

    data = df.copy()

    if "success" in data.columns:
        data = data[data["success"] == True]

    data = data.dropna(subset=[metric])

    if data.empty:
        return

    pivot = data.pivot_table(
        index="sequence",
        columns="method_label",
        values=metric,
        aggfunc="mean",
    ).sort_index()

    if pivot.empty:
        return

    width = max(7, min(14, 3 + len(pivot.index) * max(0.8, 0.35 * len(pivot.columns))))
    height = max(4, min(7, 3.5 + 0.25 * len(pivot.columns)))

    ax = pivot.plot(kind="bar", figsize=(width, height), width=0.82)
    ax.set_title(ylabel, fontweight="bold")
    ax.set_xlabel("Sequence")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)

    if len(pivot.index) > 5:
        ax.tick_params(axis="x", rotation=35)
    else:
        ax.tick_params(axis="x", rotation=0)

    ax.legend(title="Method", fontsize=8, title_fontsize=9)
    save_plot(output_path)


def plot_accuracy_runtime(df: pd.DataFrame, output_path: Path) -> None:
    required = {"ape_rmse_m", "runtime_per_frame_sec", "method_label"}

    if df.empty or not required.issubset(df.columns):
        return

    data = df.copy()

    if "success" in data.columns:
        data = data[data["success"] == True]

    data = data.dropna(subset=["ape_rmse_m", "runtime_per_frame_sec"])

    if data.empty:
        return

    plt.figure(figsize=(8, 5))

    for method, subset in data.groupby("method_label"):
        plt.scatter(
            subset["runtime_per_frame_sec"],
            subset["ape_rmse_m"],
            label=method,
            s=60,
            alpha=0.85,
        )

        if len(data) <= 20:
            for _, row in subset.iterrows():
                plt.annotate(
                    str(row.get("sequence", "")),
                    (row["runtime_per_frame_sec"], row["ape_rmse_m"]),
                    fontsize=7,
                    xytext=(4, 4),
                    textcoords="offset points",
                )

    plt.title("Accuracy vs Runtime per Frame\nLower-left is better", fontweight="bold")
    plt.xlabel("Runtime per Frame (s)")
    plt.ylabel("APE RMSE (m)")
    plt.grid(alpha=0.3)
    plt.legend(title="Method", fontsize=8, title_fontsize=9)

    save_plot(output_path)


def generate_figures(df: pd.DataFrame, figures_dir: Path) -> list[tuple[str, Path]]:
    figures_dir.mkdir(parents=True, exist_ok=True)

    figure_specs = [
        ("APE RMSE", "ape_rmse_m", "APE RMSE (m)", figures_dir / "ape_rmse_m.png"),
        ("RPE RMSE", "rpe_rmse_m", "RPE RMSE (m)", figures_dir / "rpe_rmse_m.png"),
        ("Processed FPS", "processed_fps", "Processed FPS", figures_dir / "processed_fps.png"),
        (
            "Runtime per Frame",
            "runtime_per_frame_sec",
            "Runtime per Frame (s)",
            figures_dir / "runtime_per_frame_sec.png",
        ),
        (
            "Peak Memory",
            "peak_memory_mb",
            "Peak Memory (MB)",
            figures_dir / "peak_memory_mb.png",
        ),
    ]

    outputs = []

    for title, metric, ylabel, path in figure_specs:
        plot_bar(df, metric, ylabel, path)

        if path.exists():
            outputs.append((title, path))

    scatter_path = figures_dir / "accuracy_vs_runtime_per_frame.png"
    plot_accuracy_runtime(df, scatter_path)

    if scatter_path.exists():
        outputs.append(("Accuracy vs Runtime", scatter_path))

    return outputs


def figure_cards(figures: list[tuple[str, Path]], report_path: Path) -> str:
    if not figures:
        return "<p class='empty'>No figures generated.</p>"

    cards = []

    for title, path in figures:
        cards.append(
            f"""
            <div class="figure-card">
              <div class="figure-title">{safe(title)}</div>
              <a href="{rel(path, report_path)}" target="_blank">
                <img src="{rel(path, report_path)}" alt="{safe(title)}">
              </a>
            </div>
            """
        )

    return "<div class='figure-grid'>" + "\n".join(cards) + "</div>"


def build_report(
    df: pd.DataFrame,
    visual_df: pd.DataFrame,
    figures: list[tuple[str, Path]],
    report_path: Path,
    title: str,
) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{safe(title)}</title>

  <style>
    :root {{
      --bg: #f6f7fb;
      --panel: #ffffff;
      --text: #111827;
      --muted: #6b7280;
      --line: #e5e7eb;
      --blue: #2563eb;
      --blue-soft: #eff6ff;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.07);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      line-height: 1.45;
    }}

    .page {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 24px 64px;
    }}

    .hero {{
      background: linear-gradient(135deg, #0f172a, #2563eb);
      color: white;
      border-radius: 28px;
      padding: 34px;
      box-shadow: var(--shadow);
      margin-bottom: 28px;
    }}

    .hero h1 {{
      margin: 0 0 10px;
      font-size: 34px;
      letter-spacing: -0.04em;
    }}

    .hero p {{
      max-width: 780px;
      color: #dbeafe;
      margin: 0;
    }}

    section {{
      margin: 30px 0;
    }}

    h2 {{
      font-size: 22px;
      letter-spacing: -0.03em;
      margin: 0 0 14px;
    }}

    .panel, .metric-card, .figure-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: var(--shadow);
    }}

    .panel {{
      padding: 20px;
    }}

    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 14px;
    }}

    .metric-card {{
      padding: 18px;
    }}

    .metric-title {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }}

    .metric-value {{
      font-size: 27px;
      font-weight: 800;
      letter-spacing: -0.04em;
    }}

    .metric-subtitle {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 6px;
    }}

    .table-scroll {{
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 16px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      min-width: 850px;
      font-size: 13px;
    }}

    th {{
      text-align: left;
      padding: 11px 12px;
      background: #111827;
      color: white;
      white-space: nowrap;
    }}

    td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      white-space: nowrap;
    }}

    tr:nth-child(even) td {{
      background: #f9fafb;
    }}

    .rank {{
      font-weight: 800;
      color: var(--blue);
    }}

    .figure-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }}

    .figure-card {{
      padding: 14px;
    }}

    .figure-title {{
      font-weight: 800;
      margin-bottom: 8px;
      font-size: 14px;
    }}

    .figure-card img {{
      width: 100%;
      height: 230px;
      object-fit: contain;
      display: block;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: white;
    }}

    .note, .empty {{
      color: var(--muted);
    }}
  </style>
</head>

<body>
  <main class="page">
    <div class="hero">
      <h1>{safe(title)}</h1>
      <p>
        Filtered VO/VIO deployment report generated from current benchmark outputs.
      </p>
    </div>

    <section>
      <h2>Overview</h2>
      {overview_cards(df)}
    </section>

    <section>
      <h2>Method Ranking</h2>
      <div class="panel">
        {ranking_table(df)}
      </div>
    </section>

    <section>
      <h2>Sequence-Level Results</h2>
      <div class="panel">
        {sequence_table(df)}
      </div>
    </section>

    <section>
      <h2>Benchmark Figures</h2>
      {figure_cards(figures, report_path)}
    </section>

    <section>
      <h2>Visual Conditions</h2>
      <div class="panel">
        {visual_table(visual_df)}
      </div>
    </section>

    <section>
      <h2>Interpretation Notes</h2>
      <div class="panel">
        <p><strong>APE RMSE</strong> measures global trajectory error. Lower is better.</p>
        <p><strong>RPE RMSE</strong> measures local relative motion error. Lower is better.</p>
        <p><strong>Processed FPS</strong> measures processing speed. Higher is better.</p>
        <p><strong>Runtime per frame</strong> is useful because raw runtime depends on sequence length.</p>
      </div>
    </section>
  </main>
</body>
</html>
"""


def main() -> None:
    args = parse_args()

    if not BENCHMARK_TABLE.exists():
        raise FileNotFoundError(
            f"Missing benchmark table: {BENCHMARK_TABLE}. "
            "Run python src/voeval.py summarize first."
        )

    benchmark_df = pd.read_csv(BENCHMARK_TABLE)
    benchmark_df = add_method_labels(benchmark_df)

    filtered_df = filter_dataframe(
        benchmark_df,
        dataset=args.dataset,
        methods=args.methods,
        sequences=args.sequences,
    )

    if filtered_df.empty:
        raise RuntimeError("No benchmark rows matched the requested filters.")

    visual_df = pd.DataFrame()

    if VISUAL_TABLE.exists():
        visual_df = pd.read_csv(VISUAL_TABLE)
        visual_df = filter_dataframe(
            visual_df,
            dataset=args.dataset,
            methods=None,
            sequences=args.sequences,
        )

    output_dir = Path("results") / "reports" / args.name
    figures_dir = output_dir / "figures"
    report_path = output_dir / "report.html"

    output_dir.mkdir(parents=True, exist_ok=True)

    filtered_df.to_csv(output_dir / "benchmark_filtered.csv", index=False)

    if not visual_df.empty:
        visual_df.to_csv(output_dir / "visual_conditions_filtered.csv", index=False)

    figures = generate_figures(filtered_df, figures_dir)

    title_parts = ["VO/VIO Filtered Report"]

    if args.dataset:
        title_parts.append(args.dataset)

    if args.methods:
        title_parts.append(f"{len(args.methods)} method(s)")

    title = " - ".join(title_parts)

    report_html = build_report(
        filtered_df,
        visual_df,
        figures,
        report_path,
        title,
    )

    report_path.write_text(report_html, encoding="utf-8")

    print(f"Saved filtered report: {report_path}")
    print(f"Saved filtered benchmark table: {output_dir / 'benchmark_filtered.csv'}")


if __name__ == "__main__":
    main()
