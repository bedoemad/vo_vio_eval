from pathlib import Path
import html
import os

import pandas as pd


REPORT_PATH = Path("results/report.html")
FINAL_TABLES_DIR = Path("results/final_tables")
FIGURES_DIR = Path("results/final_figures")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def rel(path: Path) -> str:
    return os.path.relpath(path.resolve(), REPORT_PATH.parent.resolve()).replace("\\", "/")


def safe(value) -> str:
    if value is None:
        return "—"
    return html.escape(str(value))


def fmt(value, digits: int = 3) -> str:
    try:
        if pd.isna(value):
            return "—"
    except Exception:
        pass

    if isinstance(value, bool):
        return str(value)

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return f"{value:.{digits}f}"

    return str(value)


def success_mask(df: pd.DataFrame) -> pd.Series:
    if "success" not in df.columns:
        return pd.Series([True] * len(df), index=df.index)

    return df["success"].astype(str).str.lower().isin(["true", "1", "yes", "ok"])


def badge(value) -> str:
    if value is True or str(value).lower() in ["true", "1", "yes", "ok"]:
        return "<span class='badge ok'>OK</span>"
    return "<span class='badge fail'>FAIL</span>"


def section(section_id: str, title: str, body: str) -> str:
    return f"""
    <section id="{safe(section_id)}" class="section">
      <h2>{safe(title)}</h2>
      {body}
    </section>
    """


def metric_card(title: str, value: str, subtitle: str) -> str:
    return f"""
    <div class="metric-card">
      <div class="metric-title">{safe(title)}</div>
      <div class="metric-value">{safe(value)}</div>
      <div class="metric-subtitle">{safe(subtitle)}</div>
    </div>
    """


def make_summary_cards(df: pd.DataFrame) -> str:
    if df.empty:
        return "<div class='panel'><p class='empty'>No benchmark summary found.</p></div>"

    total_runs = len(df)
    total_methods = df["method"].nunique() if "method" in df.columns else 0
    total_sequences = df["sequence"].nunique() if "sequence" in df.columns else 0
    successful_runs = int(success_mask(df).sum())

    best_ape = "—"
    if "ape_rmse_m" in df.columns and df["ape_rmse_m"].notna().any():
        best_ape = f"{df['ape_rmse_m'].min():.4f} m"

    median_fps = "—"
    if "processed_fps" in df.columns and df["processed_fps"].notna().any():
        median_fps = f"{df['processed_fps'].median():.2f}"

    cards = [
        metric_card("Total runs", str(total_runs), "All evaluated rows"),
        metric_card("Successful", f"{successful_runs}/{total_runs}", "Completed evaluations"),
        metric_card("Methods", str(total_methods), "Compared VO/VIO systems"),
        metric_card("Sequences", str(total_sequences), "Dataset sequences"),
        metric_card("Best APE", best_ape, "Lowest trajectory error"),
        metric_card("Median FPS", median_fps, "Typical processing speed"),
    ]

    return "<div class='metric-grid'>" + "\n".join(cards) + "</div>"


def dataset_coverage_table(df: pd.DataFrame) -> str:
    if df.empty or "method" not in df.columns or "sequence" not in df.columns:
        return "<div class='panel'><p class='empty'>No dataset coverage data available.</p></div>"

    data = df.copy()

    if "dataset" not in data.columns:
        data["dataset"] = data["sequence"].apply(
            lambda s: "KITTI" if str(s).startswith("kitti") else "EuRoC"
        )

    data["success_bool"] = success_mask(data)

    grouped = (
        data.groupby(["dataset", "method"])
        .agg(
            sequences=("sequence", "nunique"),
            runs=("sequence", "count"),
            successful_runs=("success_bool", "sum"),
        )
        .reset_index()
    )

    grouped["failed_runs"] = grouped["runs"] - grouped["successful_runs"]
    grouped["success_rate"] = grouped["successful_runs"] / grouped["runs"]
    grouped = grouped.sort_values(["dataset", "method"])

    rows = []
    for _, row in grouped.iterrows():
        rows.append(
            f"""
            <tr>
              <td>{safe(row.get("dataset", "—"))}</td>
              <td>{safe(row.get("method", "—"))}</td>
              <td>{fmt(row.get("sequences"), 0)}</td>
              <td>{fmt(row.get("runs"), 0)}</td>
              <td>{fmt(row.get("successful_runs"), 0)}</td>
              <td>{fmt(row.get("failed_runs"), 0)}</td>
              <td>{fmt(row.get("success_rate") * 100, 1)}%</td>
            </tr>
            """
        )

    return f"""
    <div class="panel">
      <p class="note">
        This table summarizes method coverage across datasets and highlights failed or invalid runs.
      </p>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Dataset</th>
              <th>Method</th>
              <th>Sequences</th>
              <th>Total runs</th>
              <th>Successful</th>
              <th>Failed</th>
              <th>Success rate</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """


