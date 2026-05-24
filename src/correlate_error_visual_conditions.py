from pathlib import Path
import pandas as pd
import numpy as np


GT_PATH = Path("data/euroc/MH_01_easy/mav0/state_groundtruth_estimate0/data_tum.txt")
PRED_PATH = Path("results/orbslam3_mono/euroc_mh01/predicted_trajectory.txt")
VISUAL_PATH = Path("results/visual_conditions/euroc_mh01_cam0.csv")
OUT_PATH = Path("results/error_visual_correlation/euroc_mh01_orbslam3.csv")


def load_tum(path: Path):
    df = pd.read_csv(
        path,
        sep=r"\s+",
        header=None,
        names=["timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw"],
    )
    return df


def nearest_merge(left, right, tolerance=0.02):
    return pd.merge_asof(
        left.sort_values("timestamp"),
        right.sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
        tolerance=tolerance,
    )


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    gt = load_tum(GT_PATH)
    pred = load_tum(PRED_PATH)
    visual = pd.read_csv(VISUAL_PATH)

    merged = nearest_merge(pred, gt, tolerance=0.02)
    merged = merged.dropna()

    merged["position_error_m"] = np.sqrt(
        (merged["tx_x"] - merged["tx_y"]) ** 2 +
        (merged["ty_x"] - merged["ty_y"]) ** 2 +
        (merged["tz_x"] - merged["tz_y"]) ** 2
    )

    merged = merged.rename(columns={
        "tx_x": "pred_tx",
        "ty_x": "pred_ty",
        "tz_x": "pred_tz",
        "tx_y": "gt_tx",
        "ty_y": "gt_ty",
        "tz_y": "gt_tz",
    })

    merged_visual = nearest_merge(
        merged[["timestamp", "position_error_m"]],
        visual,
        tolerance=0.02,
    )

    merged_visual = merged_visual.dropna()
    merged_visual.to_csv(OUT_PATH, index=False)

    print(merged_visual[[
        "position_error_m",
        "blur_score",
        "texture_score",
        "brightness_mean",
        "brightness_std",
    ]].corr())

    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
