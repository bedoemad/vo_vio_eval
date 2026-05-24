import argparse
import json
from pathlib import Path
from config_utils import load_sequences, resolve_sequence_paths
import numpy as np
import pandas as pd



CONFIG_PATH = Path("configs/sequences.json")

VISUAL_DIR = Path("results/visual_conditions")
MOTION_DIR = Path("results/motion_conditions")

OUT_DIR = Path("results/generic_failure_diagnostics")
OUT_DIR.mkdir(parents=True, exist_ok=True)

COMBINED_ERROR_OUT = OUT_DIR / "all_methods_error_conditions.csv"
BINNED_OUT = OUT_DIR / "all_methods_binned_conditions.csv"
EFFECT_OUT = Path("results/final_tables/all_methods_condition_effect_summary.csv")
EFFECT_OUT.parent.mkdir(parents=True, exist_ok=True)

SKIP_METHODS = {
    "dummy_vo",
    "noisy_dummy_vo",
    "example_adapter",
}

APPEARANCE_METRICS = [
    "blur_score",
    "texture_score",
    "fast_texture_score",
    "brightness_mean",
    "brightness_std",
]

MOTION_METRICS = [
    "frame_translation_m",
    "translation_speed_mps",
    "frame_rotation_deg",
    "rotation_speed_degps",
]


def load_tum(path: Path):
    return pd.read_csv(
        path,
        sep=r"\s+",
        header=None,
        names=["timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw"],
    )


def nearest_merge(left, right, tolerance=0.05):
    return pd.merge_asof(
        left.sort_values("timestamp"),
        right.sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
        tolerance=tolerance,
        suffixes=("", "_right"),
    )


def umeyama_alignment(source, target, with_scale=True):
    source = np.asarray(source)
    target = np.asarray(target)

    mu_source = source.mean(axis=0)
    mu_target = target.mean(axis=0)

    src_centered = source - mu_source
    tgt_centered = target - mu_target

    covariance = tgt_centered.T @ src_centered / source.shape[0]

    U, D, Vt = np.linalg.svd(covariance)

    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[-1, -1] = -1

    R = U @ S @ Vt

    if with_scale:
        var_source = np.mean(np.sum(src_centered ** 2, axis=1))
        scale = np.trace(np.diag(D) @ S) / var_source
    else:
        scale = 1.0

    t = mu_target - scale * R @ source.mean(axis=0)
    # Correct translation after centering:
    t = mu_target - scale * R @ mu_source

    aligned = (scale * (R @ source.T)).T + t
    return aligned, scale


def make_quantile_bins(series, q=4):
    binned = pd.qcut(series, q=q, labels=False, duplicates="drop")
    unique_bins = sorted(binned.dropna().unique())

    if len(unique_bins) == 1:
        label_map = {unique_bins[0]: "all"}
    elif len(unique_bins) == 2:
        label_map = {
            unique_bins[0]: "low",
            unique_bins[1]: "high",
        }
    elif len(unique_bins) == 3:
        label_map = {
            unique_bins[0]: "low",
            unique_bins[1]: "medium",
            unique_bins[2]: "high",
        }
    else:
        label_map = {
            unique_bins[0]: "low",
            unique_bins[1]: "medium_low",
            unique_bins[2]: "medium_high",
            unique_bins[3]: "high",
        }

    return binned.map(label_map)


def load_sequence_config():
    sequences = [resolve_sequence_paths(seq) for seq in load_sequences()]
    return {seq["name"]: seq for seq in sequences}


def iter_successful_runs():
    for run_path in sorted(Path("results").glob("*/*/run_result.json")):
        with open(run_path) as f:
            run = json.load(f)

        method = run.get("method")
        sequence = run.get("sequence")

        if method in SKIP_METHODS:
            continue

        if not run.get("success", False):
            continue

        pred = run.get("predicted_trajectory")
        if not pred:
            continue

        pred_path = Path(pred)
        if not pred_path.exists():
            continue

        yield run


