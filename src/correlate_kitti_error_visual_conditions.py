from pathlib import Path

import numpy as np
import pandas as pd


GT_PATH = Path("data/kitti/poses/00_tum.txt")
PRED_PATH = Path("results/orbslam3_kitti_mono/kitti_00/predicted_trajectory.txt")
VISUAL_PATH = Path("results/visual_conditions/kitti_00_cam0.csv")
OUT_PATH = Path("results/error_visual_correlation/kitti_00_orbslam3_kitti_mono.csv")


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

    t = mu_target - scale * R @ mu_source
    aligned = (scale * (R @ source.T)).T + t

    return aligned, scale


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    gt = load_tum(GT_PATH)
    pred = load_tum(PRED_PATH)
    visual = pd.read_csv(VISUAL_PATH)

    merged = nearest_merge(pred, gt, tolerance=0.05)
    merged = merged.dropna()

    if len(merged) < 10:
        raise RuntimeError(f"Too few matched poses: {len(merged)}")

    pred_xyz = merged[["tx_x", "ty_x", "tz_x"]].to_numpy()
    gt_xyz = merged[["tx_y", "ty_y", "tz_y"]].to_numpy()

    aligned_pred_xyz, scale = umeyama_alignment(pred_xyz, gt_xyz, with_scale=True)

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
        tolerance=0.05,
    )

    merged_visual = merged_visual.dropna()
    merged_visual["sequence"] = "kitti_00"
    merged_visual["method"] = "orbslam3_kitti_mono"
    merged_visual["alignment_scale"] = scale

    merged_visual.to_csv(OUT_PATH, index=False)

    print("Matched samples:", len(merged_visual))
    print("Alignment scale:", scale)

    print(
        merged_visual[
            [
                "aligned_position_error_m",
                "blur_score",
                "texture_score",
                "fast_texture_score",
                "brightness_mean",
                "brightness_std",
            ]
        ].corr()
    )

    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