def failed_runs_table(df: pd.DataFrame) -> str:
    if df.empty or "success" not in df.columns:
        return "<div class='panel'><p class='empty'>No run-validity data available.</p></div>"

    data = df.copy()
    failed = data[~success_mask(data)]

    if failed.empty:
        return """
        <div class="panel">
          <p class="note">
            No failed or invalid runs were found in the current benchmark summary.
          </p>
        </div>
        """

    columns = [
        "dataset",
        "sequence",
        "difficulty",
        "method",
        "success",
        "runtime_sec",
        "peak_memory_mb",
        "error_message",
    ]
    columns = [col for col in columns if col in failed.columns]
    failed = failed[columns]

    sort_cols = [col for col in ["dataset", "sequence", "method"] if col in failed.columns]
    if sort_cols:
        failed = failed.sort_values(sort_cols)

    rows = []
    for _, row in failed.iterrows():
        rows.append(
            f"""
            <tr>
              <td>{safe(row.get("dataset", "—"))}</td>
              <td>{safe(row.get("sequence", "—"))}</td>
              <td>{safe(row.get("difficulty", "—"))}</td>
              <td>{safe(row.get("method", "—"))}</td>
              <td>{badge(row.get("success", False))}</td>
              <td>{fmt(row.get("runtime_sec"), 2)}</td>
              <td>{fmt(row.get("peak_memory_mb"), 1)}</td>
              <td>{safe(row.get("error_message", "—"))}</td>
            </tr>
            """
        )

    return f"""
    <div class="panel">
      <p class="note">
        Failed or invalid runs are important in deployment-oriented evaluation:
        a method should not be considered successful only because it produced an output file.
      </p>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Dataset</th>
              <th>Sequence</th>
              <th>Difficulty</th>
              <th>Method</th>
              <th>Status</th>
              <th>Runtime (s)</th>
              <th>Peak memory (MB)</th>
              <th>Error message</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """


def method_ranking_table(df: pd.DataFrame) -> str:
    if df.empty or "method" not in df.columns or "ape_rmse_m" not in df.columns:
        return "<div class='panel'><p class='empty'>No method ranking data available.</p></div>"

    data = df.copy()
    data = data[success_mask(data)]
    data = data.dropna(subset=["ape_rmse_m"])

    if data.empty:
        return "<div class='panel'><p class='empty'>No successful method runs available.</p></div>"

    agg_spec = {
        "runs": ("sequence", "count"),
        "mean_ape": ("ape_rmse_m", "mean"),
        "median_ape": ("ape_rmse_m", "median"),
    }

    if "rpe_rmse_m" in data.columns:
        agg_spec["mean_rpe"] = ("rpe_rmse_m", "mean")

    if "processed_fps" in data.columns:
        agg_spec["mean_fps"] = ("processed_fps", "mean")

    if "runtime_per_frame_sec" in data.columns:
        agg_spec["runtime_per_frame"] = ("runtime_per_frame_sec", "mean")

    if "peak_memory_mb" in data.columns:
        agg_spec["peak_memory"] = ("peak_memory_mb", "mean")

    grouped = data.groupby("method").agg(**agg_spec).reset_index()
    grouped = grouped.sort_values("mean_ape", ascending=True)

    rows = []
    for rank, (_, row) in enumerate(grouped.iterrows(), start=1):
        rows.append(
            f"""
            <tr>
              <td class="rank">{rank}</td>
              <td><strong>{safe(row.get("method", "—"))}</strong></td>
              <td>{fmt(row.get("runs"), 0)}</td>
              <td>{fmt(row.get("mean_ape"), 4)}</td>
              <td>{fmt(row.get("median_ape"), 4)}</td>
              <td>{fmt(row.get("mean_rpe"), 4)}</td>
              <td>{fmt(row.get("mean_fps"), 2)}</td>
              <td>{fmt(row.get("runtime_per_frame"), 4)}</td>
              <td>{fmt(row.get("peak_memory"), 1)}</td>
            </tr>
            """
        )

    return f"""
    <div class="panel">
      <p class="note">
        Methods are ranked by mean APE Sim(3) RMSE. Sim(3) evaluates trajectory shape after scale correction. SE(3) values in the sequence table reflect metric-scale deployment behavior.
      </p>
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
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """


