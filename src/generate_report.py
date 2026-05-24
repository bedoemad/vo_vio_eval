from pathlib import Path
import html
import os
import pandas as pd


REPORT_PATH = Path("results/report.html")
FINAL_TABLES_DIR = Path("results/final_tables")
FIGURES_DIR = Path("results/final_figures")


def rel(path: Path):
    """
    Return path relative to the HTML report location.
    report.html is inside results/, so images should be linked like:
      final_figures/...
    not:
      results/final_figures/...
    """
    try:
        relative_path = os.path.relpath(
            path.resolve(),
            REPORT_PATH.parent.resolve(),
        )
        return relative_path.replace("\\", "/")
    except Exception:
        return path.as_posix()


def read_csv_preview(path: Path, max_rows=20):
    if not path.exists():
        return f"<p class='missing'>Missing table: {html.escape(str(path))}</p>"

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return (
            f"<p class='missing'>Could not read "
            f"{html.escape(str(path))}: {html.escape(str(exc))}</p>"
        )

    if df.empty:
        return f"<p class='missing'>Table is empty: {html.escape(str(path))}</p>"

    preview = df.head(max_rows).copy()

    return preview.to_html(
        index=False,
        classes="table",
        border=0,
        escape=True,
    )


def image_block(path: Path, title: str):
    if not path.exists():
        return f"""
        <div class="card">
          <h3>{html.escape(title)}</h3>
          <p class="missing">Missing figure: {html.escape(str(path))}</p>
        </div>
        """

    return f"""
    <div class="card">
      <h3>{html.escape(title)}</h3>
      <img src="{rel(path)}" alt="{html.escape(title)}">
    </div>
    """


def table_link(path: Path, title: str):
    if path.exists():
        return f"<li><a href='{rel(path)}'>{html.escape(title)}</a></li>"

    return f"<li class='missing'>{html.escape(title)} — missing</li>"


def collect_pngs(folder: Path):
    if not folder.exists():
        return []

    return sorted(folder.rglob("*.png"))


