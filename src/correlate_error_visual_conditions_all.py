import json
from pathlib import Path

import numpy as np
import pandas as pd


METHOD = "orbslam3_mono"
CONFIG_PATH = Path("configs/sequences.json")
OUT_DIR = Path("results/error_visual_correlation")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_tum(path: Path):
    return pd.read_csv(
        path,
        sep=r"\s+",
        header=None,
        names=["timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw"],
    )


def nearest_merge(left, right, tolerance=0.02):
    return pd.merge_asof(
        left.sort_values("timestamp"),
        right.sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
        tolerance=tolerance,
    )


def umeyama_alignment(source, target, with_scale=True):
    """
    Align source points to target points using Sim(3) Umeyama alignment.
    source: predicted positions, shape Nx3
    target: ground-truth positions, shape Nx3
    """
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

    t = mu_target - scale * R @ mu_source

    aligned = (scale * (R @ source.T)).T + t
    return aligned, scale, R, t


def process_sequence(sequence):
    name = sequence["name"]
    gt_path = Path(sequence["groundtruth"])
    pred_path = Path("results") / METHOD / name / "predicted_trajectory.txt"
    visual_path = Path("results/visual_conditions") / f"{name}_cam0.csv"

    if not gt_path.exists():
        print(f"[SKIP] Missing GT: {gt_path}")
        return None

    if not pred_path.exists():
        print(f"[SKIP] Missing prediction: {pred_path}")
        return None

    if not visual_path.exists():
        print(f"[SKIP] Missing visual conditions: {visual_path}")
        return None

    gt = load_tum(gt_path)
    pred = load_tum(pred_path)
    visual = pd.read_csv(visual_path)

    merged = nearest_merge(pred, gt, tolerance=0.02)
    merged = merged.dropna()

    if len(merged) < 10:
        print(f"[SKIP] Too few matched poses for {name}: {len(merged)}")
        return None

    pred_xyz = merged[["tx_x", "ty_x", "tz_x"]].to_numpy()
    gt_xyz = merged[["tx_y", "ty_y", "tz_y"]].to_numpy()

    aligned_pred_xyz, scale, R, t = umeyama_alignment(pred_xyz, gt_xyz, with_scale=True)

    merged["aligned_pred_tx"] = aligned_pred_xyz[:, 0]
    merged["aligned_pred_ty"] = aligned_pred_xyz[:, 1]
    merged["aligned_pred_tz"] = aligned_pred_xyz[:, 2]

    merged["gt_tx"] = gt_xyz[:, 0]
    merged["gt_ty"] = gt_xyz[:, 1]
    merged["gt_tz"] = gt_xyz[:, 2]

    merged["aligned_position_error_m"] = np.sqrt(
        (merged["aligned_pred_tx"] - merged["gt_tx"]) ** 2 +
        (merged["aligned_pred_ty"] - merged["gt_ty"]) ** 2 +
        (merged["aligned_pred_tz"] - merged["gt_tz"]) ** 2
    )

    merged_visual = nearest_merge(
        merged[["timestamp", "aligned_position_error_m"]],
        visual,
        tolerance=0.02,
    )

    merged_visual = merged_visual.dropna()
    merged_visual["sequence"] = name
    merged_visual["method"] = METHOD
    merged_visual["alignment_scale"] = scale

    out_path = OUT_DIR / f"{name}_{METHOD}.csv"
    merged_visual.to_csv(out_path, index=False)

    corr = merged_visual[
        [
            "aligned_position_error_m",
            "blur_score",
            "texture_score",
            "brightness_mean",
            "brightness_std",
        ]
    ].corr()

    print(f"\n=== {name} ===")
    print(f"Matched frames: {len(merged_visual)}")
    print(f"Alignment scale: {scale:.6f}")
    print(corr["aligned_position_error_m"].sort_values())

    return merged_visual


def main():
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    all_rows = []

    for sequence in config["sequences"]:
        if sequence["name"].startswith("euroc_mh"):
            result = process_sequence(sequence)
            if result is not None:
                all_rows.append(result)

    if all_rows:
        combined = pd.concat(all_rows, ignore_index=True)
        combined_out = OUT_DIR / f"all_sequences_{METHOD}.csv"
        combined.to_csv(combined_out, index=False)
        print(f"\nSaved combined file: {combined_out}")
    else:
        print("No valid sequences processed.")


if __name__ == "__main__":
    main()