def best_per_sequence_table(df: pd.DataFrame) -> str:
    required = {"sequence", "method", "ape_rmse_m"}

    if df.empty or not required.issubset(df.columns):
        return "<div class='panel'><p class='empty'>No best-per-sequence data available.</p></div>"

    data = df.copy()
    data = data[success_mask(data)]
    data = data.dropna(subset=["ape_rmse_m"])

    if data.empty:
        return "<div class='panel'><p class='empty'>No valid APE values available.</p></div>"

    idx = data.groupby("sequence")["ape_rmse_m"].idxmin()
    best = data.loc[idx].sort_values("sequence")

    rows = []
    for _, row in best.iterrows():
        rows.append(
            f"""
            <tr>
              <td>{safe(row.get("dataset", "—"))}</td>
              <td>{safe(row.get("sequence", "—"))}</td>
              <td>{safe(row.get("difficulty", "—"))}</td>
              <td><strong>{safe(row.get("method", "—"))}</strong></td>
              <td>{fmt(row.get("ape_rmse_m"), 4)}</td>
              <td>{fmt(row.get("rpe_rmse_m"), 4)}</td>
              <td>{fmt(row.get("processed_fps"), 2)}</td>
            </tr>
            """
        )

    return f"""
    <div class="panel">
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Dataset</th>
              <th>Sequence</th>
              <th>Difficulty</th>
              <th>Best method by APE Sim(3)</th>
              <th>APE Sim(3) RMSE (m)</th>
              <th>RPE Sim(3) RMSE (m)</th>
              <th>FPS</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """


def sequence_results_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<div class='panel'><p class='empty'>No sequence-level results found.</p></div>"

    columns = [
      "dataset",
      "sequence",
      "difficulty",
      "method",
      "success",

      # Default/legacy Sim(3) columns.
      "ape_rmse_m",
      "rpe_rmse_m",

      # Explicit alignment-aware metrics.
      "ape_sim3_rmse_m",
      "rpe_sim3_rmse_m",
      "ape_se3_rmse_m",
      "rpe_se3_rmse_m",

      "ape_rmse_percent_of_path",
      "runtime_sec",
      "runtime_per_frame_sec",
      "processed_fps",
      "peak_memory_mb",
    ]

    columns = [col for col in columns if col in df.columns]
    data = df[columns].copy()

    sort_cols = [col for col in ["dataset", "sequence", "method"] if col in data.columns]
    if sort_cols:
        data = data.sort_values(sort_cols)

    rows = []
    for _, row in data.iterrows():
        rows.append(
            f"""
            <tr>
              <td>{safe(row.get("dataset", "—"))}</td>
              <td>{safe(row.get("sequence", "—"))}</td>
              <td>{safe(row.get("difficulty", "—"))}</td>
              <td>{safe(row.get("method", "—"))}</td>
              <td>{badge(row.get("success", True))}</td>
              <td>{fmt(row.get("ape_rmse_m"), 4)}</td>
              <td>{fmt(row.get("rpe_rmse_m"), 4)}</td>
              <td>{fmt(row.get("ape_sim3_rmse_m"), 4)}</td>
              <td>{fmt(row.get("rpe_sim3_rmse_m"), 4)}</td>
              <td>{fmt(row.get("ape_se3_rmse_m"), 4)}</td>
              <td>{fmt(row.get("rpe_se3_rmse_m"), 4)}</td>
              <td>{fmt(row.get("ape_rmse_percent_of_path"), 3)}</td>
              <td>{fmt(row.get("runtime_sec"), 2)}</td>
              <td>{fmt(row.get("runtime_per_frame_sec"), 4)}</td>
              <td>{fmt(row.get("processed_fps"), 2)}</td>
              <td>{fmt(row.get("peak_memory_mb"), 1)}</td>
            </tr>
            """
        )

    return f"""
    <div class="panel">
      <p class="note">Use the search box to filter by method, sequence, or dataset.</p>

      <div class="table-toolbar">
        <input id="resultSearch" placeholder="Search table..." onkeyup="filterTable()">
      </div>

      <div class="table-scroll">
        <table id="resultsTable">
          <thead>
            <tr>
              <th>Dataset</th>
              <th>Sequence</th>
              <th>Difficulty</th>
              <th>Method</th>
              <th>Status</th>
              <th>APE Sim(3) RMSE (m)</th>
              <th>RPE Sim(3) RMSE (m)</th>
              <th>APE Sim(3) explicit (m)</th>
              <th>RPE Sim(3) explicit (m)</th>
              <th>APE SE(3) RMSE (m)</th>
              <th>RPE SE(3) RMSE (m)</th>
              <th>APE (% path)</th>
              <th>Runtime (s)</th>
              <th>Runtime/frame (s)</th>
              <th>FPS</th>
              <th>Peak memory (MB)</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """


