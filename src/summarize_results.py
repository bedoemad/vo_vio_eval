import json
import zipfile
from pathlib import Path
from config_utils import load_sequences, resolve_sequence_paths
import numpy as np
import pandas as pd
from benchmark_filters import keep_real_benchmark_methods


def find_rmse(obj):
    if isinstance(obj, dict):
        if "rmse" in obj:
            return obj["rmse"]
        for value in obj.values():
            found = find_rmse(value)
            if found is not None:
                return found

    elif isinstance(obj, list):
        for item in obj:
            found = find_rmse(item)
            if found is not None:
                return found

    return None


def extract_rmse_from_evo_zip(zip_path: Path):
    if not zip_path.exists():
        return None

    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            if name.endswith(".json"):
                with z.open(name) as f:
                    data = json.load(f)

                rmse = find_rmse(data)
                if rmse is not None:
                    return rmse

    return None


def load_tum_positions(path: Path):
    if not path or not path.exists():
        return None

    try:
        df = pd.read_csv(
            path,
            sep=r"\s+",
            header=None,
            names=["timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw"],
        )
        return df[["tx", "ty", "tz"]].to_numpy()
    except Exception:
        return None


def trajectory_length_m(tum_path: Path):
    positions = load_tum_positions(tum_path)

    if positions is None or len(positions) < 2:
        return None

    diffs = np.diff(positions, axis=0)
    distances = np.linalg.norm(diffs, axis=1)

    return float(distances.sum())


def count_frames(sequence_cfg):
    """
    Counts image frames for EuRoC and KITTI robustly.
    EuRoC usually points directly to mav0/cam0/data.
    KITTI usually points to the sequence folder containing image_0/image_2.
    """
    seq_path = Path(sequence_cfg["path"])
    dataset = sequence_cfg.get("dataset", "").lower()

    if not seq_path.exists():
        return None

    # If path directly contains image files
    direct_images = list(seq_path.glob("*.png")) + list(seq_path.glob("*.jpg"))
    if direct_images:
        return len(direct_images)

    # KITTI image folders
    for folder in ["image_0", "image_2", "image_1", "image_3"]:
        img_dir = seq_path / folder
        if img_dir.exists():
            images = list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg"))
            if images:
                return len(images)

    # EuRoC root fallback
    euroc_cam0 = seq_path / "mav0" / "cam0" / "data"
    if euroc_cam0.exists():
        images = list(euroc_cam0.glob("*.png")) + list(euroc_cam0.glob("*.jpg"))
        if images:
            return len(images)

    return None


sequences = [resolve_sequence_paths(seq) for seq in load_sequences()]
sequence_map = {seq["name"]: seq for seq in sequences}

rows = []

for path in Path("results").glob("*/*/run_result.json"):
    with open(path) as f:
        r = json.load(f)

    result_dir = Path(r["result_dir"])
    ape_zip = result_dir / "metrics" / "ape_results.zip"
    rpe_zip = result_dir / "metrics" / "rpe_results.zip"

    sequence = r["sequence"]
    seq_cfg = sequence_map.get(sequence)

    gt_path = Path(seq_cfg["groundtruth"]) if seq_cfg else None

    traj_length = trajectory_length_m(gt_path) if gt_path else None
    num_frames = count_frames(seq_cfg) if seq_cfg else None

    ape_rmse = extract_rmse_from_evo_zip(ape_zip)
    rpe_rmse = extract_rmse_from_evo_zip(rpe_zip)

    runtime = r.get("runtime_sec")

    runtime_per_frame = (
        runtime / num_frames
        if runtime is not None and num_frames and runtime > 0
        else None
    )

    processed_fps = (
        num_frames / runtime
        if runtime is not None and num_frames and runtime > 0
        else None
    )

    runtime_per_meter = (
        runtime / traj_length
        if runtime is not None and traj_length and runtime > 0
        else None
    )

    rows.append({
        "method": r["method"],
        "sequence": sequence,
        "success": r["success"],
        "runtime_sec": runtime,
        "num_frames": num_frames,
        "runtime_per_frame_sec": runtime_per_frame,
        "processed_fps": processed_fps,
        "peak_memory_mb": r["peak_memory_mb"],
        "avg_memory_mb": r["avg_memory_mb"],
        "trajectory_length_m": traj_length,
        "runtime_per_meter_sec": runtime_per_meter,
        "ape_rmse_m": ape_rmse,
        "rpe_rmse_m": rpe_rmse,
        "ape_rmse_percent_of_path": (
            ape_rmse / traj_length * 100
            if ape_rmse is not None and traj_length
            else None
        ),
        "prediction": r["predicted_trajectory"],
    })

df = pd.DataFrame(rows)

# Exclude smoke-test/demo adapters from the real benchmark summary.
# They remain usable for pipeline testing, but should not affect final thesis plots/tables.
df = keep_real_benchmark_methods(df)

# Treat zero/negative runtime as invalid profiling metadata.
# A real run through MethodRunner should have runtime_sec > 0; zero usually means
# --skip-run/stale metadata or an invalid profiling result.
if "runtime_sec" in df.columns:
    invalid_runtime = df["runtime_sec"].isna() | (df["runtime_sec"] <= 0)
    for col in ["runtime_per_frame_sec", "processed_fps", "runtime_per_meter_sec"]:
        if col in df.columns:
            df.loc[invalid_runtime, col] = np.nan

for col in ["peak_memory_mb", "avg_memory_mb"]:
    if col in df.columns:
        df.loc[df[col] <= 0, col] = np.nan

sequence_order = [
    "euroc_mh01",
    "euroc_mh02",
    "euroc_mh03",
    "euroc_mh04",
    "euroc_mh05",
] + [f"kitti_{i:02d}" for i in range(10)]

order_map = {seq: i for i, seq in enumerate(sequence_order)}

df["sequence_sort"] = df["sequence"].astype(str).map(order_map).fillna(999)
df = df.sort_values(["sequence_sort", "method"], na_position="last")
df = df.drop(columns=["sequence_sort"])

out = Path("results/comparison_summary.csv")
df.to_csv(out, index=False)

print(df)
print(f"\nSaved: {out}")