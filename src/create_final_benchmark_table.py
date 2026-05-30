from pathlib import Path
import pandas as pd
from benchmark_filters import keep_real_benchmark_methods


INPUT = Path("results/comparison_summary.csv")
OUT = Path("results/final_tables/benchmark_summary_final.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

# Keep only real methods; remove smoke-test/demo adapters from final table.
df = keep_real_benchmark_methods(df)

df["dataset"] = df["sequence"].apply(
    lambda x: "KITTI" if str(x).startswith("kitti") else "EuRoC"
)

df["difficulty"] = df["sequence"].map({
    "euroc_mh01": "easy",
    "euroc_mh02": "easy",
    "euroc_mh03": "medium",
    "euroc_mh04": "difficult",
    "euroc_mh05": "difficult",
}).fillna("road/outdoor")

cols = [
    "dataset",
    "sequence",
    "difficulty",
    "method",
    "success",
    "num_frames",
    "trajectory_length_m",
     # Legacy/default accuracy columns.
    # These are kept for backward compatibility and currently correspond to Sim(3).
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
    "runtime_per_meter_sec",
    "peak_memory_mb",
    "avg_memory_mb",
]

df = df[[c for c in cols if c in df.columns]]

df = df.sort_values(["dataset", "sequence", "method"])

df.to_csv(OUT, index=False)

print(df)
print(f"\nSaved: {OUT}")