def visual_conditions_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<div class='panel'><p class='empty'>No visual-condition summary found.</p></div>"

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

    columns = [col for col in columns if col in df.columns]
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
    <div class="panel">
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
              <th>FAST texture</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """


def diagnostics_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<div class='panel'><p class='empty'>No generic diagnostic effects found.</p></div>"

    data = df.copy()

    if "hard_minus_easy_error_m" in data.columns:
        data = data.sort_values("hard_minus_easy_error_m", ascending=False)

    data = data.head(25)

    rows = []
    for _, row in data.iterrows():
        rows.append(
            f"""
            <tr>
              <td>{safe(row.get("dataset", "—"))}</td>
              <td>{safe(row.get("sequence", "—"))}</td>
              <td>{safe(row.get("method", "—"))}</td>
              <td>{safe(row.get("condition_group", "—"))}</td>
              <td>{safe(row.get("condition_metric", "—"))}</td>
              <td>{safe(row.get("hard_condition", "—"))}</td>
              <td>{fmt(row.get("hard_minus_easy_error_m"), 4)}</td>
              <td>{fmt(row.get("hard_over_easy_error_ratio"), 3)}</td>
            </tr>
            """
        )

    return f"""
    <div class="panel">
      <p class="note">
        This table shows the strongest condition-dependent error increases.
        Positive hard-minus-easy values mean the harder condition produced higher error.
      </p>

      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Dataset</th>
              <th>Sequence</th>
              <th>Method</th>
              <th>Group</th>
              <th>Condition</th>
              <th>Hard bin</th>
              <th>Hard - easy error (m)</th>
              <th>Hard / easy ratio</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """


def figure(path: Path, title: str, description: str = "") -> str:
    if not path.exists():
        return ""

    return f"""
    <div class="figure-card">
      <div class="figure-title">{safe(title)}</div>
      <a href="{rel(path)}" target="_blank">
        <img src="{rel(path)}" alt="{safe(title)}">
      </a>
      <div class="figure-description">{safe(description)}</div>
    </div>
    """


def figure_grid(figures: list[str]) -> str:
    figures = [fig for fig in figures if fig.strip()]

    if not figures:
        return "<div class='panel'><p class='empty'>No figures found for this section.</p></div>"

    return "<div class='figure-grid'>" + "\n".join(figures) + "</div>"


def collect_pngs(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(folder.rglob("*.png"))


def pretty_title_from_path(path: Path, root: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path.name

    parts = list(Path(relative).with_suffix("").parts)
    return " / ".join(part.replace("_", " ").replace("-", " ").title() for part in parts)


def figure_gallery_from_folder(
    folder: Path,
    description: str = "",
    max_figures=None,
) -> str:
    pngs = collect_pngs(folder)

    if max_figures is not None:
        pngs = pngs[:max_figures]

    cards = [figure(path, pretty_title_from_path(path, folder), description) for path in pngs]
    return figure_grid(cards)


def details(title: str, body: str) -> str:
    return f"""
    <details>
      <summary>{safe(title)}</summary>
      <div class="details-body">
        {body}
      </div>
    </details>
    """


def csv_export_links() -> str:
    exports = [
        ("Benchmark summary", FINAL_TABLES_DIR / "benchmark_summary_final.csv"),
        ("Visual conditions", FINAL_TABLES_DIR / "visual_conditions_summary_final.csv"),
        ("Appearance failure effects", FINAL_TABLES_DIR / "failure_effect_summary_final.csv"),
        ("Motion failure effects", FINAL_TABLES_DIR / "motion_failure_effect_summary.csv"),
        ("Diagnostic effects", FINAL_TABLES_DIR / "diagnostic_effect_summary_final.csv"),
        ("Generic condition effects", FINAL_TABLES_DIR / "all_methods_condition_effect_summary.csv"),
    ]

    links = []
    for label, path in exports:
        if path.exists():
            links.append(f"<a href='{rel(path)}'>{safe(label)}</a>")

    if not links:
        return "<p class='empty'>No CSV exports found.</p>"

    return "<div class='csv-links'>" + "\n".join(links) + "</div>"


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    benchmark_df = read_csv(FINAL_TABLES_DIR / "benchmark_summary_final.csv")
    visual_df = read_csv(FINAL_TABLES_DIR / "visual_conditions_summary_final.csv")
    diagnostics_df = read_csv(FINAL_TABLES_DIR / "all_methods_condition_effect_summary.csv")

    benchmark_figures = figure_gallery_from_folder(
        FIGURES_DIR / "benchmark_clean",
        "Accuracy, runtime, and memory benchmark figures across all datasets.",
    )

    visual_figures = figure_gallery_from_folder(
        FIGURES_DIR / "visual_conditions",
        "Visual appearance summaries such as blur, texture, brightness, and sequence difficulty.",
    )

    failure_effect_figures = figure_gallery_from_folder(
        FIGURES_DIR / "failure_effects",
        "Visual condition effects on localization error.",
    )

    motion_effect_figures = figure_gallery_from_folder(
        FIGURES_DIR / "motion_failure_effects",
        "Motion condition effects on localization error.",
    )

    diagnostic_effect_figures = figure_gallery_from_folder(
        FIGURES_DIR / "diagnostic_effects",
        "Final diagnostic-effect plots summarizing condition-dependent error changes.",
    )

    diagnostic_pngs = collect_pngs(FIGURES_DIR / "generic_failure_diagnostics_clean")

    main_diagnostic_figures = []
    extra_diagnostic_figures = []

    for index, path in enumerate(diagnostic_pngs):
        try:
            title = str(path.parent.relative_to(FIGURES_DIR / "generic_failure_diagnostics_clean"))
        except ValueError:
            title = path.stem

        card = figure(path, title, "Top condition-dependent error factors.")

        if index < 8:
            main_diagnostic_figures.append(card)
        else:
            extra_diagnostic_figures.append(card)

    extra_diagnostics_html = ""
    if extra_diagnostic_figures:
        extra_diagnostics_html = details(
            "Additional diagnostic figures",
            figure_grid(extra_diagnostic_figures),
        )

    html_doc = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>VO/VIO Deployment Evaluation Report</title>

  <style>
    :root {{
      --bg: #f6f7fb;
      --panel: #ffffff;
      --text: #111827;
      --muted: #6b7280;
      --line: #e5e7eb;
      --blue: #2563eb;
      --blue-soft: #eff6ff;
      --green: #059669;
      --red: #dc2626;
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

    .layout {{
      display: grid;
      grid-template-columns: 230px minmax(0, 1fr);
      min-height: 100vh;
    }}

    .sidebar {{
      position: sticky;
      top: 0;
      height: 100vh;
      background: #0f172a;
      color: white;
      padding: 26px 20px;
      overflow-y: auto;
    }}

    .sidebar h1 {{
      font-size: 18px;
      margin: 0 0 22px;
      line-height: 1.25;
    }}

    .sidebar a {{
      display: block;
      color: #cbd5e1;
      text-decoration: none;
      padding: 9px 0;
      font-size: 14px;
    }}

    .sidebar a:hover {{
      color: white;
    }}

    .content {{
      padding: 32px;
      max-width: 1260px;
    }}

    .hero {{
      background: linear-gradient(135deg, #1e3a8a, #2563eb);
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
      max-width: 820px;
      margin: 0;
      color: #dbeafe;
      font-size: 16px;
    }}

    .section {{
      margin: 30px 0;
    }}

    .section h2 {{
      font-size: 22px;
      letter-spacing: -0.03em;
      margin: 0 0 14px;
    }}

    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 20px;
      box-shadow: var(--shadow);
    }}

    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
      gap: 14px;
    }}

    .metric-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 18px;
      box-shadow: var(--shadow);
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

    .csv-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}

    .csv-links a {{
      background: var(--blue-soft);
      color: var(--blue);
      padding: 9px 12px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
    }}

    .table-toolbar {{
      margin-bottom: 12px;
    }}

    .table-toolbar input {{
      width: 100%;
      max-width: 440px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 11px 14px;
      font-size: 14px;
      outline: none;
      background: white;
    }}

    .table-scroll {{
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 16px;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      background: white;
      min-width: 850px;
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

    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 800;
    }}

    .badge.ok {{
      color: var(--green);
      background: #ecfdf5;
    }}

    .badge.fail {{
      color: var(--red);
      background: #fef2f2;
    }}

    .figure-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }}

    .figure-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 14px;
      box-shadow: var(--shadow);
    }}

    .figure-title {{
      font-weight: 800;
      font-size: 14px;
      margin-bottom: 8px;
    }}

    .figure-card img {{
      width: 100%;
      height: 230px;
      object-fit: contain;
      display: block;
      border-radius: 14px;
      background: white;
      border: 1px solid var(--line);
    }}

    .figure-description {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
    }}

    details {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 16px 18px;
      box-shadow: var(--shadow);
      margin: 14px 0;
    }}

    summary {{
      cursor: pointer;
      font-weight: 800;
    }}

    .details-body {{
      margin-top: 16px;
    }}

    .note {{
      color: var(--muted);
      margin: 0 0 14px;
      max-width: 850px;
    }}

    .empty {{
      color: var(--muted);
      font-weight: 700;
    }}

    @media (max-width: 900px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}

      .sidebar {{
        position: relative;
        height: auto;
      }}

      .content {{
        padding: 20px;
      }}

      .hero h1 {{
        font-size: 27px;
      }}
    }}

    @media print {{
      .sidebar {{
        display: none;
      }}

      .layout {{
        display: block;
      }}

      .content {{
        padding: 0;
      }}

      .figure-card img {{
        height: 160px;
      }}
    }}
  </style>

  <script>
    function filterTable() {{
      const input = document.getElementById("resultSearch");
      const filter = input.value.toLowerCase();
      const table = document.getElementById("resultsTable");
      const rows = table.getElementsByTagName("tr");

      for (let i = 1; i < rows.length; i++) {{
        const text = rows[i].innerText.toLowerCase();
        rows[i].style.display = text.includes(filter) ? "" : "none";
      }}
    }}
  </script>
</head>

<body>
  <div class="layout">
    <aside class="sidebar">
      <h1>VO/VIO Report</h1>
      <a href="#overview">Overview</a>
      <a href="#coverage">Dataset Coverage</a>
      <a href="#failed">Failed Runs</a>
      <a href="#ranking">Method Ranking</a>
      <a href="#best">Best per Sequence</a>
      <a href="#results">Sequence Results</a>
      <a href="#figures">Benchmark Figures</a>
      <a href="#visual">Visual Conditions</a>
      <a href="#failure-effects">Visual Failure Effects</a>
      <a href="#motion-effects">Motion Failure Effects</a>
      <a href="#diagnostic-effects">Diagnostic Effect Figures</a>
      <a href="#diagnostics">Generic Diagnostics</a>
      <a href="#exports">CSV Exports</a>
      <a href="#notes">Notes</a>
    </aside>

    <main class="content">
      <div class="hero">
        <h1>VO/VIO Deployment-Oriented Evaluation Report</h1>
        <p>
          Compact benchmark dashboard for trajectory accuracy, runtime efficiency,
          memory usage, run validity, and condition-dependent robustness across EuRoC and KITTI.
        </p>
      </div>

      {section("overview", "Overview", make_summary_cards(benchmark_df))}

      {section("coverage", "Dataset Coverage and Run Validity", dataset_coverage_table(benchmark_df))}

      {section("failed", "Failed or Invalid Runs", failed_runs_table(benchmark_df))}

      {section("ranking", "Method Ranking", method_ranking_table(benchmark_df))}

      {section("best", "Best Method per Sequence", best_per_sequence_table(benchmark_df))}

      {section("results", "Sequence-Level Results", sequence_results_table(benchmark_df))}

      {section("figures", "Key Benchmark Figures", benchmark_figures)}

      {section(
        "visual",
        "Visual-Condition Summary",
        details(
            "Open visual-condition table and figures",
            visual_conditions_table(visual_df) + visual_figures,
        ),
    )}

    {section(
        "failure-effects",
        "Visual Failure-Effect Figures",
        details(
            "Open visual failure-effect figures",
            failure_effect_figures,
        ),
    )}

    {section(
        "motion-effects",
        "Motion Failure-Effect Figures",
        details(
           "Open motion failure-effect figures",
           motion_effect_figures,
        ),
    )}

    {section(
        "diagnostic-effects",
        "Diagnostic Effect Figures",
        details(
            "Open diagnostic-effect figures",
            diagnostic_effect_figures,
        ),
    )}

    {section(
        "diagnostics",
        "Strongest Condition-Dependent Effects",
        details(
        "Open generic diagnostic table and figures",
        diagnostics_table(diagnostics_df)
        + figure_grid(main_diagnostic_figures)
        + extra_diagnostics_html,
        ),
    )}

    {section(
        "exports",
       "CSV Exports",
       details(
            "Open CSV export links",
           "<div class='panel'>" + csv_export_links() + "</div>",
        ),
    )}
      {section(
          "notes",
          "Interpretation Notes",
          '''
          <div class="panel">
            <p><strong>APE RMSE</strong> measures global trajectory error. Lower is better.</p>
            <p><strong>RPE RMSE</strong> measures local relative motion error. Lower is better.</p>
            <p><strong>Processed FPS</strong> measures method speed. Higher is better.</p>
            <p><strong>Runtime per frame</strong> is useful because raw runtime depends on sequence length.</p>
            <p><strong>Sim(3)</strong> metrics correct scale and are useful for monocular trajectory-shape comparison.</p>
            <p><strong>SE(3)</strong> metrics do not correct scale and better reflects metric-scale deployment behavior.</p>
            <p><strong>Failed runs</strong> are preserved because deployment-oriented evaluation should expose invalid or unreliable method outputs.</p>
          </div>
          '''
      )}
    </main>
  </div>
</body>
</html>
"""

    REPORT_PATH.write_text(html_doc, encoding="utf-8")
    print(f"Saved report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