def section(title, body):
    return f"""
    <section>
      <h2>{html.escape(title)}</h2>
      {body}
    </section>
    """


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    benchmark_table = FINAL_TABLES_DIR / "benchmark_summary_final.csv"
    visual_table = FINAL_TABLES_DIR / "visual_conditions_summary_final.csv"
    diagnostic_table = FINAL_TABLES_DIR / "all_methods_condition_effect_summary.csv"

    table_links = """
    <ul>
      {benchmark}
      {visual}
      {failure}
      {motion}
      {diagnostic_old}
      {diagnostic_generic}
    </ul>
    """.format(
        benchmark=table_link(benchmark_table, "Benchmark Summary"),
        visual=table_link(visual_table, "Visual Conditions Summary"),
        failure=table_link(
            FINAL_TABLES_DIR / "failure_effect_summary_final.csv",
            "Appearance Failure Effects",
        ),
        motion=table_link(
            FINAL_TABLES_DIR / "motion_failure_effect_summary.csv",
            "Motion Failure Effects",
        ),
        diagnostic_old=table_link(
            FINAL_TABLES_DIR / "diagnostic_effect_summary_final.csv",
            "Original Diagnostic Effects",
        ),
        diagnostic_generic=table_link(
            diagnostic_table,
            "All-Methods Generic Diagnostic Effects",
        ),
    )

    benchmark_figures = ""

    preferred_benchmark_figs = [
        (
            FIGURES_DIR / "benchmark_clean" / "euroc" / "ape_rmse_m.png",
            "EuRoC APE RMSE",
        ),
        (
            FIGURES_DIR / "benchmark_clean" / "euroc" / "processed_fps.png",
            "EuRoC Processed FPS",
        ),
        (
            FIGURES_DIR / "benchmark_clean" / "kitti" / "ape_rmse_m.png",
            "KITTI APE RMSE",
        ),
        (
            FIGURES_DIR / "benchmark_clean" / "kitti" / "processed_fps.png",
            "KITTI Processed FPS",
        ),
        (
            FIGURES_DIR
            / "benchmark_clean"
            / "kitti"
            / "accuracy_vs_runtime_per_frame.png",
            "KITTI Accuracy vs Runtime per Frame",
        ),
        (
            FIGURES_DIR
            / "benchmark_clean"
            / "euroc"
            / "accuracy_vs_runtime_per_frame.png",
            "EuRoC Accuracy vs Runtime per Frame",
        ),
    ]

    for path, title in preferred_benchmark_figs:
        benchmark_figures += image_block(path, title)

    visual_figures = ""

    preferred_visual_figs = [
        (
            FIGURES_DIR / "visual_conditions" / "euroc" / "blur_mean.png",
            "EuRoC Mean Blur Score",
        ),
        (
            FIGURES_DIR / "visual_conditions" / "kitti" / "blur_mean.png",
            "KITTI Mean Blur Score",
        ),
        (
            FIGURES_DIR / "visual_conditions" / "kitti" / "fast_texture_mean.png",
            "KITTI Mean FAST Texture Score",
        ),
        (
            FIGURES_DIR / "visual_conditions" / "visual_difficulty_ranking.png",
            "Overall Visual Difficulty Ranking",
        ),
    ]

    for path, title in preferred_visual_figs:
        visual_figures += image_block(path, title)

    diagnostic_figures = ""

    diag_root = FIGURES_DIR / "generic_failure_diagnostics_clean"

    for path in collect_pngs(diag_root):
        title = path.parent.as_posix().replace(diag_root.as_posix() + "/", "")
        title = title.replace("/", " / ")
        diagnostic_figures += image_block(path, f"Diagnostics: {title}")

    if not diagnostic_figures:
        diagnostic_figures = "<p class='missing'>No generic diagnostic plots found yet.</p>"

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>VO/VIO Evaluation Report</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 32px;
      background: #f7f7f7;
      color: #222;
    }}

    h1 {{
      margin-bottom: 4px;
    }}

    h2 {{
      margin-top: 40px;
      border-bottom: 2px solid #ddd;
      padding-bottom: 8px;
    }}

    h3 {{
      margin-top: 0;
    }}

    .subtitle {{
      color: #666;
      margin-bottom: 32px;
    }}

    .card {{
      background: white;
      border-radius: 12px;
      padding: 18px;
      margin: 18px 0;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}

    img {{
      max-width: 100%;
      height: auto;
      display: block;
      margin-top: 12px;
    }}

    .table {{
      border-collapse: collapse;
      width: 100%;
      background: white;
      font-size: 13px;
    }}

    .table th {{
      background: #222;
      color: white;
      padding: 8px;
      text-align: left;
    }}

    .table td {{
      border-bottom: 1px solid #ddd;
      padding: 7px;
    }}

    .missing {{
      color: #a33;
      font-weight: bold;
    }}

    a {{
      color: #0645ad;
    }}

    code {{
      background: #eee;
      padding: 2px 4px;
      border-radius: 4px;
    }}
  </style>
</head>

<body>
  <h1>VO/VIO Evaluation Report</h1>
  <p class="subtitle">
    Automatically generated benchmark and diagnostic report.
  </p>

  {section("1. Final Tables", table_links)}

  {section("2. Benchmark Summary Preview", read_csv_preview(benchmark_table, max_rows=20))}

  {section("3. Benchmark Figures", benchmark_figures)}

  {section("4. Visual-Condition Summary Preview", read_csv_preview(visual_table, max_rows=15))}

  {section("5. Visual-Condition Figures", visual_figures)}

  {section("6. Generic Diagnostic Effects Preview", read_csv_preview(diagnostic_table, max_rows=20))}

  {section("7. Generic Diagnostic Figures", diagnostic_figures)}

  <section>
    <h2>8. Notes</h2>
    <div class="card">
      <p>
        Raw runtime depends on sequence length, so processed FPS and runtime per frame
        are included for fairer efficiency comparison.
      </p>
      <p>
        Raw APE is not directly comparable across datasets with very different trajectory
        lengths, so normalized APE is also reported.
      </p>
      <p>
        Generic diagnostics compare error under easier and harder visual/motion conditions
        for each method and sequence.
      </p>
    </div>
  </section>
</body>
</html>
"""

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Saved report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
