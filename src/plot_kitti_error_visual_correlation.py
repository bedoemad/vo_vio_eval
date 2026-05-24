from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/error_visual_correlation/kitti_00_orbslam3_kitti_mono.csv")
OUT_DIR = Path("results/error_visual_correlation/kitti_00_plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

for metric in ["blur_score", "texture_score", "brightness_mean", "brightness_std"]:
    plt.figure()
    plt.scatter(df[metric], df["aligned_position_error_m"], s=5)
    plt.xlabel(metric)
    plt.ylabel("Aligned Position Error (m)")
    plt.title(f"KITTI 00: Error vs {metric}")
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"kitti_00_error_vs_{metric}.png", dpi=200)
    plt.close()

plt.figure()
plt.plot(df["timestamp"], df["aligned_position_error_m"])
plt.xlabel("Timestamp")
plt.ylabel("Aligned Position Error (m)")
plt.title("KITTI 00: ORB-SLAM3 Error Over Time")
plt.tight_layout()
plt.savefig(OUT_DIR / "kitti_00_error_over_time.png", dpi=200)
plt.close()

print(f"Saved plots to {OUT_DIR}")