def process_run(run, sequence_map):
    method = run["method"]
    sequence = run["sequence"]

    if sequence not in sequence_map:
        print(f"[SKIP] No sequence config for {sequence}")
        return None

    seq_cfg = sequence_map[sequence]
    dataset = seq_cfg.get("dataset", "unknown")

    gt_path = Path(seq_cfg["groundtruth"])
    pred_path = Path(run["predicted_trajectory"])

    visual_path = VISUAL_DIR / f"{sequence}_cam0.csv"
    motion_path = MOTION_DIR / f"{sequence}_motion.csv"

    if not gt_path.exists():
        print(f"[SKIP] Missing GT for {method}/{sequence}: {gt_path}")
        return None

    if not visual_path.exists():
        print(f"[SKIP] Missing visual file for {method}/{sequence}: {visual_path}")
        return None

    if not motion_path.exists():
        print(f"[SKIP] Missing motion file for {method}/{sequence}: {motion_path}")
        return None

    gt = load_tum(gt_path)
    pred = load_tum(pred_path)
    visual = pd.read_csv(visual_path)
    motion = pd.read_csv(motion_path)

    merged = nearest_merge(pred, gt, tolerance=timestamp_tolerance)
    merged = merged.dropna()

    if len(merged) < 10:
        print(f"[SKIP] Too few matched poses for {method}/{sequence}: {len(merged)}")
        return None

    pred_xyz = merged[["tx", "ty", "tz"]].to_numpy()
    gt_xyz = merged[["tx_right", "ty_right", "tz_right"]].to_numpy()

    aligned_pred_xyz, scale = umeyama_alignment(pred_xyz, gt_xyz, with_scale=True)

    merged["aligned_position_error_m"] = np.sqrt(
        (aligned_pred_xyz[:, 0] - gt_xyz[:, 0]) ** 2
        + (aligned_pred_xyz[:, 1] - gt_xyz[:, 1]) ** 2
        + (aligned_pred_xyz[:, 2] - gt_xyz[:, 2]) ** 2
    )

    base = merged[["timestamp", "aligned_position_error_m"]].copy()

    visual = visual.drop(columns=["sequence", "method"], errors="ignore")
    motion = motion.drop(columns=["sequence", "method"], errors="ignore")

    merged_visual = nearest_merge(base, visual, tolerance=timestamp_tolerance)
    merged_all = nearest_merge(merged_visual, motion, tolerance=timestamp_tolerance)

    merged_all = merged_all.dropna(subset=["aligned_position_error_m"])

    merged_all["method"] = method
    merged_all["sequence"] = sequence
    merged_all["dataset"] = dataset
    merged_all["alignment_scale"] = scale

    print(f"{method}/{sequence}: {len(merged_all)} diagnostic samples")

    return merged_all


def create_binned_table(combined):
    rows = []

    for (dataset, method, sequence), seq_df in combined.groupby(
        ["dataset", "method", "sequence"]
    ):
        available_appearance = [
            m for m in APPEARANCE_METRICS if m in seq_df.columns
        ]
        available_motion = [
            m for m in MOTION_METRICS if m in seq_df.columns
        ]

        metric_groups = []
        metric_groups += [("appearance", m) for m in available_appearance]
        metric_groups += [("motion", m) for m in available_motion]

        for condition_group, metric in metric_groups:
            temp = seq_df.dropna(
                subset=[metric, "aligned_position_error_m"]
            ).copy()

            if temp.empty or temp[metric].nunique() < 2:
                continue

            temp["bin"] = make_quantile_bins(temp[metric])

            grouped = (
                temp.groupby("bin", observed=True)
                .agg(
                    samples=("aligned_position_error_m", "count"),
                    metric_min=(metric, "min"),
                    metric_max=(metric, "max"),
                    error_mean_m=("aligned_position_error_m", "mean"),
                    error_median_m=("aligned_position_error_m", "median"),
                    error_std_m=("aligned_position_error_m", "std"),
                    error_max_m=("aligned_position_error_m", "max"),
                )
                .reset_index()
            )

            grouped["dataset"] = dataset
            grouped["method"] = method
            grouped["sequence"] = sequence
            grouped["condition_group"] = condition_group
            grouped["condition_metric"] = metric

            rows.append(grouped)

    if not rows:
        raise RuntimeError("No binned diagnostic rows were created.")

    result = pd.concat(rows, ignore_index=True)

    bin_order = {
        "all": 0,
        "low": 1,
        "medium": 2,
        "medium_low": 2,
        "medium_high": 3,
        "high": 4,
    }

    result["bin_order"] = result["bin"].map(bin_order)

    result = result.sort_values(
        [
            "dataset",
            "method",
            "sequence",
            "condition_group",
            "condition_metric",
            "bin_order",
        ]
    )

    return result


