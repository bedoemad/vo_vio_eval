from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT = Path("results/error_visual_correlation/euroc_mh01_orbslam3.csv")
OUT_DIR = Path("results/error_visual_correlation/plots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

for metric in ["blur_score", "texture_score", "brightness_mean", "brightness_std"]:
    plt.figure()
    plt.scatter(df[metric], df["position_error_m"], s=5)
    plt.xlabel(metric)
    plt.ylabel("Position Error (m)")
    plt.title(f"Position Error vs {metric}")
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"error_vs_{metric}.png", dpi=200)
    plt.close()

plt.figure()
plt.plot(df["timestamp"], df["position_error_m"])
plt.xlabel("Timestamp")
plt.ylabel("Position Error (m)")
plt.title("ORB-SLAM3 Position Error Over Time")
plt.tight_layout()
plt.savefig(OUT_DIR / "position_error_over_time.png", dpi=200)
plt.close()

print(f"Saved plots to {OUT_DIR}")
