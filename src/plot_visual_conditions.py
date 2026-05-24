from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


INPUT_DIR = Path("results/visual_conditions")
OUTPUT_DIR = Path("results/visual_condition_plots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

csv_files = sorted(INPUT_DIR.glob("*.csv"))

summary_rows = []

for csv_path in csv_files:
    df = pd.read_csv(csv_path)
    sequence = csv_path.stem.replace("_cam0", "")

    summary_rows.append({
        "sequence": sequence,
        "frames": len(df),
        "blur_mean": df["blur_score"].mean(),
        "blur_median": df["blur_score"].median(),
        "texture_mean": df["texture_score"].mean(),
        "texture_median": df["texture_score"].median(),
        "brightness_mean": df["brightness_mean"].mean(),
        "brightness_std_mean": df["brightness_std"].mean(),
    })

    for metric in ["blur_score", "texture_score", "brightness_mean", "brightness_std"]:
        plt.figure()
        plt.plot(df["timestamp"], df[metric])
        plt.xlabel("Timestamp")
        plt.ylabel(metric)
        plt.title(f"{sequence} - {metric}")
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"{sequence}_{metric}.png", dpi=200)
        plt.close()

summary = pd.DataFrame(summary_rows)
summary.to_csv("results/visual_conditions_summary.csv", index=False)

print(summary)
print("Saved plots to:", OUTPUT_DIR)
print("Saved summary to: results/visual_conditions_summary.csv")