def create_effect_table(binned):
    rows = []

    for (
        dataset,
        method,
        sequence,
        condition_group,
        metric,
    ), group in binned.groupby(
        ["dataset", "method", "sequence", "condition_group", "condition_metric"],
        dropna=False,
    ):
        low = group[group["bin"] == "low"]
        high = group[group["bin"] == "high"]

        if low.empty or high.empty:
            continue

        low_error = float(low["error_mean_m"].iloc[0])
        high_error = float(high["error_mean_m"].iloc[0])

        if condition_group == "motion":
            hard_condition = "high"
            easy_condition = "low"
            hard_error = high_error
            easy_error = low_error
            hard_samples = int(high["samples"].iloc[0])
            easy_samples = int(low["samples"].iloc[0])
        else:
            hard_condition = "low"
            easy_condition = "high"
            hard_error = low_error
            easy_error = high_error
            hard_samples = int(low["samples"].iloc[0])
            easy_samples = int(high["samples"].iloc[0])

        rows.append(
            {
                "dataset": dataset,
                "method": method,
                "sequence": sequence,
                "condition_group": condition_group,
                "condition_metric": metric,
                "hard_condition": hard_condition,
                "easy_condition": easy_condition,
                "hard_condition_mean_error_m": hard_error,
                "easy_condition_mean_error_m": easy_error,
                "hard_minus_easy_error_m": hard_error - easy_error,
                "hard_over_easy_error_ratio": (
                    hard_error / easy_error if easy_error != 0 else None
                ),
                "hard_condition_samples": hard_samples,
                "easy_condition_samples": easy_samples,
            }
        )

    effect = pd.DataFrame(rows)

    if effect.empty:
        raise RuntimeError("No diagnostic effect rows were created.")

    effect["abs_effect_m"] = effect["hard_minus_easy_error_m"].abs()

    effect = effect.sort_values(
        ["dataset", "method", "abs_effect_m"],
        ascending=[True, True, False],
    )

    return effect

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run generic condition-dependent VO/VIO failure diagnostics."
    )

    parser.add_argument(
        "--timestamp-tolerance",
        type=float,
        default=0.05,
        help=(
            "Nearest-neighbor timestamp matching tolerance in seconds. "
            "Default: 0.05 seconds."
        ),
    )

    return parser.parse_args()

def main():
    args = parse_args()
    sequence_map = load_sequence_config()

    print(
        f"Using timestamp matching tolerance: "
        f"{args.timestamp_tolerance:.3f} seconds"
    )

    all_rows = []

    for run in iter_successful_runs():
        result = process_run(
            run,
            sequence_map,
            timestamp_tolerance=args.timestamp_tolerance,
        )
        if result is not None:
            all_rows.append(result)

    if not all_rows:
        raise RuntimeError("No successful method runs could be processed.")

    combined = pd.concat(all_rows, ignore_index=True)
    combined.to_csv(COMBINED_ERROR_OUT, index=False)

    binned = create_binned_table(combined)
    binned.to_csv(BINNED_OUT, index=False)

    effect = create_effect_table(binned)
    effect.to_csv(EFFECT_OUT, index=False)

    print(f"\nSaved combined diagnostics: {COMBINED_ERROR_OUT}")
    print(f"Saved binned diagnostics:   {BINNED_OUT}")
    print(f"Saved effect summary:       {EFFECT_OUT}")


if __name__ == "__main__":
    main()
